from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Note
from .serializers import NoteSerializer

User = get_user_model()


class MyNotesViewSet(viewsets.ModelViewSet):
    """Свои заметки и цитаты: /api/notes/"""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['book', 'kind', 'is_public']
    search_fields = ['text']
    ordering_fields = ['created_at', 'page']

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).select_related('user', 'book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicNotesView(ListAPIView):
    """
    Публичные заметки пользователя: /api/notes/users/<id>/
    Приватные заметки не отдаются никому, кроме самого автора.
    """

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['book', 'kind']

    def get_queryset(self):
        owner = get_object_or_404(User, pk=self.kwargs['pk'])
        is_self = owner == self.request.user

        if not owner.is_shelf_public and not is_self:
            raise PermissionDenied('Этот пользователь закрыл свою книжную полку.')

        queryset = Note.objects.filter(user=owner).select_related('user', 'book')
        if not is_self:
            queryset = queryset.filter(is_public=True)
        return queryset


class BookNotesView(ListAPIView):
    """Публичные цитаты и заметки по конкретной книге: /api/notes/books/<id>/"""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['kind']

    def get_queryset(self):
        return (
            Note.objects.filter(book_id=self.kwargs['pk'], is_public=True, user__is_shelf_public=True)
            .select_related('user', 'book')
        )
