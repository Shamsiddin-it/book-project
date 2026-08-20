from django.urls import path

from .views import ReaderContentView, ReaderManifestView, ReadingProgressView

urlpatterns = [
    path('<int:pk>/', ReaderManifestView.as_view(), name='reader-manifest'),
    path('<int:pk>/content/', ReaderContentView.as_view(), name='reader-content'),
    path('<int:pk>/progress/', ReadingProgressView.as_view(), name='reader-progress'),
]
