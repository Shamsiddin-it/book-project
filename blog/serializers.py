from rest_framework import serializers

from accounts.serializers import UserBriefSerializer

from .models import Post, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class PostListSerializer(serializers.ModelSerializer):
    """Карточка в списке — без тела материала, оно тут ни к чему."""

    author = UserBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'cover', 'excerpt', 'author', 'tags', 'published_at']


class PostDetailSerializer(serializers.ModelSerializer):
    author = UserBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover', 'excerpt', 'body',
            'author', 'tags', 'is_published', 'published_at',
            'created_at', 'updated_at',
        ]


class PostWriteSerializer(serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, required=False,
    )

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover', 'excerpt', 'body',
            'tag_ids', 'is_published', 'published_at',
        ]
        # slug генерируется из заголовка, но задать свой тоже можно.
        extra_kwargs = {'slug': {'required': False}}
