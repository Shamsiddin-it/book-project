from django.conf import settings
from django.db import models

from books.models import Book, Character


class Like(models.Model):
    """Отметка «нравится» на произведении. Единственный источник правды для избранного."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_like'),
        ]

    def __str__(self):
        return f'{self.user.username} ♥ {self.book.name}'


class Follow(models.Model):
    """Подписка на аккаунт с похожими вкусами."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow'),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')),
                name='no_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.follower.username} → {self.following.username}'


class Comment(models.Model):
    """
    Обсуждение книги. Ответы делаются через parent, так получается ветка.
    Необязательная привязка к герою позволяет обсуждать конкретного персонажа.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies'
    )
    text = models.TextField()
    has_spoilers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username} о «{self.book.name}»'


class CommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'comment'], name='unique_comment_like'),
        ]

    def __str__(self):
        return f'{self.user.username} ♥ comment #{self.comment_id}'
