from django.contrib import admin
from apps.fleet.models import Machine, KTGHistory, RepairLog


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'board_number',
        'ktg_value', 'ktg_threshold',
        'is_in_repair', 'repair_started_at'
    )
    list_filter = ('is_in_repair',)
    search_fields = ('name', 'board_number')

    # Поля доступные для редактирования в форме машины
    fields = (
        'name', 'board_number',
        'ktg_value', 'ktg_threshold',
        'is_in_repair', 'repair_started_at',
        'image',
    )

@admin.register(KTGHistory)
class KTGHistoryAdmin(admin.ModelAdmin):
    list_display = ('machine', 'value', 'created_at')
    list_filter = ('machine',)


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = (
        'machine', 'user',
        'created_at', 'finished_at', 'is_active'
    )
    list_filter = ('is_active', 'machine')