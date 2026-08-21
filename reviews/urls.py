from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BookRatingSummaryView, BookReviewsView, ReviewViewSet

router = DefaultRouter()
router.register('', ReviewViewSet, basename='review')

urlpatterns = [
    path('books/<int:pk>/', BookReviewsView.as_view(), name='book-reviews'),
    path('books/<int:pk>/summary/', BookRatingSummaryView.as_view(), name='book-rating-summary'),
] + router.urls
