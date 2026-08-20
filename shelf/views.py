from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import ShelfItem
from .serializers import ShelfItemSerializer

User = get_user_model()


def shelf_queryset():
    return ShelfItem.objects.select_related('edition', 'edition__book').prefetch_related(
        'edition__book__authors'
    )


class MyShelfViewSet(viewsets.ModelViewSet):
    """
    Своя книжная полка: /api/shelf/
    Заводится сама — отдельного создания полки не требуется, элементы просто добавляются.
    """

    serializer_class = ShelfItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'is_owned']
    ordering_fields = ['added_at', 'finished_at']

    def get_queryset(self):
        # Фильтр по пользователю здесь же — так чужой элемент нельзя достать даже по прямому id.
        return shelf_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicShelfView(ListAPIView):
    """Чужая полка: /api/shelf/users/<id>/ — если владелец её не закрыл."""

    serializer_class = ShelfItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['status']

    def get_queryset(self):
        owner = get_object_or_404(User, pk=self.kwargs['pk'])

        if not owner.is_shelf_public and owner != self.request.user:
            raise PermissionDenied('Этот пользователь закрыл свою книжную полку.')

        return shelf_queryset().filter(user=owner)
