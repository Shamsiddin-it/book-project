from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AcquireEditionView, CartViewSet, CheckoutView, OrderViewSet

router = DefaultRouter()
router.register('cart', CartViewSet, basename='cart')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('editions/<int:pk>/acquire/', AcquireEditionView.as_view(), name='acquire-edition'),
] + router.urls
