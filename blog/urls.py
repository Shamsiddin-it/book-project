from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PostViewSet, TagListView

router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')

urlpatterns = [
    path('tags/', TagListView.as_view(), name='blog-tags'),
] + router.urls
