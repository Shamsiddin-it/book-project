from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Author, Book, BookAuthor, Category, Character, Edition, MoodboardImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'subcategory_of']
    list_filter = ['subcategory_of']
    search_fields = ['name']


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1
    autocomplete_fields = ['author']


class EditionInline(admin.TabularInline):
    model = Edition
    extra = 1
    fields = [
        'format', 'cover', 'isbn', 'publisher', 'published_year',
        'pages', 'price', 'old_price', 'is_active',
    ]


class MoodboardImageInline(admin.TabularInline):
    model = MoodboardImage
    extra = 6  # По ТЗ мудборд состоит из шести изображений.
    max_num = 6
    fields = ['image', 'position']


class CharacterInline(admin.StackedInline):
    model = Character
    extra = 1
    fields = ['name', 'image', 'signature_quote', 'is_main']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_authors', 'language', 'editions_count', 'colour_chip', 'created_at']
    list_filter = ['language', 'is_active', 'categories']
    search_fields = ['name', 'description', 'authors__name']
    filter_horizontal = ['categories']
    inlines = [BookAuthorInline, EditionInline, MoodboardImageInline, CharacterInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('authors', 'editions')

    @admin.display(description='Авторы')
    def get_authors(self, obj):
        return ', '.join(author.name for author in obj.authors.all()) or '—'

    @admin.display(description='Изданий')
    def editions_count(self, obj):
        return obj.editions.count()

    @admin.display(description='Акцент')
    def colour_chip(self, obj):
        if not obj.accent_color:
            return '—'
        return format_html(
            '<span style="display:inline-block;width:18px;height:18px;'
            'border:1px solid #999;background:{}"></span> {}',
            obj.accent_color,
            obj.accent_color,
        )


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'format', 'isbn', 'price', 'old_price', 'is_active']
    list_filter = ['format', 'is_active']
    search_fields = ['book__name', 'isbn', 'publisher']
    autocomplete_fields = ['book']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'books_amount']
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            books_amount=Count('books', distinct=True),
        )

    @admin.display(description='Книг', ordering='books_amount')
    def books_amount(self, obj):
        return obj.books_amount


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'book', 'is_main']
    list_filter = ['is_main']
    search_fields = ['name', 'book__name']


@admin.register(MoodboardImage)
class MoodboardImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'position']
    search_fields = ['book__name']
