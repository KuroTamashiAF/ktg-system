"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from .views import export_repairs_excel, export_ktg_results_excel
app_name = "fleet"


from django.urls import path
from apps.fleet.views import DashboardView, MachineDetailView, api_ktg_history, api_repairs_history, update_engine_hours

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("machine/<int:pk>/", MachineDetailView.as_view(), name="machine_detail"),
    path("machine/<int:pk>/export/repairs/", export_repairs_excel, name="export_repairs"),
    path("machine/<int:pk>/export/ktg/", export_ktg_results_excel, name="export_ktg"),
    # api для графиков 
    path("machine/<int:pk>/api/ktg/", api_ktg_history, name="api_ktg"),
    path("machine/<int:pk>/api/repairs/", api_repairs_history, name="api_repairs"),
    # для моточасов 
    path("machine/<int:pk>/engine-hours/", update_engine_hours, name="update_engine_hours"),
]
