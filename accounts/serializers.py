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


class PublicUserSerializer(serializers.ModelSerializer):
    """Как пользователя видят другие пользователи."""

    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'photo', 'bio',
            'followers_count', 'following_count', 'is_shelf_public',
        ]


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
