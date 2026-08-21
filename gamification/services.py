"""
Подсчёт статистики читателя, выдача наград и определение ступени.

Очки не хранятся отдельным полем, а считаются из фактических данных. Так они
не могут разойтись с реальностью: откатили покупку, удалили отзыв — счёт сам
стал верным. Хранить приходится только факт получения награды, потому что у
него есть дата, которую иначе неоткуда взять.
"""

from django.db import IntegrityError, transaction
from django.db.models import Count

from notes.models import Note
from reviews.models import Review
from shelf.models import ShelfItem

from .models import Level, Metric, Trophy, UserTrophy

# Сколько очков даёт единица каждой метрики.
# Прочитанная книга весит больше отзыва, отзыв — больше заметки:
# это соответствует затраченному усилию.
POINTS_PER_UNIT = {
    Metric.BOOKS_READ: 10,
    Metric.REVIEWS_WRITTEN: 3,
    Metric.NOTES_WRITTEN: 1,
    Metric.GENRES_EXPLORED: 5,
    Metric.LANGUAGES_READ: 15,
}


def collect_metrics(user):
    """Считает все метрики пользователя. Один запрос на метрику, не больше."""
    read_items = ShelfItem.objects.filter(user=user, status=ShelfItem.Status.READ)

    # distinct по книге: два издания одного произведения — это одна прочитанная книга.
    books_read = read_items.values('edition__book_id').distinct().count()

    genres = (
        read_items.exclude(edition__book__categories__isnull=True)
        .values('edition__book__categories')
        .distinct()
        .count()
    )
    languages = read_items.values('edition__book__language').distinct().count()

    return {
        Metric.BOOKS_READ: books_read,
        Metric.REVIEWS_WRITTEN: Review.objects.filter(user=user).count(),
        Metric.NOTES_WRITTEN: Note.objects.filter(user=user).count(),
        Metric.GENRES_EXPLORED: genres,
        Metric.LANGUAGES_READ: languages,
    }


def calculate_points(metrics, earned_trophies=()):
    """Очки за активность плюс бонусы за сами награды."""
    total = sum(
        value * POINTS_PER_UNIT.get(metric, 0) for metric, value in metrics.items()
    )
    total += sum(trophy.points for trophy in earned_trophies)
    return total


def award_trophies(user, metrics):
    """
    Выдаёт награды, порог которых пройден.

    Возвращает список только что выданных — вызывающий код может показать
    пользователю «вы получили награду».
    """
    already_earned = set(
        UserTrophy.objects.filter(user=user).values_list('trophy_id', flat=True)
    )
    candidates = Trophy.objects.filter(is_active=True).exclude(pk__in=already_earned)

    newly_awarded = []
    for trophy in candidates:
        if metrics.get(trophy.metric, 0) >= trophy.threshold:
            try:
                with transaction.atomic():
                    UserTrophy.objects.create(user=user, trophy=trophy)
            except IntegrityError:
                # Параллельный запрос успел выдать ту же награду — это не ошибка.
                continue
            newly_awarded.append(trophy)

    return newly_awarded


def resolve_level(points):
    """Текущая ступень и прогресс до следующей."""
    levels = list(Level.objects.order_by('min_points'))
    if not levels:
        return {'level': None, 'next_level': None, 'points_to_next': None, 'progress': 0}

    current = levels[0]
    for level in levels:
        if points >= level.min_points:
            current = level
        else:
            break

    following = next((level for level in levels if level.min_points > points), None)

    if following is None:
        # Максимальная ступень: прогресс всегда полный, иначе на витрине
        # получится вечные 87% без возможности их закрыть.
        return {'level': current, 'next_level': None, 'points_to_next': 0, 'progress': 100}

    span = following.min_points - current.min_points
    gained = points - current.min_points
    progress = int(round(gained / span * 100)) if span > 0 else 0

    return {
        'level': current,
        'next_level': following,
        'points_to_next': following.min_points - points,
        'progress': max(0, min(100, progress)),
    }


def build_profile(user):
    """Полная картина для страницы Level & Trophy."""
    metrics = collect_metrics(user)
    newly_awarded = award_trophies(user, metrics)

    earned = list(
        UserTrophy.objects.filter(user=user).select_related('trophy')
    )
    points = calculate_points(metrics, [item.trophy for item in earned])

    return {
        'metrics': metrics,
        'points': points,
        'earned': earned,
        'newly_awarded': newly_awarded,
        **resolve_level(points),
    }


def trophy_catalogue(user):
    """
    Все награды с отметкой, получена ли, и текущим прогрессом по каждой.

    Показывать невыполненные тоже важно: без этого непонятно, к чему стремиться.
    """
    metrics = collect_metrics(user) if user.is_authenticated else {}
    earned_at = {
        item.trophy_id: item.earned_at
        for item in UserTrophy.objects.filter(user=user)
    } if user.is_authenticated else {}

    catalogue = []
    for trophy in Trophy.objects.filter(is_active=True):
        current = metrics.get(trophy.metric, 0)
        catalogue.append({
            'trophy': trophy,
            'earned': trophy.id in earned_at,
            'earned_at': earned_at.get(trophy.id),
            'current': current,
            'progress': (
                min(100, int(round(current / trophy.threshold * 100)))
                if trophy.threshold else 100
            ),
        })
    return catalogue
