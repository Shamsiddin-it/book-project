from django.conf import settings
from django.db import models

from books.models import Edition


class CartItem(models.Model):
    """
    Корзина. Отдельной модели Cart нет — она была бы пустой обёрткой
    вокруг пользователя, а корзина у него всё равно одна.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items',
    )
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name='cart_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'edition'], name='unique_cart_item'),
        ]

    def __str__(self):
        return '{}: {}'.format(self.user.username, self.edition)


class Order(models.Model):
    """
    Заказ. Заводится и для бесплатной выдачи тоже — так история покупок
    остаётся единообразной, а подключение оплаты добавит шаг, а не переделает
    структуру данных.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает оплаты'
        PAID = 'paid', 'Оплачен'
        CANCELLED = 'cancelled', 'Отменён'
        REFUNDED = 'refunded', 'Возвращён'

    class Provider(models.TextChoices):
        FREE = 'free', 'Бесплатная выдача'
        STRIPE = 'stripe', 'Stripe'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders',
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=10, choices=Provider.choices, default=Provider.FREE)

    # Сколько стоило по прайсу на момент заказа и сколько с человека взяли.
    # При бесплатной выдаче первое ненулевое, второе — ноль. Разница видна
    # в отчётах и не теряется, когда цены потом поменяются.
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    provider_ref = models.CharField(
        max_length=255, blank=True, help_text='Идентификатор платежа на стороне провайдера.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return 'Заказ #{} — {} ({})'.format(self.id, self.user.username, self.get_status_display())

    @property
    def is_free(self):
        return self.amount_paid == 0


class OrderItem(models.Model):
    """
    Строка заказа. Цена копируется сюда, а не читается из Edition:
    прайс меняется, а в истории покупок должна остаться та сумма,
    по которой человек покупал.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    edition = models.ForeignKey(Edition, on_delete=models.PROTECT, related_name='order_items')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['order', 'edition'], name='unique_order_item'),
        ]

    def __str__(self):
        return '{} × {}'.format(self.order_id, self.edition)
