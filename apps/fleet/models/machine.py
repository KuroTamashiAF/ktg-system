from django.db import models
from apps.core.models import TimeStampeModel


class Machine(TimeStampeModel):
    name = models.CharField(max_length=255, verbose_name="Название")
    board_number = models.CharField(
        max_length=50, unique=True, verbose_name="Бортовой номер"
    )
    ktg_value = models.FloatField(default=1.0, verbose_name="КТГ")
    ktg_threshold = models.FloatField(default=0.7, verbose_name="Порог КТГ")
    is_in_repair = models.BooleanField(default=False, verbose_name="В ремонте")
    image = models.ImageField(
        upload_to="machines/", blank=True, null=True, verbose_name="Фото"
    )

    def __str__(self):
        return f"{self.name} {self.board_number}"

    class Meta:
        verbose_name = "Машина"
        verbose_name_plural = "Машины"
