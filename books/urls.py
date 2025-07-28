from django.urls import path
from .views import (
    CategoryViewSet,
    BookViewSet,
    EditionViewSet,
    BookImageViewSet,
)

# Используем .as_view({'method': 'action'}) вручную
urlpatterns = [
    # Category
    path('categories/', CategoryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('categories/<int:pk>/', CategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # Book
    path('books/', BookViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('books/<int:pk>/', BookViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # Edition
    path('editions/', EditionViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('editions/<int:pk>/', EditionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # BookImage
    path('images/', BookImageViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('images/<int:pk>/', BookImageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]
