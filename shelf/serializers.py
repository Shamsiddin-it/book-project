from django.utils import timezone
from rest_framework import serializers

from books.models import Edition
from books.serializers import AuthorBriefSerializer

from .models import ShelfItem


class ShelfEditionSerializer(serializers.ModelSerializer):
    """Издание в том виде, в каком оно нужно на полке."""

    book_id = serializers.IntegerField(source='book.id', read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)
    accent_color = serializers.CharField(source='book.accent_color', read_only=True)
    authors = AuthorBriefSerializer(source='book.authors', many=True, read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)

    class Meta:
        model = Edition
        fields = [
            'id', 'book_id', 'book_name', 'accent_color', 'authors',
            'format', 'format_display', 'cover',
        ]


class ShelfItemSerializer(serializers.ModelSerializer):
    edition = ShelfEditionSerializer(read_only=True)
    edition_id = serializers.PrimaryKeyRelatedField(
        queryset=Edition.objects.filter(is_active=True),
        source='edition',
        write_only=True,
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ShelfItem
        fields = [
            'id', 'edition', 'edition_id', 'status', 'status_display',
            'is_owned', 'progress_percent', 'added_at', 'finished_at',
        ]
        # is_owned выставляется покупкой, а не клиентом — иначе платный
        # контент можно было бы получить обычным PATCH.
        read_only_fields = ['is_owned', 'added_at', 'finished_at']

    def validate_progress_percent(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Прогресс задаётся числом от 0 до 100.')
        return value

    def validate(self, data):
        user = self.context['request'].user
        edition = data.get('edition')
        if edition is not None:
            existing = ShelfItem.objects.filter(user=user, edition=edition)
            if self.instance is not None:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {'edition_id': 'Это издание уже стоит на вашей полке.'}
                )
        return data

    def update(self, instance, validated_data):
        # Отметка «прочитано» проставляет дату и добивает прогресс до 100.
        new_status = validated_data.get('status', instance.status)
        if new_status == ShelfItem.Status.READ and instance.status != ShelfItem.Status.READ:
            validated_data['finished_at'] = timezone.now()
            validated_data.setdefault('progress_percent', 100)
        elif new_status != ShelfItem.Status.READ:
            validated_data['finished_at'] = None
        return super().update(instance, validated_data)
