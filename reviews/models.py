from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from books.models import Book


class Review(models.Model):
    """
    Оценка книги от 1 до 5 со звёздами на карточке.

    Отзыв ставится произведению, а не изданию: читатель оценивает текст,
    а не качество переплёта. Один пользователь — один отзыв на книгу,
    иначе средний балл легко накрутить.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews',
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField(blank=True, help_text='Необязательно: можно поставить только оценку.')
    has_spoilers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_review'),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='rating_between_1_and_5',
            ),
        ]
        indexes = [
            models.Index(fields=['book', '-created_at']),
        ]

    def __str__(self):
        return '{} — {} ({}★)'.format(self.user.username, self.book.name, self.rating)
