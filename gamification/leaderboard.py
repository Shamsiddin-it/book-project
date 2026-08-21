"""
Таблица лидеров.

Личный профиль считает метрики по одному пользователю — там цикл незаметен.
Для таблицы такой подход не годится: пять запросов на человека превращаются
в сотни. Поэтому каждая метрика оформлена подзапросом, и вся таблица
собирается двумя запросами независимо от числа участников.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce

from notes.models import Note
from reviews.models import Review
from shelf.models import ShelfItem

from .models import Level, Metric, UserTrophy
from .services import POINTS_PER_UNIT

User = get_user_model()


def _count_subquery(queryset, distinct_field):
    """
    Подзапрос «сколько у этого пользователя ...».

    values('user') задаёт группировку по пользователю, иначе Count схлопнул бы
    всю таблицу в одно число.
    """
    return Subquery(
        queryset.filter(user=OuterRef('pk'))
        .values('user')
        .annotate(total=Count(distinct_field, distinct=True))
        .values('total')[:1],
        output_field=IntegerField(),
    )


def leaderboard_rows(limit):
    read_items = ShelfItem.objects.filter(status=ShelfItem.Status.READ)

    users = (
        User.objects.filter(is_shelf_public=True)
        .annotate(
            books_read=Coalesce(_count_subquery(read_items, 'edition__book'), 0),
            genres_explored=Coalesce(
                _count_subquery(read_items, 'edition__book__categories'), 0,
            ),
            languages_read=Coalesce(
                _count_subquery(read_items, 'edition__book__language'), 0,
            ),
            reviews_written=Coalesce(_count_subquery(Review.objects.all(), 'id'), 0),
            notes_written=Coalesce(_count_subquery(Note.objects.all(), 'id'), 0),
        )
        # Пустые профили в таблице лидеров не нужны — она бы состояла из нулей.
        .filter(books_read__gt=0)
    )

    # Сумма очков за награды, а не их количество: у наград разный вес.
    trophy_points = {
        row['user_id']: row['total'] or 0
        for row in UserTrophy.objects.values('user_id').annotate(
            total=Sum('trophy__points'),
        )
    }

    rows = []
    for user in users:
        metrics = {
            Metric.BOOKS_READ: user.books_read,
            Metric.REVIEWS_WRITTEN: user.reviews_written,
            Metric.NOTES_WRITTEN: user.notes_written,
            Metric.GENRES_EXPLORED: user.genres_explored,
            Metric.LANGUAGES_READ: user.languages_read,
        }
        points = sum(
            value * POINTS_PER_UNIT.get(metric, 0) for metric, value in metrics.items()
        )
        points += trophy_points.get(user.id, 0)

        rows.append({
            'user': user,
            'points': points,
            'books_read': user.books_read,
        })

    # При равенстве очков — по имени, чтобы порядок был устойчивым между запросами.
    rows.sort(key=lambda row: (-row['points'], row['user'].username))
    rows = rows[:limit]

    # Ступени читаем один раз: resolve_level внутри цикла ходил бы в базу
    # на каждую строку таблицы.
    levels = list(Level.objects.order_by('min_points'))

    for index, row in enumerate(rows, start=1):
        row['rank'] = index
        row['level'] = next(
            (level for level in reversed(levels) if row['points'] >= level.min_points),
            None,
        )

    return rows
