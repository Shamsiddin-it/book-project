from django.conf import settings
from django.db import models


class Metric(models.TextChoices):
    """
    По чему считается достижение.

    Намеренно нет метрики за лайки и добавления в корзину: их ставят одним
    кликом и в любом количестве, награда за них превращается в накрутку.
    Считаем только то, что требует реального чтения или письменного усилия.
    """

    BOOKS_READ = 'books_read', 'Прочитано книг'
    REVIEWS_WRITTEN = 'reviews_written', 'Написано отзывов'
    NOTES_WRITTEN = 'notes_written', 'Оставлено заметок и цитат'
    GENRES_EXPLORED = 'genres_explored', 'Освоено жанров'
    LANGUAGES_READ = 'languages_read', 'Языков прочитано'


class Level(models.Model):
    """
    Ступень читателя. Пороги лежат в базе, а не в коде, чтобы их можно было
    перенастроить из админки, не выкатывая релиз.
    """

    number = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=60)
    min_points = models.PositiveIntegerField(
        unique=True, help_text='Сколько очков нужно набрать, чтобы достичь ступени.',
    )
    icon = models.CharField(max_length=8, blank=True, help_text='Эмодзи для значка.')

    class Meta:
        ordering = ['number']

    def __str__(self):
        return '{}. {}'.format(self.number, self.name)


class Trophy(models.Model):
    """
    Достижение. Условие описано данными — метрика плюс порог, — поэтому новые
    награды заводятся в админке без единой строчки кода.
    """

    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text='Эмодзи для значка.')

    metric = models.CharField(max_length=20, choices=Metric.choices)
    threshold = models.PositiveIntegerField(help_text='Значение метрики, с которого награда выдаётся.')

    points = models.PositiveIntegerField(
        default=0, help_text='Сколько очков добавляет само получение награды.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['metric', 'threshold']
        verbose_name_plural = 'trophies'

    def __str__(self):
        return '{} ({} ≥ {})'.format(self.name, self.get_metric_display(), self.threshold)


class UserTrophy(models.Model):
    """Полученная награда. Дата хранится, чтобы показать «получено 3 марта»."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trophies',
    )
    trophy = models.ForeignKey(Trophy, on_delete=models.CASCADE, related_name='awards')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-earned_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'trophy'], name='unique_user_trophy'),
        ]

    def __str__(self):
        return '{} — {}'.format(self.user.username, self.trophy.name)
