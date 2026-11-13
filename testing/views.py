
import json

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Device,
    DeviceModel,
    ModelPhase,
    Phase,
    TestDefinition,
    TestPlanItem,
    TestResult,
    TestRun,
    TestSession,
)

@login_required
def device_list(request):
    search = request.GET.get("search", "").strip()

    devices = (
        Device.objects
        .select_related("model")
        .order_by("-created_at")
    )

    if search:
        devices = devices.filter(
            serial_number__icontains=search
        )

    context = {
        "devices": devices,
        "search": search,
        "total_devices": devices.count(),
        "device_models": DeviceModel.objects.filter(
            is_active=True
        ).order_by("name"),
    }

    return render(request, "testing/device_list.html", context)

@login_required
@require_POST
def add_device(request):
    serial_number = request.POST.get(
        "serial_number", ""
    ).strip()

    model_id = request.POST.get("model_id")

    if not serial_number:
        messages.error(request, "Укажи серийный номер.")
        return redirect("device_list")

    if len(serial_number) > 100:
        messages.error(request, "Серийный номер слишком длинный.")
        return redirect("device_list")

    model = DeviceModel.objects.filter(
        pk=model_id,
        is_active=True
    ).first()

    if model is None:
        messages.error(request, "Выбери существующую модель.")
        return redirect("device_list")

    try:
        Device.objects.create(
            serial_number=serial_number,
            model=model,
            status=Device.Status.PENDING
        )
    except IntegrityError:
        messages.error(
            request,
            "Устройство с таким серийным номером уже существует."
        )
        return redirect("device_list")

    messages.success(
        request,
        f"Устройство {serial_number} добавлено.",
        extra_tags="device"
    )

    return redirect("device_list")

@login_required
def test_session(request):
    devices = Device.objects.order_by("serial_number")

    selected_serial = request.GET.get("serial_number")

    if selected_serial:
        device = devices.filter(
            serial_number=selected_serial
        ).first()
    else:
        device = devices.first()

    session = None
    test_runs = TestRun.objects.none()

    if device is not None:
        session = (
            TestSession.objects
            .filter(device=device)
            .select_related("device__model")
            .order_by("-started_at")
            .first()
        )

    if session is not None:
        test_runs = (
            TestRun.objects.filter(session=session)
            .select_related("test")
            .prefetch_related(
                "results",
                "test__parameters"
            )
        )

    total_tests = test_runs.count()

    completed_tests = test_runs.filter(
        status__in=["passed", "failed", "skipped"]
    ).count()

    progress = (
        round(completed_tests / total_tests * 100, 2)
        if total_tests > 0
        else 0
    )

    context = {
        "devices": devices,
        "device": device,
        "session": session,
        "test_runs": test_runs,
        "total_tests": total_tests,
        "completed_tests": completed_tests,
        "progress": progress,
    }

    return render(request, "testing/test_session.html", context)


@login_required
@require_POST
def start_testing(request):
    serial = request.POST.get("serial_number")

    with transaction.atomic():

        device = get_object_or_404(
            Device.objects.select_for_update(),
            serial_number=serial,
        )

        if TestSession.objects.filter(
            device=device,
            status=TestSession.Status.RUNNING,
        ).exists():
            messages.error(request, "У этого устройства уже есть активная сессия.")
            return redirect(f"/testing/?serial_number={device.serial_number}")

        plan_items = (
            TestPlanItem.objects
            .filter(model_phase__device_model=device.model)
            .order_by("model_phase__order", "order", "pk")
            .values_list("test_id", flat=True)
        )

        test_ids = list(dict.fromkeys(plan_items))

        if not test_ids:
            messages.error(request, "Для модели не настроен план тестирования.")
            return redirect(f"/testing/?serial_number={device.serial_number}")

        session = TestSession.objects.create(
            device=device,
            status=TestSession.Status.RUNNING,
        )
        TestRun.objects.bulk_create([
            TestRun(
                session=session,
                test_id=test_id,
                status=TestRun.Status.PENDING,
            )
            for test_id in test_ids
        ])
        device.status = Device.Status.TESTING
        device.save(update_fields=["status"])

    return redirect(f"/testing/?serial_number={device.serial_number}")


