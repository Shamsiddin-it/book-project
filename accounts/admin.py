from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from server.admin_utils import thumbnail

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        'photo_preview', 'username', 'email', 'role',
        'books_on_shelf', 'is_shelf_public', 'is_staff', 'is_active',
    )
    list_display_links = ('photo_preview', 'username')
    list_filter = ('role', 'is_staff', 'is_active', 'is_shelf_public')
    list_editable = ('is_active',)
    search_fields = ('username', 'email')
    readonly_fields = ('photo_large', 'date_joined', 'last_login')

    fieldsets = UserAdmin.fieldsets + (
        ('Профиль книголюба', {
            'fields': (
                'role',
                ('photo', 'photo_large'),
                ('phone', 'birthdate'),
                'bio',
                'is_shelf_public',
            ),
            'description': (
                'Если полка закрыта, от других прячутся и книги, и цитаты, '
                'и статистика чтения.'
            ),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Профиль книголюба', {'fields': ('role', 'email')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(shelf_total=Count('shelf'))

    @admin.display(description='Фото')
    def photo_preview(self, obj):
        return thumbnail(obj.photo, height=40, radius=20)

    @admin.display(description='Текущее фото')
    def photo_large(self, obj):
        return thumbnail(obj.photo, height=160, radius=80)

    @admin.display(description='На полке', ordering='shelf_total')
    def books_on_shelf(self, obj):
        return obj.shelf_total
