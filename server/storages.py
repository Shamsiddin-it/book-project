from django.conf import settings
from django.core.files.storage import FileSystemStorage


class ProtectedStorage(FileSystemStorage):
    """
    Хранилище для файлов, которые нельзя раздавать напрямую: сами книги.

    MEDIA_ROOT отдаётся веб-сервером по /media/, поэтому всё, что там лежит,
    доступно любому, кто знает URL. Файлы книг живут отдельно и уходят
    пользователю только через ридер, после проверки, что издание куплено.

    url() намеренно падает: у этих файлов публичной ссылки не существует.
    Без этого FileSystemStorage подставил бы MEDIA_URL и вернул правдоподобный,
    но неверный адрес, который легко утёк бы в API.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('location', settings.PROTECTED_MEDIA_ROOT)
        super().__init__(**kwargs)

    def url(self, name):
        raise ValueError(
            'У файлов книг нет публичного URL. '
            'Отдавать их можно только через /api/reader/<edition_id>/content/.'
        )


protected_storage = ProtectedStorage()
