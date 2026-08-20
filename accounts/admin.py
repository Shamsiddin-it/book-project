from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Профиль книголюба', {
            'fields': ('role', 'phone', 'photo', 'birthdate', 'bio', 'is_shelf_public'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Профиль книголюба', {'fields': ('role', 'email')}),
    )
