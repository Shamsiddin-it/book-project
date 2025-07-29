from django.contrib import admin
from .models import Category, Book, BookImage, Author, BookAuthor


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_authors', 'language', 'created_at']
    list_filter = ['language', 'categories']
    search_fields = ['name', 'description']
    filter_horizontal = ['categories']
    inlines = [BookAuthorInline]

    def get_authors(self, obj):
        return ", ".join([author.name for author in obj.authors.all()])
    get_authors.short_description = 'Authors'




@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'image']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
