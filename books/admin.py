from django import forms
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from server.admin_utils import (
    ColorInput,
    ImagePreviewMixin,
    ProtectedFileWidget,
    thumbnail,
)

from .models import Author, Book, BookAuthor, Category, Character, Edition, MoodboardImage


class BookAdminForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'
        widgets = {'accent_color': ColorInput()}


@admin.register(Category)
class CategoryAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ['cover_preview', 'name', 'subcategory_of', 'books_count']
    list_display_links = ['cover_preview', 'name']
    list_filter = ['subcategory_of']
    search_fields = ['name']
    readonly_fields = ['current_image']
    fields = ['name', 'subcategory_of', 'image', 'current_image']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(books_total=Count('books'))

    @admin.display(description='Картинка')
    def cover_preview(self, obj):
        return thumbnail(obj.image, height=48)

    @admin.display(description='Книг', ordering='books_total')
    def books_count(self, obj):
        return obj.books_total


@admin.register(Author)
class AuthorAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_source = 'image'
    list_display = ['photo_preview', 'name', 'books_count']
    list_display_links = ['photo_preview', 'name']
    search_fields = ['name']
    readonly_fields = ['current_image']
    fields = ['name', 'description', 'image', 'current_image']

    def get_queryset(self, request):
        # Счётчик книг считается аннотацией: на модели такого поля нет,
        # а обращение к author.books.count() в списке дало бы запрос на строку.
        return super().get_queryset(request).annotate(books_total=Count('books'))

    @admin.display(description='Фото')
    def photo_preview(self, obj):
        return thumbnail(obj.image, height=48, radius=24)

    @admin.display(description='Книг', ordering='books_total')
    def books_count(self, obj):
        return obj.books_total


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1
    autocomplete_fields = ['author']
    verbose_name = 'Автор'
    verbose_name_plural = 'Авторы'


class EditionAdminForm(forms.ModelForm):
    class Meta:
        model = Edition
        fields = '__all__'
        widgets = {'file': ProtectedFileWidget()}


class EditionInline(admin.StackedInline):
    model = Edition
    form = EditionAdminForm
    extra = 1
    readonly_fields = ['cover_preview', 'discount_hint']
    verbose_name = 'Издание'
    verbose_name_plural = 'Издания — обложка, цена и файл живут здесь'
    fieldsets = [
        (None, {
            'fields': [
                ('format', 'is_active'),
                ('cover', 'cover_preview'),
                ('isbn', 'publisher', 'published_year', 'pages'),
                ('price', 'old_price', 'discount_hint'),
            ],
        }),
        ('Для чтения и прослушивания', {
            'fields': ['file', 'audio_link'],
            'description': (
                'Файл книги попадает в закрытое хранилище — прямой ссылки на него '
                'не существует, он отдаётся только владельцу издания через ридер. '
                'Для аудиокниги вместо файла укажите ссылку.'
            ),
        }),
    ]

    @admin.display(description='Обложка')
    def cover_preview(self, obj):
        return thumbnail(obj.cover, height=140)

    @admin.display(description='Скидка')
    def discount_hint(self, obj):
        if obj is None or not obj.pk:
            return '—'
        if not obj.is_on_sale:
            return format_html(
                '<span style="color:#999">нет — заполните «цену до скидки»</span>'
            )
        return format_html(
            '<strong style="color:#c2185b">−{}%</strong>', obj.discount_percent,
        )


class MoodboardImageInline(admin.TabularInline):
    model = MoodboardImage
    extra = 6  # По ТЗ мудборд состоит из шести изображений.
    max_num = 6
    fields = ['image', 'image_preview', 'position']
    readonly_fields = ['image_preview']
    verbose_name = 'Изображение'
    verbose_name_plural = 'Мудборд — шесть кадров, position задаёт порядок'

    @admin.display(description='Превью')
    def image_preview(self, obj):
        return thumbnail(obj.image, height=90)


