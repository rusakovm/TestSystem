from django.db import models


class DeviceModel(models.Model):
    name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TestParameter(models.Model):
    FIELD_TYPES = [
        ("text", "Текст"),
        ("number", "Число"),
        ("choice", "Выбор"),
    ]

    test = models.ForeignKey(
        "TestDefinition",
        on_delete=models.CASCADE,
        related_name="parameters",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        default="text",
    )
    unit = models.CharField(max_length=20, blank=True)
    choices_text = models.TextField(
        blank=True,
        help_text="Для поля 'Выбор': один вариант на строку",
    )
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["test", "code"],
                name="unique_test_parameter_code",
            ),
        ]

    @property
    def options(self):
        return [
            option.strip()
            for option in self.choices_text.splitlines()
            if option.strip()
        ]

    def __str__(self):
        return f"{self.test.code}: {self.name}"


class Device(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        TESTING = "testing", "Тестируется"
        PASSED = "passed", "Успешно"
        FAILED = "failed", "Ошибка"

    serial_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    model = models.ForeignKey(
        DeviceModel,
        on_delete=models.PROTECT,
        related_name="devices",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.serial_number


class Phase(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ModelPhase(models.Model):
    device_model = models.ForeignKey(
        DeviceModel,
        on_delete=models.CASCADE,
        related_name="model_phases",
    )
    phase = models.ForeignKey(
        Phase,
        on_delete=models.PROTECT,
        related_name="model_phases",
    )
    order = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device_model", "phase"],
                name="unique_model_phase",
            ),
            models.UniqueConstraint(
                fields=["device_model", "order"],
                name="unique_model_phase_order",
            ),
        ]
        ordering = ["order"]

    def __str__(self):
        return f"{self.device_model.name} — {self.phase.name}"


class TestDefinition(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TestPlanItem(models.Model):
    model_phase = models.ForeignKey(
        ModelPhase,
        on_delete=models.CASCADE,
        related_name="tests",
    )
    test = models.ForeignKey(
        TestDefinition,
        on_delete=models.PROTECT,
        related_name="plan_items",
    )
    order = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["model_phase", "test"],
                name="unique_test_in_phase",
            ),
            models.UniqueConstraint(
                fields=["model_phase", "order"],
                name="unique_test_order_in_phase",
            ),
        ]
        ordering = ["order"]

    def __str__(self):
        return f"{self.model_phase} — {self.test.name}"


class TestSession(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Выполняется"
        PASSED = "passed", "Успешно"
        FAILED = "failed", "Ошибка"
        CANCELLED = "cancelled", "Отменено"

    device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.device.serial_number} — {self.status}"


class TestRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        RUNNING = "running", "Выполняется"
        PASSED = "passed", "Успешно"
        FAILED = "failed", "Ошибка"
        SKIPPED = "skipped", "Пропущен"

    session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        related_name="test_runs",
    )
    test = models.ForeignKey(
        TestDefinition,
        on_delete=models.PROTECT,
        related_name="runs",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.session.device.serial_number} — {self.test.code}"


class TestResult(models.Model):
    test_run = models.ForeignKey(
        TestRun,
        on_delete=models.CASCADE,
        related_name="results",
    )
    name = models.CharField(max_length=100)
    value = models.TextField()
    unit = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["test_run", "name"],
                name="unique_test_result_per_run",
            ),
        ]

    def __str__(self):
        return f"{self.test_run.test.code} — {self.name}: {self.value}"
