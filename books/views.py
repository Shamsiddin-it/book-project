from django.db.models import Count, Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shelf.models import ShelfItem
from social.models import Like

from .models import Author, Book, BookAuthor, Category, Character, Edition, MoodboardImage
from .permissions import IsAdminOrReadOnly
from .serializers import (
    AuthorSerializer,
    BookAuthorSerializer,
    BookDetailSerializer,
    BookListSerializer,
    BookWriteSerializer,
    CategorySerializer,
    CharacterSerializer,
    EditionSerializer,
    MoodboardImageSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('subcategories')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['subcategory_of']
    search_fields = ['name']


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.annotate(books_amount=Count('books', distinct=True)).order_by('name')
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    search_fields = ['name']


class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['language', 'categories', 'authors', 'is_active']
    search_fields = ['name', 'description', 'authors__name']
    ordering_fields = ['created_at', 'name', 'publishing_year']

    def get_queryset(self):
        active_editions = Edition.objects.filter(is_active=True)
        queryset = Book.objects.prefetch_related(
            'authors',
            Prefetch('editions', queryset=active_editions),
        )
        if self.action == 'retrieve':
            # Каталогу это не нужно — лишние запросы на каждую страницу выдачи.
            queryset = queryset.prefetch_related(
                'categories', 'categories__subcategories', 'moodboard', 'characters',
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BookWriteSerializer
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookListSerializer

    def get_serializer_context(self):
        """
        Один запрос на лайки и один на полку вместо запроса на каждую книгу.
        Сериализатор читает эти множества через контекст.
        """
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['liked_book_ids'] = set(
                Like.objects.filter(user=user).values_list('book_id', flat=True)
            )
            context['read_book_ids'] = set(
                ShelfItem.objects.filter(user=user, status=ShelfItem.Status.READ)
                .values_list('edition__book_id', flat=True)
            )
        return context

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_like(self, request, pk=None):
        book = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, book=book)
        if not created:
            like.delete()
        return Response({
            'liked': created,
            'likes_count': book.likes.count(),
        })


class EditionViewSet(viewsets.ModelViewSet):
    queryset = Edition.objects.select_related('book')
    serializer_class = EditionSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['book', 'format', 'is_active']


class MoodboardImageViewSet(viewsets.ModelViewSet):
    queryset = MoodboardImage.objects.select_related('book')
    serializer_class = MoodboardImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['book']


class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.select_related('book')
    serializer_class = CharacterSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['book', 'is_main']


class BookAuthorViewSet(viewsets.ModelViewSet):
    queryset = BookAuthor.objects.select_related('book', 'author')
    serializer_class = BookAuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['book', 'author']
