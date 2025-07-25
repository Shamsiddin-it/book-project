from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    # PROVIDER = 'provider', 'Service Provider'
    CUSTOMER = 'customer', 'Customer'

def user_photo_upload_path(instance, filename):
    return f'users/{instance.username}/profile/{filename}'

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True, null=True)
    # address = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to=user_photo_upload_path, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    # telegram = models.URLField(blank=True, null=True)
    # instagram = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
