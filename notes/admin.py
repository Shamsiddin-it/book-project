from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'kind', 'page', 'is_public', 'created_at')
    list_filter = ('kind', 'is_public', 'has_spoilers')
    search_fields = ('user__username', 'book__name', 'text')
    autocomplete_fields = ('book',)
