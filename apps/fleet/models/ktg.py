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


class KTGMonthResult(TimeStampeModel):
    """
    Итоговый КТГ за период.
    Записывается автоматически когда наступает дата сброса ktg_reset_at.
    Хранит историю — какой КТГ машина показала за каждый месяц.
    """
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="ktg_results",
        verbose_name="Машина",
    )

    # КТГ который был ДО сброса — это и есть результат за период
    value = models.FloatField(verbose_name="Итоговый КТГ")

    # Когда начался период — предыдущая дата сброса
    period_start = models.DateTimeField(verbose_name="Начало периода")

    # Когда закончился период — момент сброса
    period_end = models.DateTimeField(verbose_name="Конец периода")

    def __str__(self):
        return (
            f"{self.machine.name} | "
            f"{self.period_start.strftime('%d.%m.%Y')} — "
            f"{self.period_end.strftime('%d.%m.%Y')} | "
            f"КТГ: {self.value:.4f}"
        )

    class Meta:
        verbose_name = "Результат КТГ за период"
        verbose_name_plural = "Результаты КТГ за период"
        ordering = ["-period_end"]

    