@login_required
def plan_settings(request):

    models = DeviceModel.objects.order_by("name")

    selected_model_id = request.GET.get("model_id")

    available_tests = TestDefinition.objects.filter(
    is_active=True
).order_by("name")

    available_phases = Phase.objects.filter(
        is_active=True
    ).order_by("name")

    if selected_model_id:
        selected_model = models.filter(
            pk=selected_model_id
        ).first()
    else:
        selected_model = models.first()

    phases = ModelPhase.objects.none()

    if selected_model:
        phases = (
            ModelPhase.objects
            .filter(device_model=selected_model)
            .select_related("phase")
            .prefetch_related(
                Prefetch(
                    "tests",
                    queryset=TestPlanItem.objects
                        .select_related("test")
                        .order_by("order")
                )
            )
            .order_by("order")
        )

    context = {
        "models": models,
        "selected_model": selected_model,
        "phases": phases,
        "available_tests": available_tests,
        "available_phases": available_phases,
    }

    return render(request, "testing/plan_settings.html", context)


@login_required
@require_POST
def add_plan_test(request):
    model_phase = get_object_or_404(
        ModelPhase,
        pk=request.POST.get("model_phase_id")
    )

    test = get_object_or_404(
        TestDefinition,
        pk=request.POST.get("test_id"),
        is_active=True
    )

    exists = TestPlanItem.objects.filter(
        model_phase=model_phase,
        test=test
    ).exists()

    if not exists:
        max_order = TestPlanItem.objects.filter(
            model_phase=model_phase
        ).aggregate(Max("order"))["order__max"]

        TestPlanItem.objects.create(
            model_phase=model_phase,
            test=test,
            order=(max_order or 0) + 1
        )

    return redirect(
        f"/testing/plan/?model_id={model_phase.device_model_id}"
    )
@login_required
@require_POST
def add_plan_phase(request):
    device_model = get_object_or_404(
        DeviceModel,
        pk=request.POST.get("model_id")
    )

    phase = get_object_or_404(
        Phase,
        pk=request.POST.get("phase_id"),
        is_active=True
    )

    exists = ModelPhase.objects.filter(
        device_model=device_model,
        phase=phase
    ).exists()

    if not exists:
        max_order = ModelPhase.objects.filter(
            device_model=device_model
        ).aggregate(Max("order"))["order__max"]

        ModelPhase.objects.create(
            device_model=device_model,
            phase=phase,
            order=(max_order or 0) + 1
        )

    return redirect(
        f"/testing/plan/?model_id={device_model.pk}"
    
  )


@login_required
@require_POST
def delete_plan_phase(request):
    model_phase = get_object_or_404(
        ModelPhase,
        pk=request.POST.get("model_phase_id")
    )

    model_id = model_phase.device_model_id

    if model_phase.tests.exists():
        messages.error(
            request,
            "Сначала удалите все тесты из этой фазы."
        )
        return redirect(
            f"/testing/plan/?model_id={model_id}"
        )

    model_phase.delete()

    return redirect(
        f"/testing/plan/?model_id={model_id}"
    )


@login_required
@require_POST
def delete_plan_test(request):
    plan_item = get_object_or_404(
        TestPlanItem,
        pk=request.POST.get("plan_item_id")
    )

    model_id = plan_item.model_phase.device_model_id

    plan_item.delete()

    return redirect(
        f"/testing/plan/?model_id={model_id}"
    )

