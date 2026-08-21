from django.contrib import admin
from django.utils.html import format_html

from server.admin_utils import thumbnail

from .models import ShelfItem


@admin.register(ShelfItem)
class ShelfItemAdmin(admin.ModelAdmin):
    list_display = (
        'cover_preview', 'user', 'edition', 'status', 'is_owned', 'progress_bar', 'added_at',
    )
    list_display_links = ('cover_preview', 'user')
    list_filter = ('status', 'is_owned')
    list_editable = ('status', 'is_owned')
    search_fields = ('user__username', 'edition__book__name')
    autocomplete_fields = ('edition', 'user')
    readonly_fields = ('added_at', 'finished_at', 'last_read_at')

    fieldsets = [
        (None, {'fields': [('user', 'edition')]}),
        ('Состояние', {
            'fields': [('status', 'is_owned'), ('progress_percent', 'position')],
            'description': (
                'is_owned означает «куплено» и открывает доступ к файлу книги. '
                'Пока оплата не подключена, эта галочка — единственный способ '
                'выдать доступ вручную.'
            ),
        }),
        ('Даты', {'fields': [('added_at', 'finished_at', 'last_read_at')]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'edition', 'edition__book',
        )

    @admin.display(description='Обложка')
    def cover_preview(self, obj):
        return thumbnail(obj.edition.cover, height=52)

    @admin.display(description='Прогресс')
    def progress_bar(self, obj):
        return format_html(
            '<div style="width:80px;height:8px;background:#eee;border-radius:4px;overflow:hidden">'
            '<div style="width:{}%;height:100%;background:#8fc0b0"></div></div>'
            '<small>{}%</small>',
            obj.progress_percent,
            obj.progress_percent,
        )
