"""
Оформление заказа.

Сейчас книги выдаются бесплатно: настройка PURCHASES_ARE_FREE включена.
Заказ при этом создаётся настоящий — с позициями и суммой по прайсу, — просто
шаг оплаты пропускается, а amount_paid остаётся нулевым. Когда появится Stripe,
достаточно выключить флаг и вставить платёж между созданием заказа и выдачей
доступа: модели и выдача доступа менять не придётся.
"""

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from shelf.models import ShelfItem

from .models import CartItem, Order, OrderItem


def purchases_are_free():
    return getattr(settings, 'PURCHASES_ARE_FREE', True)


def owned_edition_ids(user):
    return set(
        ShelfItem.objects.filter(user=user, is_owned=True).values_list('edition_id', flat=True)
    )


def _grant_access(user, editions):
    """
    Кладёт издания на полку и помечает как купленные.

    Полка «создаётся автоматически» — элемента может ещё не быть, а может уже
    лежать со статусом «хочу прочитать». Во втором случае не затираем статус
    и прогресс, только поднимаем флаг владения.
    """
    for edition in editions:
        item, created = ShelfItem.objects.get_or_create(
            user=user, edition=edition, defaults={'is_owned': True},
        )
        if not created and not item.is_owned:
            item.is_owned = True
            item.save(update_fields=['is_owned'])


@transaction.atomic
def place_order(user, editions):
    """
    Создаёт заказ на список изданий и, если покупки бесплатны, сразу выдаёт доступ.

    Возвращает Order. Список изданий должен быть уже проверен вызывающим кодом
    на активность и на то, что человек ими ещё не владеет.
    """
    if not editions:
        raise ValidationError('Нечего оформлять: список изданий пуст.')

    total = sum(edition.price for edition in editions)

    order = Order.objects.create(
        user=user,
        total=total,
        provider=Order.Provider.FREE if purchases_are_free() else Order.Provider.STRIPE,
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, edition=edition, unit_price=edition.price)
        for edition in editions
    ])

    if purchases_are_free():
        order.status = Order.Status.PAID
        order.amount_paid = 0
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'amount_paid', 'paid_at'])

        _grant_access(user, editions)

        # Оформленное из корзины оттуда убираем.
        CartItem.objects.filter(
            user=user, edition__in=editions,
        ).delete()

    return order


def validate_purchasable(user, editions):
    """
    Общая проверка перед оформлением: издание активно и ещё не куплено.

    Нужна и для корзины, и для выдачи одной книги, поэтому живёт здесь,
    а не в сериализаторе.
    """
    already_owned = owned_edition_ids(user)

    for edition in editions:
        if not edition.is_active:
            raise ValidationError(
                'Издание «{}» больше не доступно.'.format(edition)
            )
        if edition.id in already_owned:
            raise ValidationError(
                'Издание «{}» уже есть в вашей библиотеке.'.format(edition)
            )
