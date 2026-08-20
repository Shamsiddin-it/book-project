from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MyShelfViewSet, PublicShelfView

router = DefaultRouter()
router.register('', MyShelfViewSet, basename='shelf')

urlpatterns = [
    path('users/<int:pk>/', PublicShelfView.as_view(), name='public-shelf'),
] + router.urls
