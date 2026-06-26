from django.db import models
from apps.core.models import TimeStampeModel
from .machine import Machine


class KTGHistory(TimeStampeModel):

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="ktg_history",
        verbose_name="Машина",
    )

    value = models.FloatField(verbose_name="Значение КТГ")

    class Meta:
        verbose_name = "История КТГ"
        verbose_name_plural = "История КТГ"
        ordering = ["-created_at"]
