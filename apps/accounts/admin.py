from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import User, Section


# Register your models here.




@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name','timezone',)
    search_fields = ('name',"timezone",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username', 'get_full_name',
        'role', 'section', 'is_active'
    )

    list_filter = ('role', 'section')

    fieldsets = UserAdmin.fieldsets + (
        ('Доп. данные', {
            'fields': ('patronim', 'section', 'role')
        }),
    )