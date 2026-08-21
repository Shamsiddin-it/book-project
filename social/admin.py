from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, CommentLike, Follow, Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'created_at')
    search_fields = ('user__username', 'book__name')
    autocomplete_fields = ('book', 'user')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    autocomplete_fields = ('follower', 'following')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('follower', 'following')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'snippet', 'spoiler_badge', 'is_reply', 'created_at')
    list_display_links = ('id', 'snippet')
    list_filter = ('has_spoilers',)
    search_fields = ('user__username', 'book__name', 'text')
    autocomplete_fields = ('book', 'character', 'user', 'parent')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book', 'parent')

    @admin.display(description='Текст')
    def snippet(self, obj):
        return obj.text[:80] + ('...' if len(obj.text) > 80 else '')

    @admin.display(description='Спойлер')
    def spoiler_badge(self, obj):
        if not obj.has_spoilers:
            return '—'
        return format_html('<span style="color:#c2185b">спойлер</span>')

    @admin.display(description='Ответ', boolean=True)
    def is_reply(self, obj):
        return obj.parent_id is not None


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'comment', 'created_at')
    search_fields = ('user__username',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'comment')
