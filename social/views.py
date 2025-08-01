from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Liked
from books.models import Book
from django.shortcuts import get_object_or_404

class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        liked, created = Liked.objects.get_or_create(user=request.user, book=book)
        if not created:
            liked.delete()
            return Response({'liked': False})
        return Response({'liked': True})