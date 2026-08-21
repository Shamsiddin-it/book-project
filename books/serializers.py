from rest_framework import serializers

from shelf.models import ShelfItem
from social.models import Like

from .models import Author, Book, BookAuthor, Category, Character, Edition, MoodboardImage


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'subcategory_of', 'subcategories']

    def get_subcategories(self, obj):
        return [{'id': c.id, 'name': c.name} for c in obj.subcategories.all()]


class AuthorBriefSerializer(serializers.ModelSerializer):
    """Для вложения в карточку книги. Без books_amount — иначе получаем запрос на автора."""

    class Meta:
        model = Author
        fields = ['id', 'name', 'image']


class AuthorSerializer(serializers.ModelSerializer):
    # Значение приходит из annotate() во вьюхе, в модели такого поля нет.
    books_amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'name', 'description', 'image', 'books_amount']


class EditionSerializer(serializers.ModelSerializer):
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    is_physical = serializers.BooleanField(read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Edition
        fields = [
            'id', 'book', 'format', 'format_display', 'cover', 'isbn', 'publisher',
            'published_year', 'pages', 'price', 'old_price', 'is_on_sale',
            'discount_percent', 'is_physical', 'is_active', 'audio_link',
        ]

    def validate(self, data):
        old_price = data.get('old_price', getattr(self.instance, 'old_price', None))
        price = data.get('price', getattr(self.instance, 'price', None))

        if old_price is not None and price is not None and old_price <= price:
            raise serializers.ValidationError(
                {'old_price': 'Цена до скидки должна быть больше текущей.'}
            )
        return data
        # Сам файл книги не отдаём в каталоге — доступ к нему выдаёт ридер,
        # только владельцу издания.


class MoodboardImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodboardImage
        fields = ['id', 'book', 'image', 'position']


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ['id', 'book', 'name', 'image', 'signature_quote', 'is_main']


class BookAuthorSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), source='author', write_only=True
    )

    class Meta:
        model = BookAuthor
        fields = ['id', 'book', 'author', 'author_id']


class _UserFlagsMixin(serializers.ModelSerializer):
    """Общие поля is_liked / is_read, чтобы не дублировать логику в двух сериализаторах."""

    is_liked = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()

    def _user(self):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return user if user is not None and user.is_authenticated else None

    def get_is_liked(self, obj):
        user = self._user()
        if user is None:
            return False
        # liked_book_ids кладёт во view одним запросом — иначе получаем N+1.
        liked_ids = self.context.get('liked_book_ids')
        if liked_ids is not None:
            return obj.id in liked_ids
        return Like.objects.filter(user=user, book=obj).exists()

    def get_is_read(self, obj):
        user = self._user()
        if user is None:
            return False
        read_ids = self.context.get('read_book_ids')
        if read_ids is not None:
            return obj.id in read_ids
        return ShelfItem.objects.filter(
            user=user, edition__book=obj, status=ShelfItem.Status.READ
        ).exists()


class BookListSerializer(_UserFlagsMixin):
    """Облегчённый вид для каталога: без мудборда и героев."""

    authors = AuthorBriefSerializer(many=True, read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    cover = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    # Приходят из annotate() во вьюхе: полей с такими именами в модели нет.
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    sale = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'language', 'language_display', 'authors',
            'accent_color', 'cover', 'min_price', 'sale',
            'average_rating', 'reviews_count', 'is_liked', 'is_read',
        ]

    def get_sale(self, obj):
        """Лучшее предложение по книге — для плашки со скидкой на карточке."""
        discounted = [
            edition for edition in obj.editions.all()
            if edition.is_active and edition.is_on_sale
        ]
        if not discounted:
            return None

        best = max(discounted, key=lambda edition: edition.discount_percent)
        return {
            'old_price': best.old_price,
            'price': best.price,
            'discount_percent': best.discount_percent,
        }

    def get_cover(self, obj):
        edition = next((e for e in obj.editions.all() if e.is_active), None)
        if edition is None or not edition.cover:
            return None
        request = self.context.get('request')
        url = edition.cover.url
        return request.build_absolute_uri(url) if request else url

    def get_min_price(self, obj):
        prices = [e.price for e in obj.editions.all() if e.is_active]
        return min(prices) if prices else None


class BookDetailSerializer(_UserFlagsMixin):
    """Полная страница книги: издания, мудборд, герои."""

    authors = AuthorBriefSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    editions = EditionSerializer(many=True, read_only=True)
    moodboard = MoodboardImageSerializer(many=True, read_only=True)
    characters = CharacterSerializer(many=True, read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'description', 'language', 'language_display',
            'authors', 'categories', 'publishing_year', 'accent_color',
            'editions', 'moodboard', 'characters',
            'average_rating', 'reviews_count',
            'is_active', 'created_at', 'is_liked', 'is_read',
        ]


class BookWriteSerializer(serializers.ModelSerializer):
    """Отдельный сериализатор на запись — вложенные поля тут не нужны."""

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'description', 'language', 'categories',
            'publishing_year', 'accent_color', 'is_active',
        ]
