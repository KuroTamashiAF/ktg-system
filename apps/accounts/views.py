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
        # Админ и диспетчер → выбор участка
        # Остальные → сразу на dashboard своего участка
        if self.request.user.role in ('admin', 'dispatcher'):
            return '/accounts/select-section/'
        return '/fleet/dashboard/'


class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"


@login_required
def select_section_view(request):
    """
    Страница выбора участка.
    Доступна только админу и диспетчеру.
    Остальные автоматически редиректятся на dashboard своего участка.
    """
    # Механик и viewer не должны попадать сюда
    # У них участок уже привязан в профиле
    if request.user.role not in ('admin', 'dispatcher'):
        return redirect('fleet:dashboard')

    if request.method == 'POST':
        section_id = request.POST.get('section_id')

        if section_id:
            # Временно меняем участок для просмотра
            # Это не меняет постоянный участок пользователя в БД
            # Сохраняем в сессию — не в модель
            request.session['viewed_section_id'] = int(section_id)

        return redirect('fleet:dashboard')

    sections = Section.objects.all()
    return render(request, 'accounts/select_section.html', {
        'sections': sections,
    })