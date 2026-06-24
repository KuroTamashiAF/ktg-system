from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/dashboard.html"
