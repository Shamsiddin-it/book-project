from django.conf import settings
from django.db import models

from books.models import Book


class Note(models.Model):
    """
    Заметка или цитата, оставленная пользователем на книге.
    Привязка идёт к произведению, а не к изданию: цитата остаётся той же,
    в какой обложке её ни читай.
    """

    class Kind(models.TextChoices):
        NOTE = 'note', 'Заметка'
        QUOTE = 'quote', 'Цитата'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='notes')
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.NOTE)
    text = models.TextField()
    page = models.PositiveIntegerField(null=True, blank=True)
    is_public = models.BooleanField(
        default=True,
        help_text='Видна ли заметка другим пользователям на публичной полке.',
    )
    has_spoilers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'book']),
        ]

    def __str__(self):
        return '{} — {} ({})'.format(self.user.username, self.book.name, self.get_kind_display())
