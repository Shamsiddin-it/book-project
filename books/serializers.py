from rest_framework import serializers
from .models import (
    Category, Author, Book, BookAuthor,
    BookImage
)


class CategorySerializer(serializers.ModelSerializer):
    subcategory_of = Category.subcategory_of
    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'subcategory_of']


class AuthorSerializer(serializers.ModelSerializer):
    books_amount = Author.books_amount
    class Meta:
        model = Author
        fields = ['id', 'name', 'description', 'books_amount', 'image']


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookImage
        fields = ['id', 'image', 'book']


class BookAuthorSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        source='author',
        write_only=True
    )

    class Meta:
        model = BookAuthor
        fields = ['id', 'book', 'author', 'author_id']
        extra_kwargs = {
            'book': {'read_only': True},
        }


class BookSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    imges = BookImageSerializer(source='images', many=True, read_only = True)
    publishing_year = Book.publishing_year
    audio_link = Book.audio_link
    class Meta:
        model = Book
        fields = [
            'id', 'name', 'description', 'language',
            'categories', 'authors', 'imges', 'cover', 'isbn', 'pages', 
            'publishing_year', 'price', 'file', 'audio_link'
        ]
