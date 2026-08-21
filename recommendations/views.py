from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from books.serializers import BookListSerializer
from shelf.models import ShelfItem
from social.models import Like

from .engine import DEFAULT_LIMIT, recommend_for_user, similar_to_book

MAX_LIMIT = 50


def _limit_from(request):
    try:
        limit = int(request.query_params.get('limit', DEFAULT_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(limit, MAX_LIMIT))


def _serializer_context(request):
    """
    Те же множества, что и в каталоге: без них is_liked / is_read
    дадут по запросу на каждую книгу подборки.
    """
    context = {'request': request}
    user = request.user
    if user.is_authenticated:
        context['liked_book_ids'] = set(
            Like.objects.filter(user=user).values_list('book_id', flat=True)
        )
        context['read_book_ids'] = set(
            ShelfItem.objects.filter(user=user, status=ShelfItem.Status.READ)
            .values_list('edition__book_id', flat=True)
        )
    return context


class SimilarBooksView(APIView):
    """
    GET /api/recommendations/similar/<book_id>/

    «Если вам понравилась эта книга, прочтите…»
    Доступно и анонимам — это часть страницы книги.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk, is_active=True)
        books = similar_to_book(book, limit=_limit_from(request), user=request.user)

        serializer = BookListSerializer(
            books, many=True, context=_serializer_context(request),
        )
        return Response({
            'book_id': book.id,
            'count': len(books),
            'results': serializer.data,
        })


class PersonalRecommendationsView(APIView):
    """
    GET /api/recommendations/

    Подборка по вкусу. Поле basis говорит, на чём она построена:
    collaborative — по людям с похожим вкусом,
    taste — по жанрам и авторам, которые пользователь уже выбирал,
    popular — пользователь новый, показываем популярное,
    mixed — не хватило совпадений, добрали популярным.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        language = request.query_params.get('language') or None
        result = recommend_for_user(
            request.user, limit=_limit_from(request), language=language,
        )

        serializer = BookListSerializer(
            result['books'], many=True, context=_serializer_context(request),
        )
        return Response({
            'basis': result['basis'],
            'count': len(result['books']),
            'results': serializer.data,
        })
