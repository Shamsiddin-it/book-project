import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Edition
from shelf.models import ShelfItem

from .access import get_shelf_item_for_reading
from .serializers import ReaderManifestSerializer, ReadingProgressSerializer


def _get_edition(pk):
    return get_object_or_404(
        Edition.objects.select_related('book').prefetch_related('book__authors'),
        pk=pk,
        is_active=True,
    )


class ReaderManifestView(APIView):
    """
    GET /api/reader/<edition_id>/

    Отдаёт ридеру всё для старта. Доступен только владельцу издания —
    по составу ответа нельзя понять содержимое книги, но и его мы не показываем
    посторонним, чтобы не раскрывать наличие файла.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        edition = _get_edition(pk)
        item = get_shelf_item_for_reading(request.user, edition)

        has_file = bool(edition.file)
        content_type = None
        size_bytes = None

        if has_file:
            content_type = (
                mimetypes.guess_type(edition.file.name)[0] or 'application/octet-stream'
            )
            try:
                size_bytes = edition.file.size
            except (OSError, ValueError):
                # Запись в БД есть, а файла на диске нет — не роняем весь ответ.
                size_bytes = None

        payload = {
            'edition_id': edition.id,
            'book_id': edition.book_id,
            'book_name': edition.book.name,
            'authors': edition.book.authors.all(),
            'accent_color': edition.book.accent_color,
            'language': edition.book.language,

            'format': edition.format,
            'format_display': edition.get_format_display(),
            'is_audio': edition.format == Edition.Format.AUDIO,

            'content_url': (
                request.build_absolute_uri(reverse('reader-content', args=[edition.id]))
                if has_file else None
            ),
            'audio_link': edition.audio_link or None,
            'content_type': content_type,
            'size_bytes': size_bytes,

            'progress_percent': item.progress_percent if item else 0,
            'position': item.position if item else '',
            'status': item.status if item else ShelfItem.Status.WANT_TO_READ,
            'last_read_at': item.last_read_at if item else None,
        }
        return Response(ReaderManifestSerializer(payload).data)


class ReaderContentView(APIView):
    """
    GET /api/reader/<edition_id>/content/

    Сам файл книги. Единственный путь к нему — прямой ссылки не существует,
    файлы лежат вне MEDIA_ROOT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        edition = _get_edition(pk)
        get_shelf_item_for_reading(request.user, edition)

        if not edition.file:
            raise NotFound('У этого издания нет файла для чтения.')

        content_type = (
            mimetypes.guess_type(edition.file.name)[0] or 'application/octet-stream'
        )

        # В проде отдачу забирает веб-сервер: Django отвечает пустым телом
        # с заголовком, а файл шлёт nginx или Apache.
        accel_header = settings.PROTECTED_MEDIA_ACCEL_HEADER
        if accel_header:
            internal_url = '{}{}'.format(
                settings.PROTECTED_MEDIA_INTERNAL_URL.rstrip('/') + '/',
                edition.file.name.lstrip('/'),
            )
            response = HttpResponse(content_type=content_type)
            response[accel_header] = internal_url
            response['Content-Disposition'] = 'inline; filename="{}"'.format(
                os.path.basename(edition.file.name)
            )
            return response

        try:
            handle = edition.file.open('rb')
        except (FileNotFoundError, OSError):
            raise NotFound('Файл издания не найден на сервере.')

        response = FileResponse(handle, content_type=content_type)
        response['Content-Disposition'] = 'inline; filename="{}"'.format(
            os.path.basename(edition.file.name)
        )
        # Файл платный — его не должны кэшировать промежуточные прокси.
        response['Cache-Control'] = 'private, no-store'
        return response


class ReadingProgressView(APIView):
    """
    GET  /api/reader/<edition_id>/progress/ — где остановились
    PATCH /api/reader/<edition_id>/progress/ — сохранить место
    """

    permission_classes = [IsAuthenticated]

    def _item(self, request, pk):
        edition = _get_edition(pk)
        item = get_shelf_item_for_reading(request.user, edition)
        if item is None:
            # Персонал открыл чужое издание — прогресс писать некуда.
            raise NotFound('Это издание не стоит на вашей полке.')
        return item

    def get(self, request, pk):
        item = self._item(request, pk)
        return Response(ReadingProgressSerializer(item).data)

    def patch(self, request, pk):
        item = self._item(request, pk)
        serializer = ReadingProgressSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        item = serializer.save(last_read_at=timezone.now())

        # Открыли книгу — она уже не «хочу прочитать».
        if item.status == ShelfItem.Status.WANT_TO_READ:
            item.status = ShelfItem.Status.READING

        # Дочитали до конца — закрываем автоматически, чтобы полка не требовала
        # отдельного действия от пользователя.
        if item.progress_percent >= 100:
            item.status = ShelfItem.Status.READ
            item.finished_at = item.finished_at or timezone.now()

        item.save(update_fields=['status', 'finished_at'])
        return Response(ReadingProgressSerializer(item).data, status=status.HTTP_200_OK)
