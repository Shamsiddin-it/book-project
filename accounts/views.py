from rest_framework import generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from books.serializers import BookSerializer
from .serializers import ProfileSerializer, RegisterSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Profile
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class FavouriteBooksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        favourites = user.profile.favourites.all()
        serializer = BookSerializer(favourites, many=True, context={'request': request})
        return Response(serializer.data)