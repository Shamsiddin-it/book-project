from django.db import models
from books.models import Book
from accounts.models import User
class Liked(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')  # Prevent duplicates

    def __str__(self):
        return f'{self.user.username} liked {self.book.name}'
    
