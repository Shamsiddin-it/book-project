from django.contrib import admin

from server.admin_utils import thumbnail

from .models import Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'posts_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Материалов')
    def posts_count(self, obj):
        return obj.posts.count()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('cover_preview', 'title', 'author', 'is_published', 'published_at')
    list_display_links = ('cover_preview', 'title')
    list_filter = ('is_published', 'tags')
    list_editable = ('is_published',)
    search_fields = ('title', 'excerpt', 'body')
    filter_horizontal = ('tags',)
    readonly_fields = ('cover_large', 'created_at', 'updated_at')
    actions = ['publish', 'unpublish']
    save_on_top = True

    fieldsets = [
        (None, {'fields': ['title', 'excerpt', 'body']}),
        ('Обложка', {'fields': [('cover', 'cover_large')]}),
        ('Публикация', {
            'fields': ['tags', ('is_published', 'published_at')],
            'description': (
                'Адрес материала берётся из заголовка и после создания не меняется — '
                'иначе внешние ссылки перестанут работать. '
                'Дату можно поставить будущую: до неё материал виден только персоналу.'
            ),
        }),
        ('Служебное', {'fields': [('created_at', 'updated_at')], 'classes': ['collapse']}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')

    @admin.display(description='Обложка')
    def cover_preview(self, obj):
        return thumbnail(obj.cover, height=48)

    @admin.display(description='Текущая обложка')
    def cover_large(self, obj):
        return thumbnail(obj.cover, height=180)

    @admin.action(description='Опубликовать выбранные')
    def publish(self, request, queryset):
        # Через save(), а не update(): модель сама проставляет дату публикации.
        for post in queryset:
            post.is_published = True
            post.save()
        self.message_user(request, f'Опубликовано материалов: {queryset.count()}.')

    @admin.action(description='Снять с публикации')
    def unpublish(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'Снято с публикации: {updated}.')
