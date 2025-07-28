from rest_framework import viewsets, permissions
from .models import Category, Book, Edition, BookImage
from .serializers import (
    CategorySerializer,
    BookSerializer,
    EditionSerializer,
    BookImageSerializer
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class EditionViewSet(viewsets.ModelViewSet):
    queryset = Edition.objects.all()
    serializer_class = EditionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class BookImageViewSet(viewsets.ModelViewSet):
    queryset = BookImage.objects.all()
    serializer_class = BookImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
