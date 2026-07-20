from django.db import models
from django.conf import settings
from apps.core.models import TimeStampeModel
from .machine import Machine


class EngineHoursLog(TimeStampeModel):
    """
    Лог внесения моточасов.
    Каждый раз когда вносятся моточасы — создаётся запись.
    Нельзя вносить значение меньше или равное предыдущему.
    """
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='engine_hours_log',
        verbose_name='Машина'
    )

    # Новое значение моточасов
    value = models.FloatField(verbose_name='Моточасы')

    # Кто внёс
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Кто внёс'
    )

    def __str__(self):
        return f"{self.machine.name} — {self.value} м/ч ({self.created_at})"

    class Meta:
        verbose_name = 'Лог моточасов'
        verbose_name_plural = 'Лог моточасов'
        ordering = ['-created_at']