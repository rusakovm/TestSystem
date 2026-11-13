from django.db import transaction
from django.utils import timezone
from .models import (
    Device,
    TestSession,
    TestRun,
    TestPlanItem,
    TestResult,
)


@transaction.atomic
def finish_test_run(run_id,passed):
    run = TestRun.objects.select_for_update().get(id = run_id)
    if run.status not in [
        TestRun.Status.PENDING,
        TestRun.Status.RUNNING
    ]:
        raise ValueError("Тест уже завершён")

    if passed:
        run.status = TestRun.Status.PASSED
    else:
        run.status = TestRun.Status.FAILED
    
    run.finished_at = timezone.now()
    
    run.save(update_fields=[
        "status",
        "finished_at",
    ])  

    update_session_status(run.session)

    return run


def start_test_session(serial_number):
    device = Device.objects.get(
        serial_number = serial_number
    )
    session = TestSession.objects.create(
        device = device,
        status = TestSession.Status.RUNNING,
    )

    plan_items = TestPlanItem.objects.filter(
        model_phase__device_model=device.model,
        model_phase__phase__is_active=True, 
        test__is_active=True,
    ).order_by("model_phase__order", "order")
    for item in plan_items:
        TestRun.objects.create(
            session = session,
            test=item.test,
            status = TestRun.Status.PENDING
            
        )
    return session

def update_session_status(session):
    runs = session.test_runs.all()

    if runs.filter(
        status__in=[
            TestRun.Status.PENDING,
            TestRun.Status.RUNNING,
        ]
    ).exists():
        session.status = TestSession.Status.RUNNING
    elif runs.filter(
        status = TestRun.Status.FAILED
    ).exists():
        session.status = TestSession.Status.FAILED
    elif runs.exists() and not runs.exclude(
        status=TestRun.Status.PASSED
    ).exists():
        session.status = TestSession.Status.PASSED
    else:
       return

    session.save(update_fields=["status"]) 

def add_test_results(run_id, results):

    if not result:
        raise ValueError("Список результатов пуст")

    for item in results:
        if "name" not in item or "value" not in item:
            raise ValueError(
                "У результата должны быть поля name и value"
            )
    
    run = TestRun.objects.get(id = run_id)

    
    saved_results = []

    for item in results:
        result = TestResult.objects.create(
            test_run=run,
            name=item["name"],
            value=str(item["value"]),
            unit=item.get("unit", ""),
        )

        saved_results.append(result)

    return saved_results
