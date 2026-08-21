from django.contrib import admin
from django.utils.html import format_html

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'stars', 'snippet', 'has_spoilers', 'created_at')
    list_display_links = ('id', 'snippet')
    list_filter = ('rating', 'has_spoilers')
    search_fields = ('user__username', 'book__name', 'text')
    autocomplete_fields = ('book', 'user')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book')

    @admin.display(description='Оценка', ordering='rating')
    def stars(self, obj):
        filled = '★' * obj.rating
        empty = '★' * (5 - obj.rating)
        return format_html(
            '<span style="color:#c2185b;letter-spacing:2px">{}</span>'
            '<span style="color:#ccc;letter-spacing:2px">{}</span>',
            filled,
            empty,
        )

    @admin.display(description='Текст')
    def snippet(self, obj):
        if not obj.text:
            return format_html('<span style="color:#999">только оценка</span>')
        return obj.text[:80] + ('...' if len(obj.text) > 80 else '')
