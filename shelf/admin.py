from django.contrib import admin
from .models import BookShelf
# Register your models here.
@admin.register(BookShelf)
class BookShelfAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'created_at')
    search_fields = ('user__username', 'book__title')