from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import LogoutView, MeView, PublicUserView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('me/', MeView.as_view(), name='api-me'),
    path('users/<int:pk>/', PublicUserView.as_view(), name='api-public-user'),
    path('logout/', LogoutView.as_view(), name='api-logout'),

    # JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
