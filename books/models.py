from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/')
    subcategory_of = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
    )

    def __str__(self):
        return self.name


class Book(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    authors = models.ManyToManyField('Author', through='BookAuthor', related_name='books')
    language = models.CharField(max_length=50)
    categories = models.ManyToManyField(Category, related_name="books")

    COVER_CHOICES = (
        ('soft', 'Soft Cover'),
        ('hard', 'Hard Cover'),
    )
    
    cover = models.CharField(choices=COVER_CHOICES, max_length=50)
    isbn = models.CharField(max_length=20, unique=True)
    pages = models.PositiveIntegerField()
    publishing_year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_physical = models.BooleanField(default=True)  # 🔥 можно ли купить физически
    file = models.FileField(upload_to="book_files/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_link = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.name


class BookImage(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="book_images/")

    def __str__(self):
        return f"Обложка для: {self.book}"

class Author(models.Model):
    name = models.CharField( max_length=70)
    description = models.TextField()
    books_amount = models.IntegerField()
    image = models.ImageField(upload_to='authors_photo/', null=True, blank=True)

    def __str__(self):
        return self.name
    
class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.book.name} — {self.author}"