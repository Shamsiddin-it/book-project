from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from server.storages import protected_storage


class Language(models.TextChoices):
    """Языки, на которых доступны книги. Используется для фильтрации библиотеки."""

    RUSSIAN = 'ru', 'Русский'
    ENGLISH = 'en', 'English'
    UZBEK = 'uz', "O'zbekcha"
    FRENCH = 'fr', 'Français'
    GERMAN = 'de', 'Deutsch'
    SPANISH = 'es', 'Español'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    subcategory_of = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
    )

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=70)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='authors_photo/', null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """
    Произведение как таковое, без привязки к конкретному изданию.
    Обложки, цены и ISBN живут в Edition — у одного произведения их может быть несколько.
    """

    name = models.CharField(max_length=150)
    description = models.TextField(help_text='Краткое описание без спойлеров.')
    language = models.CharField(max_length=5, choices=Language.choices, default=Language.RUSSIAN)
    authors = models.ManyToManyField('Author', through='BookAuthor', related_name='books')
    categories = models.ManyToManyField(Category, related_name='books', blank=True)
    publishing_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2100)],
        help_text='Год первой публикации произведения.',
    )
    accent_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[RegexValidator(r'^#[0-9a-fA-F]{6}$', 'Ожидается HEX-цвет, например #1A2B3C.')],
        help_text='Цвет фона страницы книги, подобранный под обложку. Формат #RRGGBB.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['book', 'author'], name='unique_book_author'),
        ]

    def __str__(self):
        return f'{self.book.name} — {self.author.name}'


class Edition(models.Model):
    """
    Конкретное издание книги: своя обложка, свой ISBN, своя цена.
    Пользователь выбирает то издание, которое ему ближе.
    """

    class Format(models.TextChoices):
        SOFT = 'soft', 'Мягкая обложка'
        HARD = 'hard', 'Твёрдая обложка'
        EBOOK = 'ebook', 'Электронная книга'
        AUDIO = 'audio', 'Аудиокнига'

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='editions')
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.SOFT)
    cover = models.ImageField(upload_to='book_covers/')
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=120, blank=True)
    published_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2100)],
        help_text='Год выпуска именно этого издания.',
    )
    pages = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    # Файлы для чтения и прослушивания внутри сайта.
    # Приватное хранилище: прямой ссылки на файл не существует, выдачей
    # занимается ридер после проверки, что издание куплено.
    file = models.FileField(
        upload_to='book_files/', null=True, blank=True, storage=protected_storage,
    )
    audio_link = models.URLField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['book', 'format']

    def __str__(self):
        return f'{self.book.name} ({self.get_format_display()})'

    @property
    def is_physical(self):
        return self.format in (self.Format.SOFT, self.Format.HARD)


class MoodboardImage(models.Model):
    """Мудборд по сюжету книги — по ТЗ шесть изображений на книгу."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='moodboard')
    image = models.ImageField(upload_to='moodboards/')
    position = models.PositiveSmallIntegerField(default=0, help_text='Порядок вывода в сетке.')

    class Meta:
        ordering = ['position', 'id']

    def __str__(self):
        return f'Мудборд: {self.book.name} #{self.position}'


class Character(models.Model):
    """Визуализация героя книги и его фирменная цитата."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=120)
    image = models.ImageField(upload_to='characters/', null=True, blank=True)
    signature_quote = models.TextField(blank=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_main', 'name']

    def __str__(self):
        return f'{self.name} — {self.book.name}'
