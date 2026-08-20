from rest_framework.exceptions import PermissionDenied

from shelf.models import ShelfItem


def get_shelf_item_for_reading(user, edition):
    """
    Единственное место, где решается, можно ли пользователю открыть издание.

    Доступ есть, если издание куплено (ShelfItem.is_owned) либо пользователь —
    персонал. Пока покупки не подключены, is_owned проставляется через админку.

    Возвращает ShelfItem, чтобы вызывающий код мог писать в него прогресс.
    Персоналу элемент полки может и не принадлежать — тогда вернётся None.
    """
    if not user.is_authenticated:
        raise PermissionDenied('Чтобы читать, нужно войти в аккаунт.')

    item = ShelfItem.objects.filter(user=user, edition=edition).first()

    if item is not None and item.is_owned:
        return item

    if user.is_staff:
        return item

    raise PermissionDenied('Это издание не куплено.')


def edition_has_content(edition):
    """Есть ли что открывать: файл для чтения или ссылка на аудио."""
    return bool(edition.file) or bool(edition.audio_link)
