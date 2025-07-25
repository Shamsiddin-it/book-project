from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, ProfileView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('profile/', ProfileView.as_view(), name='api-profile'),
    path('logout/', LogoutView.as_view(), name='api-logout'),

    # JWT Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
