from django.contrib import admin

from .models import (
    DeviceModel,
    Device,
    Phase,
    ModelPhase,
    TestDefinition,
    TestParameter,
    TestPlanItem,
    TestRun,
    TestResult,
    TestSession,
)

class TestRunInline(admin.TabularInline):
    model = TestRun
    extra = 0
    show_change_link = True

    fields = (
        "test",
        "status",
        "started_at",
        "finished_at",
    )


class TestParameterInline(admin.TabularInline):
    model = TestParameter
    extra = 1
    fields = (
        "name",
        "code",
        "field_type",
        "unit",
        "choices_text",
        "is_required",
        "order",
    )



class TestResultInline(admin.TabularInline):
    model = TestResult
    extra = 0

    fields = (
        "name",
        "value",
        "unit",
    )


admin.site.register(DeviceModel)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "serial_number",
        "model",
        "status",
        "created_at",
    )

    search_fields = (
        "serial_number",
        "model__name",
    )

    list_filter = (
        "status",
        "model",
    )

    ordering = ("-created_at",)

admin.site.register(Phase)
admin.site.register(ModelPhase)

admin.site.register(TestPlanItem)


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    inlines = [TestParameterInline]

@admin.register(TestSession)
class AdminTestSession(admin.ModelAdmin):
    list_display = (
        "id",
        "device",
        "status",
        "started_at",
        "finished_at",
    )
    search_fields = (
         "device__serial_number",
    )

    list_filter = (
        "status",
    )

    inlines = [TestRunInline]

@admin.register(TestRun)
class AdminTestRun(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "test",
        "status",
        "started_at",
        "finished_at",
    )

    search_fields = (
        "session__device__serial_number",
        "test__code",
    )

    list_filter = (
        "status",
        "test",
    )

    inlines = [TestResultInline]

@admin.register(TestResult)
class AdminTestResult(admin.ModelAdmin):

    list_display = (
        "id",
        "test_run",
        "name",
        "value",
        "unit",
        "created_at",
    )

    search_fields = (
        "name",
        "test_run__session__device__serial_number",
    )

    list_filter = (
        "name",
    )
    
    

