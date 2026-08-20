from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    CUSTOMER = 'customer', 'Customer'


def user_photo_upload_path(instance, filename):
    return f'users/{instance.username}/profile/{filename}'


class User(AbstractUser):
    """
    Профиль пользователя хранится прямо здесь.
    Отдельная модель Profile была убрана: она дублировала лайки и полку,
    которые теперь живут в social.Like и shelf.ShelfItem.
    """

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to=user_photo_upload_path, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, help_text='О себе — видно другим пользователям.')
    is_shelf_public = models.BooleanField(
        default=True,
        help_text='Могут ли другие пользователи просматривать книжную полку.',
    )

    def __str__(self):
        return f'{self.username} ({self.role})'