class CharacterInline(admin.StackedInline):
    model = Character
    extra = 1
    fields = [('name', 'is_main'), ('image', 'image_preview'), 'signature_quote']
    readonly_fields = ['image_preview']
    verbose_name = 'Герой'
    verbose_name_plural = 'Герои и их фирменные цитаты'

    @admin.display(description='Превью')
    def image_preview(self, obj):
        return thumbnail(obj.image, height=110, radius=55)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookAdminForm
    list_display = [
        'cover_preview', 'name', 'get_authors', 'language',
        'editions_count', 'rating', 'colour_chip', 'is_active',
    ]
    list_display_links = ['cover_preview', 'name']
    list_filter = ['is_active', 'language', 'categories']
    list_editable = ['is_active']
    search_fields = ['name', 'description', 'authors__name']
    filter_horizontal = ['categories']
    inlines = [BookAuthorInline, EditionInline, MoodboardImageInline, CharacterInline]
    save_on_top = True

    fieldsets = [
        (None, {
            'fields': ['name', 'description'],
            'description': 'Описание показывается на странице книги — без спойлеров.',
        }),
        ('Как книгу находят', {
            'fields': [('language', 'publishing_year'), 'categories', 'is_active'],
        }),
        ('Оформление страницы', {
            'fields': ['accent_color'],
            'description': (
                'Цвет заливает шапку страницы книги и подложку карточки в каталоге. '
                'Берите тёмный оттенок с обложки — текст поверх белый.'
            ),
        }),
    ]

    def get_queryset(self, request):
        # Без этого список книг делает запрос на авторов и издания для каждой строки.
        return (
            super()
            .get_queryset(request)
            .prefetch_related('authors', 'editions')
            .annotate(reviews_total=Count('reviews', distinct=True))
        )

    @admin.display(description='Обложка')
    def cover_preview(self, obj):
        edition = next((item for item in obj.editions.all() if item.cover), None)
        return thumbnail(edition.cover if edition else None, height=70)

    @admin.display(description='Авторы')
    def get_authors(self, obj):
        return ', '.join(author.name for author in obj.authors.all()) or '—'

    @admin.display(description='Изданий')
    def editions_count(self, obj):
        total = len(obj.editions.all())
        if total == 0:
            # Книга без изданий не покупается и не имеет цены — это стоит заметить сразу.
            return format_html('<span style="color:#c00">нет изданий</span>')
        return total

    @admin.display(description='Отзывов', ordering='reviews_total')
    def rating(self, obj):
        return obj.reviews_total

    @admin.display(description='Цвет')
    def colour_chip(self, obj):
        if not obj.accent_color:
            return '—'
        return format_html(
            '<span style="display:inline-block;width:22px;height:22px;border-radius:4px;'
            'border:1px solid #999;background:{}" title="{}"></span>',
            obj.accent_color,
            obj.accent_color,
        )


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    form = EditionAdminForm
    list_display = [
        'cover_preview', 'book', 'format', 'price', 'old_price',
        'sale_badge', 'has_file', 'is_active',
    ]
    list_display_links = ['cover_preview', 'book']
    list_filter = ['format', 'is_active', 'book__language']
    list_editable = ['is_active']
    search_fields = ['book__name', 'isbn', 'publisher']
    autocomplete_fields = ['book']
    readonly_fields = ['cover_preview_large']

    fieldsets = [
        (None, {'fields': ['book', ('format', 'is_active')]}),
        ('Обложка', {'fields': [('cover', 'cover_preview_large')]}),
        ('Выходные данные', {'fields': [('isbn', 'publisher'), ('published_year', 'pages')]}),
        ('Цена', {
            'fields': [('price', 'old_price')],
            'description': 'Цена до скидки должна быть больше текущей, иначе форма не сохранится.',
        }),
        ('Содержимое', {'fields': ['file', 'audio_link']}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book')

    @admin.display(description='Обложка')
    def cover_preview(self, obj):
        return thumbnail(obj.cover, height=60)

    @admin.display(description='Текущая обложка')
    def cover_preview_large(self, obj):
        return thumbnail(obj.cover, height=200)

    @admin.display(description='Скидка')
    def sale_badge(self, obj):
        if not obj.is_on_sale:
            return '—'
        return format_html('<strong style="color:#c2185b">−{}%</strong>', obj.discount_percent)

    @admin.display(description='Файл', boolean=True)
    def has_file(self, obj):
        return bool(obj.file) or bool(obj.audio_link)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'book', 'is_main']
    list_display_links = ['image_preview', 'name']
    list_filter = ['is_main']
    list_editable = ['is_main']
    search_fields = ['name', 'book__name']
    autocomplete_fields = ['book']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book')

    @admin.display(description='Портрет')
    def image_preview(self, obj):
        return thumbnail(obj.image, height=52, radius=26)


@admin.register(MoodboardImage)
class MoodboardImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'book', 'position']
    list_display_links = ['image_preview', 'book']
    list_editable = ['position']
    search_fields = ['book__name']
    autocomplete_fields = ['book']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book')

    @admin.display(description='Кадр')
    def image_preview(self, obj):
        return thumbnail(obj.image, height=64)
