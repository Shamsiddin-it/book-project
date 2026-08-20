from django.conf import settings
from django.db import models

from books.models import Edition


class ShelfItem(models.Model):
    """
    Виртуальная книжная полка. Заводится автоматически по факту покупки
    или когда пользователь сам добавляет издание.
    Хранит именно Edition, потому что обложку пользователь выбирает сам.
    """

    class Status(models.TextChoices):
        WANT_TO_READ = 'want', 'Хочу прочитать'
        READING = 'reading', 'Читаю'
        READ = 'read', 'Прочитано'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shelf')
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name='shelf_items')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.WANT_TO_READ)
    is_owned = models.BooleanField(default=False, help_text='Куплено пользователем.')
    progress_percent = models.PositiveSmallIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'edition'], name='unique_user_edition_on_shelf'),
        ]

    def __str__(self):
        return f'{self.user.username}: {self.edition} — {self.get_status_display()}'
