from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.accounts.forms import UserLoginForm
from apps.accounts.models import Section


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "accounts/login.html"
    # redirect_authenticated_user = True  — закомментировано, конфликтует

    def get_success_url(self):
        """
        После успешного входа — редиректим на выбор участка.
        Не на dashboard сразу, а сначала выбрать участок.
        """
        return '/accounts/select-section/'


class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"


@login_required
def select_section_view(request):
    """
    Страница выбора участка после входа.
    GET  — показываем список участков.
    POST — сохраняем выбранный участок и идём на dashboard.
    """
    if request.method == 'POST':
        section_id = request.POST.get('section_id')

        if section_id:
            # Сохраняем участок у пользователя
            request.user.section_id = section_id
            request.user.save()

        # После выбора — на dashboard
        return redirect('dashboard')

    # GET — показываем все доступные участки
    sections = Section.objects.all()
    return render(request, 'accounts/select_section.html', {
        'sections': sections
    })