from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BookNotesView, MyNotesViewSet, PublicNotesView

router = DefaultRouter()
router.register('', MyNotesViewSet, basename='note')

urlpatterns = [
    path('users/<int:pk>/', PublicNotesView.as_view(), name='public-notes'),
    path('books/<int:pk>/', BookNotesView.as_view(), name='book-notes'),
] + router.urls
