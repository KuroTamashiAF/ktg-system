from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from apps.accounts.forms import UserLoginForm


# Create your views here.
class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"
