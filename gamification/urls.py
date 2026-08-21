from django.urls import path

from .views import (
    LeaderboardView,
    MyGamificationView,
    PublicGamificationView,
    TrophyCatalogueView,
)

urlpatterns = [
    path('me/', MyGamificationView.as_view(), name='gamification-me'),
    path('trophies/', TrophyCatalogueView.as_view(), name='trophy-catalogue'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('users/<int:pk>/', PublicGamificationView.as_view(), name='gamification-public'),
]
