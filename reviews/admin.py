from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'rating', 'has_spoilers', 'created_at')
    list_filter = ('rating', 'has_spoilers')
    search_fields = ('user__username', 'book__name', 'text')
    autocomplete_fields = ('book',)
