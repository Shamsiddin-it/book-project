from django.contrib import admin

from .models import Comment, CommentLike, Follow, Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'created_at')
    search_fields = ('user__username', 'book__name')
    autocomplete_fields = ('book',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'character', 'has_spoilers', 'created_at')
    list_filter = ('has_spoilers',)
    search_fields = ('user__username', 'book__name', 'text')
    autocomplete_fields = ('book', 'character')


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'comment', 'created_at')
