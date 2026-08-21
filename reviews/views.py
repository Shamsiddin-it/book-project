from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from server.permissions import IsOwnerOrReadOnly

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Отзывы: /api/reviews/

    Читают все, пишет автор только свой. Персонал может удалить чужой —
    для модерации.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_fields = ['book', 'rating', 'has_spoilers']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        return Review.objects.select_related('user', 'book').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookReviewsView(ListAPIView):
    """Отзывы на конкретную книгу: /api/reviews/books/<id>/"""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return (
            Review.objects.filter(book_id=self.kwargs['pk'])
            .select_related('user')
            .order_by('-created_at')
        )


class BookRatingSummaryView(APIView):
    """
    Сводка оценок: /api/reviews/books/<id>/summary/

    Отдаёт средний балл, количество и разбивку по звёздам — этого хватает,
    чтобы нарисовать блок рейтинга, не выкачивая все отзывы.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        aggregate = book.reviews.aggregate(
            average=Avg('rating'), total=Count('id'),
        )
        distribution = {
            row['rating']: row['count']
            for row in book.reviews.values('rating').annotate(count=Count('id'))
        }

        average = aggregate['average']
        if average is not None:
            # Именно ROUND_HALF_UP, а не round(): встроенное округление
            # банковское и превращает 4.25 в 4.2, чего читатель не ожидает.
            average = float(
                Decimal(str(average)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            )

        return Response({
            'book_id': book.id,
            'average_rating': average,
            'reviews_count': aggregate['total'],
            'distribution': {str(star): distribution.get(star, 0) for star in range(1, 6)},
        })