@login_required
@require_POST
def reorder_phases(request):
    try:
        data = json.loads(request.body)
        phase_ids = data["phase_ids"]

        if not isinstance(phase_ids, list):
            return JsonResponse({"error": "Неверный формат"}, status=400)

        ids = [int(pk) for pk in phase_ids]

        if len(ids) != len(set(ids)):
            return JsonResponse({"error": "Повторяющиеся ID"}, status=400)

        with transaction.atomic():
            phases = list(
                ModelPhase.objects.select_for_update()
                .filter(pk__in=ids)
            )

            if len(phases) != len(ids):
                return JsonResponse({"error": "Фазы не найдены"}, status=400)

            if phases and len({p.device_model_id for p in phases}) != 1:
                return JsonResponse({"error": "Разные модели"}, status=400)

            if phases:
                model_id = phases[0].device_model_id
                all_ids = set(
                    ModelPhase.objects.filter(
                        device_model_id=model_id
                    ).values_list("pk", flat=True)
                )

                if all_ids != set(ids):
                    return JsonResponse({"error": "Неполный список фаз"}, status=400)
            max_order = (
                ModelPhase.objects.aggregate(Max("order"))["order__max"] or 0
            )

            for index, phase in enumerate(phases, start=1):
                phase.order = max_order + index
                phase.save(update_fields=["order"])

            phase_map = {phase.pk: phase for phase in phases}

            for index, pk in enumerate(ids, start=1):
                phase = phase_map[pk]
                phase.order = index
                phase.save(update_fields=["order"])

        return JsonResponse({"success": True})

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Неверные данные"}, status=400)

@login_required
@require_POST
def reorder_tests(request):
    try:
        data = json.loads(request.body)
        model_phase_id = int(data["model_phase_id"])
        test_ids = [int(pk) for pk in data["test_ids"]]

        if len(test_ids) != len(set(test_ids)):
            return JsonResponse({"error": "Повторяющиеся ID"}, status=400)

        with transaction.atomic():
            model_phase = get_object_or_404(
                ModelPhase,
                pk=model_phase_id
            )

            items = list(
                TestPlanItem.objects.select_for_update()
                .filter(model_phase=model_phase)
            )

            if set(item.pk for item in items) != set(test_ids):
                return JsonResponse(
                    {"error": "Неверный список тестов"},
                    status=400
                )

            max_order = (
                TestPlanItem.objects.aggregate(Max("order"))["order__max"] or 0
            )

            for index, item in enumerate(items, start=1):
                item.order = max_order + index
                item.save(update_fields=["order"])

            item_map = {item.pk: item for item in items}

            for index, pk in enumerate(test_ids, start=1):
                item = item_map[pk]
                item.order = index
                item.save(update_fields=["order"])

        return JsonResponse({"success": True})

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Неверные данные"}, status=400)
@login_required
@require_POST
def update_test_status(request):
    test_run_id = request.POST.get("test_run_id")

    status = request.POST.get("status")

    allowed_statuses = [
        TestRun.Status.PASSED,
        TestRun.Status.FAILED,
    ]

    if status not in allowed_statuses:
        messages.error(request, "Недопустимый статус теста.")
        return redirect("test_session")

    comment = request.POST.get("comment", "").strip()

    with transaction.atomic():

        test_run = get_object_or_404(
            TestRun.objects.select_related("session__device"),
            pk=test_run_id,
        )
        session = TestSession.objects.select_for_update().get(
            pk=test_run.session_id
        )
        test_run.refresh_from_db()

        if session.status != TestSession.Status.RUNNING:
            messages.error(
                request,
                "Сессия тестирования уже завершена."
            )
            return redirect("test_session")

        test_run.status = status
        test_run.finished_at = timezone.now()
        test_run.save(update_fields=["status", "finished_at"])

        if comment:
            TestResult.objects.update_or_create(
                test_run=test_run,
                name="COMMENT",
                defaults={
                    "value": comment,
                    "unit": "",
                }
            )
        else:
            TestResult.objects.filter(
                test_run=test_run,
                name="COMMENT"
            ).delete()

        statuses = list(
            TestRun.objects.filter(
                session=session
            ).values_list("status", flat=True)
        )

        finished_statuses = {
            TestRun.Status.PASSED,
            TestRun.Status.FAILED,
            TestRun.Status.SKIPPED,
        }

        all_tests_finished = (
            bool(statuses)
            and all(s in finished_statuses for s in statuses)
        )

        if all_tests_finished:
            has_failed_tests = (
                TestRun.Status.FAILED in statuses
            )

            session.status = (
                TestSession.Status.FAILED
                if has_failed_tests
                else TestSession.Status.PASSED
            )

            session.finished_at = timezone.now()
            session.save(
                update_fields=["status", "finished_at"]
            )

            device = session.device

            device.status = (
                Device.Status.FAILED
                if has_failed_tests
                else Device.Status.PASSED
            )

            device.save(update_fields=["status"])

        else:
            device = session.device

            if device.status != Device.Status.TESTING:
                device.status = Device.Status.TESTING
                device.save(update_fields=["status"])

    messages.success(
        request,
        "Результат теста сохранён."
    )

    return redirect(
        f"/testing/?serial_number={test_run.session.device.serial_number}"
    )

