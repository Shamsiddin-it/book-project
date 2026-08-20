from rest_framework import serializers

from accounts.serializers import UserBriefSerializer

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = Note
        fields = [
            'id', 'user', 'book', 'kind', 'kind_display', 'text',
            'page', 'is_public', 'has_spoilers', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError('Заметка не может быть пустой.')
        return value
