from django.contrib import admin
from apps.fleet.models import Machine, KTGHistory, RepairLog, KTGMonthResult


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "board_number",
        "section",
        "ktg_value",
        "ktg_threshold",
        "is_in_repair",
        "repair_started_at",
        "ktg_reset_at",
    )
    list_filter = ("is_in_repair",)
    search_fields = ("name", "board_number")

    # Поля доступные для редактирования в форме машины
    fields = (
        "name",
        "board_number",
        "section",
        "ktg_value",
        "ktg_threshold",
        "is_in_repair",
        "repair_started_at",
        "ktg_reset_at",
        "image",
    )


@admin.register(KTGHistory)
class KTGHistoryAdmin(admin.ModelAdmin):
    list_display = ("machine", "value", "created_at")
    list_filter = ("machine",)


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = ("machine", "user", "created_at", "finished_at", "is_active")
    list_filter = ("is_active", "machine")


@admin.register(KTGMonthResult)
class KTGMonthResultAdmin(admin.ModelAdmin):
    # Показываем итоги КТГ за периоды — только чтение
    # Записи создаются автоматически при сбросе, вручную не редактируются
    list_display = ('machine', 'value', 'period_start', 'period_end')
    list_filter = ('machine',)
    readonly_fields = ('machine', 'value', 'period_start', 'period_end')