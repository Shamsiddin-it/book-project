from django.contrib import admin

from .models import ShelfItem


@admin.register(ShelfItem)
class ShelfItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'edition', 'status', 'is_owned', 'progress_percent', 'added_at')
    list_filter = ('status', 'is_owned')
    search_fields = ('user__username', 'edition__book__name')
    autocomplete_fields = ('edition',)
