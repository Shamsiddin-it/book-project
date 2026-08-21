from rest_framework import serializers

from accounts.serializers import UserBriefSerializer

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'book', 'rating', 'text',
            'has_spoilers', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Оценка ставится от 1 до 5.')
        return value

    def validate(self, data):
        # Уникальность на уровне БД есть, но без этой проверки клиент получил бы
        # 500 вместо внятной ошибки формы.
        request = self.context['request']
        book = data.get('book') or getattr(self.instance, 'book', None)

        if book is not None and self.instance is None:
            if Review.objects.filter(user=request.user, book=book).exists():
                raise serializers.ValidationError(
                    {'book': 'Вы уже оценили эту книгу — измените существующий отзыв.'}
                )
        return data
