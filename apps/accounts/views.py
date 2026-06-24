from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView


# Create your views here.
class UserLoginView(LoginView):
    template_name = "accounts/login.html"


class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"
