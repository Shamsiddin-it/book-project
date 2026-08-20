from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, FollowersView, FollowingView, ToggleFollowView

router = DefaultRouter()
router.register('comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('users/<int:pk>/follow/', ToggleFollowView.as_view(), name='toggle-follow'),
    path('users/<int:pk>/followers/', FollowersView.as_view(), name='followers'),
    path('users/<int:pk>/following/', FollowingView.as_view(), name='following'),
] + router.urls
