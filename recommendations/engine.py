"""
Рекомендации на коллаборативной фильтрации по совстречаемости.

Подход намеренно простой и без внешних зависимостей: считаем, сколько общих
читателей у пары книг, и этим ранжируем. На объёмах книжного магазина такой
подсчёт делается в базе и не требует ни обучения модели, ни отдельного сервиса.

Слабое место любой коллаборативной фильтрации — холодный старт: пока лайков
мало, рекомендовать не из чего. Поэтому у каждой выдачи есть запасной путь:
сначала пробуем совстречаемость, потом добираем по жанрам и авторам,
и в самом конце — просто популярным.
"""

from django.db.models import Avg, Count, Q

from books.models import Book
from shelf.models import ShelfItem
from social.models import Like

DEFAULT_LIMIT = 10


def _books():
    """
    Базовая выборка книг для выдачи.

    Аннотации обязательны: BookListSerializer ждёт average_rating и
    reviews_count, и без них поля молча пропадают из ответа — фронт получает
    undefined там, где по типам должно быть число.
    """
    return Book.objects.annotate(
        average_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews', distinct=True),
    ).prefetch_related('authors', 'editions')

# Статусы полки, которые считаем осознанным интересом.
# «Хочу прочитать» не в счёт: туда складывают наугад.
MEANINGFUL_STATUSES = (ShelfItem.Status.READING, ShelfItem.Status.READ)


def _taste_book_ids(user):
    """Книги, которыми пользователь показал вкус: лайкнул или читает/прочитал."""
    if not user.is_authenticated:
        return set()

    liked = Like.objects.filter(user=user).values_list('book_id', flat=True)
    shelved = ShelfItem.objects.filter(
        user=user, status__in=MEANINGFUL_STATUSES,
    ).values_list('edition__book_id', flat=True)

    return set(liked) | set(shelved)


def _readers_of(book_ids):
    """Пользователи, которые проявили интерес хотя бы к одной из этих книг."""
    if not book_ids:
        return set()

    liked = Like.objects.filter(book_id__in=book_ids).values_list('user_id', flat=True)
    shelved = ShelfItem.objects.filter(
        edition__book_id__in=book_ids, status__in=MEANINGFUL_STATUSES,
    ).values_list('user_id', flat=True)

    return set(liked) | set(shelved)


def _co_occurrence_scores(reader_ids, exclude_book_ids):
    """
    Сколько из этих читателей интересовались каждой книгой.

    Считаем по лайкам и полке отдельно, потом складываем в питоне: объединять
    два multivalued-джойна одним запросом — верный способ получить произведение
    строк вместо суммы.
    """
    if not reader_ids:
        return {}

    scores = {}

    likes = (
        Like.objects.filter(user_id__in=reader_ids)
        .exclude(book_id__in=exclude_book_ids)
        .values('book_id')
        .annotate(weight=Count('user_id', distinct=True))
    )
    for row in likes:
        scores[row['book_id']] = scores.get(row['book_id'], 0) + row['weight']

    shelved = (
        ShelfItem.objects.filter(user_id__in=reader_ids, status__in=MEANINGFUL_STATUSES)
        .exclude(edition__book_id__in=exclude_book_ids)
        .values('edition__book_id')
        .annotate(weight=Count('user_id', distinct=True))
    )
    for row in shelved:
        book_id = row['edition__book_id']
        scores[book_id] = scores.get(book_id, 0) + row['weight']

    return scores


def _ordered_books(book_ids):
    """Достаёт книги и раскладывает их в том же порядке, что и переданные id."""
    if not book_ids:
        return []

    books = _books().filter(pk__in=book_ids, is_active=True)
    by_id = {book.id: book for book in books}
    return [by_id[book_id] for book_id in book_ids if book_id in by_id]


