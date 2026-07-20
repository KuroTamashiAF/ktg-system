from django.db import models
from apps.core.models import TimeStampeModel


class Machine(TimeStampeModel):
    name = models.CharField(max_length=255, verbose_name="Название")

    board_number = models.CharField(
        max_length=50,
        verbose_name="Бортовой номер"
        # unique убрали — бортовой номер может повторяться у разных заказчиков
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Серийный номер"
    )

    project_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Номер проекта"
    )

    customer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Заказчик"
    )

    # Моточасы — вводятся вручную на странице машины
    engine_hours = models.FloatField(
        default=0,
        verbose_name="Моточасы"
    )

    ktg_value = models.FloatField(default=1.0, verbose_name="КТГ")
    ktg_threshold = models.FloatField(default=0.7, verbose_name="Порог КТГ")
    ktg_reset_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Плановый сброс КТГ"
    )
    is_in_repair = models.BooleanField(default=False, verbose_name="В ремонте")
    repair_started_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Начало ремонта (вручную)"
    )
    ktg_calc_from = models.DateTimeField(
        null=True, blank=True, verbose_name="КТГ считать от"
    )

    image = models.ImageField(
        upload_to="machines/", blank=True, null=True, verbose_name="Фото"
    )

    section = models.ForeignKey(
        "accounts.Section",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Участок",
        related_name="machines",
    )

    def __str__(self):
        return f"{self.name} ({self.board_number}) — {self.customer or 'без заказчика'}"

    class Meta:
        verbose_name = "Машина"
        verbose_name_plural = "Машины"