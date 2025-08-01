from django.contrib import admin
from .models import Liked
@admin.register(Liked)
class LikedAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'created_at')
    search_fields = ('user__username', 'book__title')