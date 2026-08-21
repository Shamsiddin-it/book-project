from rest_framework import viewsets
from rest_framework.generics import ListAPIView

from server.permissions import IsAdminOrReadOnly

from .models import Post, Tag
from .serializers import (
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
    TagSerializer,
)


class PostViewSet(viewsets.ModelViewSet):
    """
    Материалы раздела «Blogs & News»: /api/blog/posts/

    Адресуются по slug, а не по id: так ссылки читаемы и переживают
    перенос базы.
    """

    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filterset_fields = ['tags__slug']
    search_fields = ['title', 'excerpt', 'body']
    ordering_fields = ['published_at', 'title']

    def get_queryset(self):
        queryset = Post.objects.select_related('author').prefetch_related('tags')

        # Черновики и отложенные публикации видит только персонал —
        # иначе материал утечёт раньше запланированной даты.
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.published()

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PostWriteSerializer
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagListView(ListAPIView):
    """Теги материалов: /api/blog/tags/"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None
