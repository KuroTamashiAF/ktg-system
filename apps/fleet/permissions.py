from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


"""
Единая точка принятия решений "кто что может с машиной".

До этого файла проверка роли/участка была в пяти разных местах:
  - MachineDetailView.test_func()      — проверял только роль
  - export_repairs_excel               — вообще не проверял
  - export_ktg_results_excel           — вообще не проверял
  - api_ktg_history / api_repairs_history — вообще не проверял
  - update_engine_hours                — вообще не проверял
  - FleetConsumer.get_machines()       — проверял участок, но для другой задачи (что показывать в списке)

Из-за этого можно было открыть чужую машину по прямому URL
(/fleet/machine/<pk>/export/repairs/, /api/ktg/, /engine-hours/)
и не наткнуться ни на одну из этих проверок — доступ ограничивался
только в вёрстке страницы, а не на сервере.

Теперь любое место, которое трогает конкретную машину, обязано
спросить can_view_machine() или can_edit_machine().
"""


def can_view_machine(user, machine):
    """
    Может ли пользователь СМОТРЕТЬ данные машины
    (страница машины, Excel-экспорты, API для графиков).

    admin, dispatcher — видят весь парк, любой участок.
                         Это диспетчерские роли, им по смыслу
                         нужен обзор всех участков, а не только своего.

    mechanic, viewer   — только машины СВОЕГО участка.
                         Если участок не назначен (user.section_id пустой) —
                         доступа нет вообще, а не "показываем всё".
                         Пустой участок — это незаконченная настройка
                         аккаунта, а не признак расширенных прав.
    """
    if user.role in ("admin", "dispatcher"):
        return True

    return user.section_id is not None and user.section_id == machine.section_id


def can_edit_machine(user, machine):
    """
    Может ли пользователь МЕНЯТЬ данные машины
    (вносить моточасы, ставить/завершать ремонт).

    viewer — никогда, ни на каком участке. Роль буквально
             называется "Просмотр" — у неё по определению
             нет права редактировать.

    Остальные — те же правила участка, что и для просмотра.
    """
    if user.role == "viewer":
        return False

    return can_view_machine(user, machine)


# ──────────────────────────────────────────────────────────────────
# Декоратор для view-функций вида def view(request, pk): ...
# ──────────────────────────────────────────────────────────────────



def machine_access_required(edit=False):
    """
    Декоратор для view-функций, принимающих pk машины в URL.

    Делает три вещи одним движением:
      1. Достаёт машину через get_object_or_404 — если pk не существует,
         отдаёт честный 404, а не необработанный DoesNotExist (500 с трейсбеком,
         который особенно опасен при случайно включённом DEBUG).
      2. Проверяет can_edit_machine() или can_view_machine() — в зависимости
         от edit=True/False.
      3. Передаёт уже загруженную machine во view как keyword-аргумент,
         чтобы не делать .get(pk=pk) ещё раз внутри функции.

    Использование:

        @login_required
        @machine_access_required()            # только просмотр
        def api_ktg_history(request, pk, machine):
            ...  # machine уже загружена и доступ уже проверен

        @login_required
        @machine_access_required(edit=True)   # нужно право редактировать
        def update_engine_hours(request, pk, machine):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, pk, *args, **kwargs):
            from apps.fleet.models import Machine

            machine = get_object_or_404(
                Machine.objects.select_related("section"), pk=pk
            )

            checker = can_edit_machine if edit else can_view_machine
            if not checker(request.user, machine):
                raise PermissionDenied("Нет доступа к этой машине")

            kwargs["machine"] = machine
            return view_func(request, pk, *args, **kwargs)

        return wrapped

    return decorator