@login_required
def history(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    sessions = (
        TestSession.objects
        .select_related("device", "device__model")
        .annotate(
            total_tests=Count("test_runs", distinct=True),
            passed_tests=Count(
                "test_runs",
                filter=Q(test_runs__status="passed"),
                distinct=True
            )
        )
        .order_by("-started_at", "-pk")
    )

    if search:
        sessions = sessions.filter(
            Q(device__serial_number__icontains=search) |
            Q(device__model__name__icontains=search)
        )

    if status in ["running", "passed", "failed", "cancelled"]:
        sessions = sessions.filter(status=status)

    context = {
        "sessions": sessions,
        "search": search,
        "selected_status": status,
        "total_sessions": sessions.count(),
        "passed_sessions": sessions.filter(status="passed").count(),
        "failed_sessions": sessions.filter(status="failed").count(),
    }

    return render(request, "testing/history.html", context)
@login_required
def history_detail(request, session_id):
    session = get_object_or_404(
        TestSession.objects.select_related(
            "device",
            "device__model"
        ),
        pk=session_id
    )

    test_runs = (
        TestRun.objects
        .filter(session=session)
        .select_related("test")
        .prefetch_related("results")
        .order_by("pk")
    )

    context = {
        "session": session,
        "test_runs": test_runs,
    }

    return render(request, "testing/history_detail.html", context)

@login_required
def models_page(request):
    search = request.GET.get("search", "").strip()

    models = DeviceModel.objects.all().order_by("name")

    if search:
        models = models.filter(
            Q(name__icontains=search) |
            Q(manufacturer__icontains=search)
        )

    context = {
        "device_models": models,
        "total_models": models.count(),
        "search": search,
    }

    return render(request, "testing/models.html", context)

@login_required
@require_POST
def add_device_model(request):
    name = request.POST.get("name", "").strip()
    manufacturer = request.POST.get("manufacturer", "").strip()
    device_type = request.POST.get("device_type", "").strip()
    description = request.POST.get("description", "").strip()

    if not name or not manufacturer or not device_type:
        messages.error(
            request,
            "Заполни название, производителя и тип.",
            extra_tags="model"
        )
        return redirect("models_page")

    if (
        len(name) > 100 or
        len(manufacturer) > 100 or
        len(device_type) > 50
    ):
        messages.error(
            request,
            "Одно из полей превышает допустимую длину.",
            extra_tags="model"
        )
        return redirect("models_page")

    if DeviceModel.objects.filter(
        name__iexact=name,
        manufacturer__iexact=manufacturer
    ).exists():
        messages.error(
            request,
            "Такая модель уже существует.",
            extra_tags="model"
        )
        return redirect("models_page")

    DeviceModel.objects.create(
        name=name,
        manufacturer=manufacturer,
        device_type=device_type,
        description=description,
        is_active=True
    )

    messages.success(
        request,
        f"Модель {name} добавлена.",
        extra_tags="model"
    )

    return redirect("models_page")

@login_required
def settings_page(request):
    return redirect("plan_settings")