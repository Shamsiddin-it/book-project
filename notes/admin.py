from django.contrib import admin
from django.utils.html import format_html

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'kind', 'snippet', 'page', 'visibility', 'created_at')
    list_display_links = ('id', 'snippet')
    list_filter = ('kind', 'is_public', 'has_spoilers')
    search_fields = ('user__username', 'book__name', 'text')
    autocomplete_fields = ('book', 'user')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book')

    @admin.display(description='Текст')
    def snippet(self, obj):
        return obj.text[:80] + ('...' if len(obj.text) > 80 else '')

    @admin.display(description='Видно')
    def visibility(self, obj):
        if obj.is_public:
            return format_html('<span style="color:#2e7d32">всем</span>')
        return format_html('<span style="color:#999">только автору</span>')
