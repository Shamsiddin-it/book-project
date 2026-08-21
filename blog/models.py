from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PostQuerySet(models.QuerySet):
    def published(self):
        """
        Опубликованные и уже наступившие.

        Проверять только is_published недостаточно: материал можно поставить
        в очередь на будущую дату, и до неё он показываться не должен.
        """
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Post(models.Model):
    """Материал раздела «Blogs & News»."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    cover = models.ImageField(upload_to='blog_covers/', null=True, blank=True)

    excerpt = models.CharField(
        max_length=300, blank=True, help_text='Короткий анонс для карточки в списке.',
    )
    body = models.TextField()

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
    )
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(
        null=True, blank=True, help_text='Момент публикации. Можно поставить будущую дату.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['is_published', '-published_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or 'post'
            slug = base
            suffix = 2
            # Заголовки повторяются — добавляем номер, пока адрес не станет свободным.
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = '{}-{}'.format(base, suffix)
                suffix += 1
            self.slug = slug

        # Публикуем без явной даты — считаем, что прямо сейчас.
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
