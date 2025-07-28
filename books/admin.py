from django.contrib import admin
from .models import Category, Book, Edition, BookImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'authors', 'language', 'created_at']
    list_filter = ['language', 'categories']
    search_fields = ['name', 'authors', 'description']
    filter_horizontal = ['categories']


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'book', 'format', 'cover', 'isbn', 'publishing_year',
        'price', 'is_physical', 'is_active'
    ]
    list_filter = ['format', 'cover', 'is_physical', 'is_active']
    search_fields = ['book__name', 'isbn']
    inlines = [BookImageInline]


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'edition', 'image']
