app_name = "accounts"

from django.urls import path
from apps.accounts.views import UserLoginView, UserLogoutView, select_section_view

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("select-section/", select_section_view, name="select_section"),
]