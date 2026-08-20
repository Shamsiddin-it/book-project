from rest_framework import serializers

from books.serializers import AuthorBriefSerializer
from shelf.models import ShelfItem


class ReaderManifestSerializer(serializers.Serializer):
    """
    Всё, что нужно ридеру на старте: что открываем, чем открывать
    и на каком месте пользователь остановился в прошлый раз.
    """

    edition_id = serializers.IntegerField()
    book_id = serializers.IntegerField()
    book_name = serializers.CharField()
    authors = AuthorBriefSerializer(many=True)
    accent_color = serializers.CharField()
    language = serializers.CharField()

    format = serializers.CharField()
    format_display = serializers.CharField()
    is_audio = serializers.BooleanField()

    content_url = serializers.CharField(allow_null=True)
    audio_link = serializers.CharField(allow_null=True)
    content_type = serializers.CharField(allow_null=True)
    size_bytes = serializers.IntegerField(allow_null=True)

    progress_percent = serializers.IntegerField()
    position = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    last_read_at = serializers.DateTimeField(allow_null=True)


class ReadingProgressSerializer(serializers.ModelSerializer):
    """Сохранение места, на котором остановился читатель."""

    class Meta:
        model = ShelfItem
        fields = ['progress_percent', 'position', 'status', 'last_read_at', 'finished_at']
        read_only_fields = ['status', 'last_read_at', 'finished_at']

    def validate_progress_percent(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Прогресс задаётся числом от 0 до 100.')
        return value
