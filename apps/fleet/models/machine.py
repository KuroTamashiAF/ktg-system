from django.db import models
from apps.core.models import TimeStampeModel


class Machine(TimeStampeModel):
    name = models.CharField(max_length=255, verbose_name="Название")
    board_number = models.CharField(
        max_length=50, unique=True, verbose_name="Бортовой номер"
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
        related_name="machines" )

    def __str__(self):
        return f"{self.name} {self.board_number}"

    class Meta:
        verbose_name = "Машина"
        verbose_name_plural = "Машины"
