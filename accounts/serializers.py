from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        # role сюда сознательно не входит: иначе любой желающий зарегистрировался бы админом.
        fields = ['id', 'username', 'email', 'phone', 'birthdate', 'password', 'password2']

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Пароли не совпадают.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserBriefSerializer(serializers.ModelSerializer):
    """
    Для вложения в комментарии, заметки и полку.
    Без счётчиков подписок — иначе получаем два запроса на каждого автора.
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'photo']


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Профиль пользователя. Счётчики приходят из annotate() во вьюхе,
    полей с такими именами в модели нет.
    """

    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'photo', 'bio',
            'followers_count', 'following_count', 'is_following', 'is_shelf_public',
        ]

    def get_is_following(self, obj):
        """
        Подписан ли на этого человека тот, кто смотрит.

        Без этого поля кнопка «Подписаться» при загрузке страницы не знает
        своего состояния и показывает неверную надпись.

        В списках вьюха кладёт в контекст готовое множество id — иначе
        получаем запрос на каждого пользователя в выдаче.
        """
        request = self.context.get('request')
        viewer = getattr(request, 'user', None)
        if viewer is None or not viewer.is_authenticated or viewer.pk == obj.pk:
            return False

        followed_ids = self.context.get('followed_ids')
        if followed_ids is not None:
            return obj.pk in followed_ids

        return viewer.following.filter(following=obj).exists()


class MeSerializer(serializers.ModelSerializer):
    """Собственный профиль: видно больше, редактировать можно только своё."""

    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'photo', 'birthdate', 'bio', 'role', 'is_shelf_public',
            'followers_count', 'following_count', 'date_joined',
        ]
        read_only_fields = ['id', 'username', 'role', 'date_joined']
