from django.contrib import admin
from apps.accounts.models import CustomUser
from django.contrib.auth.admin import UserAdmin


# Register your models here.

admin.site.register(CustomUser, UserAdmin)