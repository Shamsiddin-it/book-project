from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import PublicUserSerializer
from server.permissions import IsOwnerOrReadOnly

from .models import Comment, CommentLike, Follow
from .serializers import CommentSerializer

User = get_user_model()


def _users_with_counts():
    """PublicUserSerializer ждёт счётчики из аннотации — в модели таких полей нет."""
    return User.objects.annotate(
        followers_count=Count('followers', distinct=True),
        following_count=Count('following', distinct=True),
    )


class CommentViewSet(viewsets.ModelViewSet):
    """
    Обсуждение книг. Список отдаёт только верхний уровень —
    ответы приезжают вложенными в поле replies.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_fields = ['book', 'character', 'has_spoilers']
    ordering_fields = ['created_at', 'likes_count']

    def get_queryset(self):
        replies = (
            Comment.objects.select_related('user')
            .annotate(likes_count=Count('likes', distinct=True))
            .order_by('created_at')
        )
        queryset = (
            Comment.objects.select_related('user', 'book', 'character')
            .annotate(likes_count=Count('likes', distinct=True))
            .prefetch_related(Prefetch('replies', queryset=replies, to_attr='prefetched_replies'))
        )
        if self.action == 'list':
            queryset = queryset.filter(parent__isnull=True)
        return queryset.order_by('created_at')

    def get_serializer_context(self):
        """Один запрос на лайки комментариев вместо запроса на каждый комментарий."""
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['liked_comment_ids'] = set(
                CommentLike.objects.filter(user=user).values_list('comment_id', flat=True)
            )
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_like(self, request, pk=None):
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            like.delete()
        return Response({'liked': created, 'likes_count': comment.likes.count()})


class ToggleFollowView(APIView):
    """POST /api/social/users/<id>/follow/ — подписаться или отписаться."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)

        if target == request.user:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if not created:
            follow.delete()

        return Response({
            'following': created,
            'followers_count': target.followers.count(),
        })


class FollowersView(ListAPIView):
    """Кто подписан на пользователя."""

    serializer_class = PublicUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        target = get_object_or_404(User, pk=self.kwargs['pk'])
        return _users_with_counts().filter(following__following=target).order_by('username')


class FollowingView(ListAPIView):
    """На кого подписан пользователь."""

    serializer_class = PublicUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        target = get_object_or_404(User, pk=self.kwargs['pk'])
        return _users_with_counts().filter(followers__follower=target).order_by('username')
