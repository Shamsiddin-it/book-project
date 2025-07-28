from rest_framework import serializers
from .models import Category, Book, Edition, BookImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookImage
        fields = ['id', 'image']


class EditionSerializer(serializers.ModelSerializer):
    images = BookImageSerializer(many=True, read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)

    class Meta:
        model = Edition
        fields = [
            'id', 'book', 'book_name', 'cover', 'format', 'isbn', 'pages',
            'publishing_year', 'price', 'is_active', 'is_physical', 'file',
            'images', 'created_at'
        ]


class BookSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    editions = EditionSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'description', 'authors', 'language',
            'categories', 'editions', 'created_at'
        ]
