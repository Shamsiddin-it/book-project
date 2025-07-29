from django.urls import path
from .views import (
    CategoryViewSet, AuthorViewSet, BookViewSet,
    BookAuthorViewSet, BookImageViewSet
)

urlpatterns = [
    path('categories/', CategoryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('categories/<int:pk>/', CategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('authors/', AuthorViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('authors/<int:pk>/', AuthorViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('books/', BookViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('books/<int:pk>/', BookViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('book-authors/', BookAuthorViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('book-authors/<int:pk>/', BookAuthorViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('images/', BookImageViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('images/<int:pk>/', BookImageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]
