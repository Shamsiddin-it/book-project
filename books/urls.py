from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthorViewSet,
    BookAuthorViewSet,
    BookViewSet,
    CategoryViewSet,
    CharacterViewSet,
    EditionViewSet,
    LanguageListView,
    MoodboardImageViewSet,
)

router = DefaultRouter()
router.register('books', BookViewSet, basename='book')
router.register('categories', CategoryViewSet, basename='category')
router.register('authors', AuthorViewSet, basename='author')
router.register('editions', EditionViewSet, basename='edition')
router.register('moodboard', MoodboardImageViewSet, basename='moodboard')
router.register('characters', CharacterViewSet, basename='character')
router.register('book-authors', BookAuthorViewSet, basename='book-author')

urlpatterns = [
    path('languages/', LanguageListView.as_view(), name='languages'),
] + router.urls