def _popular_books(exclude_ids, limit, language=None):
    """Запасной вариант: просто самое залайканное."""
    queryset = _books().filter(is_active=True).exclude(pk__in=exclude_ids)
    if language:
        queryset = queryset.filter(language=language)

    return list(
        queryset.annotate(likes_total=Count('likes', distinct=True))
        .order_by('-likes_total', '-created_at')[:limit]
    )


def similar_to_book(book, limit=DEFAULT_LIMIT, user=None):
    """
    «Если вам понравилась эта книга, прочтите…»

    Порядок: общие читатели → те же жанры и авторы → популярное на том же языке.
    """
    exclude_ids = {book.id}
    if user is not None and user.is_authenticated:
        # Уже прочитанное рекомендовать незачем.
        exclude_ids |= _taste_book_ids(user)

    readers = _readers_of([book.id])
    scores = _co_occurrence_scores(readers, exclude_ids)

    ranked_ids = [
        book_id for book_id, _ in
        sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    ]
    result = _ordered_books(ranked_ids)[:limit]

    if len(result) >= limit:
        return result

    # Добираем по содержательному сходству: те же категории или тот же автор.
    taken = exclude_ids | {item.id for item in result}
    category_ids = list(book.categories.values_list('id', flat=True))
    author_ids = list(book.authors.values_list('id', flat=True))

    if category_ids or author_ids:
        kinship = Q()
        if category_ids:
            kinship |= Q(categories__id__in=category_ids)
        if author_ids:
            kinship |= Q(authors__id__in=author_ids)

        neighbours = (
            _books().filter(kinship, is_active=True)
            .exclude(pk__in=taken)
            .annotate(likes_total=Count('likes', distinct=True))
            .order_by('-likes_total', '-created_at')
            .distinct()[: limit - len(result)]
        )
        result.extend(neighbours)
        taken |= {item.id for item in result}

    if len(result) < limit:
        result.extend(
            _popular_books(taken, limit - len(result), language=book.language)
        )

    return result[:limit]


def recommend_for_user(user, limit=DEFAULT_LIMIT, language=None):
    """
    Персональная подборка «по вашему вкусу».

    Ищем людей с пересекающимся вкусом и смотрим, что читают они.
    Новому пользователю показываем популярное — рекомендовать пока не из чего.
    """
    taste = _taste_book_ids(user)

    if not taste:
        return {
            'basis': 'popular',
            'books': _popular_books(set(), limit, language=language),
        }

    peers = _readers_of(taste)
    peers.discard(user.id)

    scores = _co_occurrence_scores(peers, taste)
    ranked_ids = [
        book_id for book_id, _ in
        sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    ]

    books = _ordered_books(ranked_ids)
    if language:
        books = [book for book in books if book.language == language]
    books = books[:limit]

    basis = 'collaborative' if books else 'taste'

    if len(books) < limit:
        # Никто пока не пересёкся по вкусу — идём от жанров и авторов,
        # которые пользователь уже выбирал.
        taken = taste | {item.id for item in books}
        category_ids = list(
            Book.objects.filter(pk__in=taste).values_list('categories__id', flat=True)
        )
        author_ids = list(
            Book.objects.filter(pk__in=taste).values_list('authors__id', flat=True)
        )
        category_ids = [value for value in category_ids if value is not None]
        author_ids = [value for value in author_ids if value is not None]

        if category_ids or author_ids:
            kinship = Q()
            if category_ids:
                kinship |= Q(categories__id__in=category_ids)
            if author_ids:
                kinship |= Q(authors__id__in=author_ids)

            queryset = _books().filter(kinship, is_active=True).exclude(pk__in=taken)
            if language:
                queryset = queryset.filter(language=language)

            books.extend(
                queryset.annotate(likes_total=Count('likes', distinct=True))
                .order_by('-likes_total', '-created_at')
                .distinct()[: limit - len(books)]
            )

    if len(books) < limit:
        taken = taste | {item.id for item in books}
        books.extend(_popular_books(taken, limit - len(books), language=language))
        if basis == 'taste':
            basis = 'mixed'

    return {'basis': basis, 'books': books[:limit]}
