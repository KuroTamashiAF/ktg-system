from django.db import models
from django.conf import settings
from apps.core.models import TimeStampeModel
from .machine import Machine


class RepairLog(TimeStampeModel):

    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='repairs',
        verbose_name='Машина'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Кто отправил'
    )
    # Фактическая дата начала ремонта — может отличаться от created_at
    # Если дата введена вручную — берём её, иначе created_at
    repair_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Начало ремонта'
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Завершён'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    class Meta:
        verbose_name = 'Лог ремонта'
        verbose_name_plural = 'Логи ремонтов'
        ordering = ['-created_at']