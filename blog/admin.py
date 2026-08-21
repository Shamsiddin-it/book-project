from django.contrib import admin

from .models import Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'is_published', 'published_at')
    list_filter = ('is_published', 'tags')
    search_fields = ('title', 'excerpt', 'body')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')
