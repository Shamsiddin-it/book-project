from rest_framework import serializers

from accounts.serializers import UserBriefSerializer

from .models import Comment, Follow, Like


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'book', 'created_at']
        read_only_fields = ['created_at']


class FollowSerializer(serializers.ModelSerializer):
    follower = UserBriefSerializer(read_only=True)
    following = UserBriefSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """Комментарий с автором, счётчиком лайков и вложенными ответами."""

    user = UserBriefSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'book', 'character', 'parent', 'text',
            'has_spoilers', 'likes_count', 'is_liked', 'replies',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        liked_ids = self.context.get('liked_comment_ids')
        if liked_ids is None:
            return False
        return obj.id in liked_ids

    def get_replies(self, obj):
        # Ответы отдаём только на верхнем уровне, иначе дерево уходит вглубь
        # и вьюха начинает тянуть неограниченное число уровней.
        if obj.parent_id is not None:
            return []
        replies = getattr(obj, 'prefetched_replies', None)
        if replies is None:
            replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def validate(self, data):
        parent = data.get('parent')
        book = data.get('book') or getattr(self.instance, 'book', None)

        if parent is not None:
            if parent.book_id != getattr(book, 'id', book):
                raise serializers.ValidationError(
                    {'parent': 'Ответ должен относиться к той же книге, что и исходный комментарий.'}
                )
            if parent.parent_id is not None:
                raise serializers.ValidationError(
                    {'parent': 'Отвечать можно только на комментарий верхнего уровня.'}
                )

        character = data.get('character')
        if character is not None and book is not None:
            if character.book_id != getattr(book, 'id', book):
                raise serializers.ValidationError(
                    {'character': 'Этот герой относится к другой книге.'}
                )
        return data
