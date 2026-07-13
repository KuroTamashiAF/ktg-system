from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from apps.fleet.models import Machine, KTGHistory, RepairLog, KTGMonthResult

# Create your views here.
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/dashboard.html"




class MachineDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная страница машины.
    DetailView автоматически берёт машину по pk из URL
    и передаёт в шаблон как object или machine.
    """
    model = Machine
    template_name = "fleet/machine_detail.html"
    context_object_name = "machine"  # в шаблоне будет {{ machine }}

    def get_context_data(self, **kwargs):
        """
        Добавляем дополнительные данные в контекст шаблона.
        super() вызывает родительский метод — он добавляет machine.
        Мы добавляем историю ремонтов и результаты КТГ.
        """
        context = super().get_context_data(**kwargs)
        machine = self.object

        # История ремонтов — последние 10
        context['repairs'] = RepairLog.objects.filter(
            machine=machine
        ).select_related('user').order_by('-created_at')[:10]

        # Результаты КТГ за периоды
        context['ktg_results'] = KTGMonthResult.objects.filter(
            machine=machine
        ).order_by('-period_end')[:12]  # последние 12 месяцев

        # История КТГ для графика — последние 100 точек
        context['ktg_history'] = KTGHistory.objects.filter(
            machine=machine
        ).order_by('-created_at')[:100]

        return context