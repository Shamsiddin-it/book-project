from django.db import models


class Category(models.Model):
    """Категория книги — жанр, тема и т.д."""
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга как произведение (без привязки к изданию)"""
    name = models.CharField(max_length=150)
    description = models.TextField()
    authors = models.CharField(max_length=250)
    language = models.CharField(max_length=50)
    categories = models.ManyToManyField(Category, related_name="books")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Edition(models.Model):
    """Конкретное издание книги (PDF, EPUB, аудио, физическое)"""
    COVER_CHOICES = (
        ('soft', 'Soft Cover'),
        ('hard', 'Hard Cover'),
    )
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('audio', 'Audio'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="editions")
    cover = models.CharField(choices=COVER_CHOICES, max_length=50)
    format = models.CharField(choices=FORMAT_CHOICES, max_length=20)
    isbn = models.CharField(max_length=20, unique=True)
    pages = models.PositiveIntegerField()
    publishing_year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_physical = models.BooleanField(default=False)  # 🔥 можно ли купить физически
    file = models.FileField(upload_to="edition_files/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.book.name} — {self.cover} ({self.format})"


class BookImage(models.Model):
    """Дополнительные изображения обложки (мудборд, вариации и т.д.)"""
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="edition_covers/")

    def __str__(self):
        return f"Обложка для: {self.edition}"
