from django.urls import path

from .views import PersonalRecommendationsView, SimilarBooksView

urlpatterns = [
    path('', PersonalRecommendationsView.as_view(), name='recommendations'),
    path('similar/<int:pk>/', SimilarBooksView.as_view(), name='similar-books'),
]
