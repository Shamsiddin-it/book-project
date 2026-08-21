from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Edition

from .models import CartItem, Order
from .serializers import CartItemSerializer, OrderSerializer
from .services import place_order, purchases_are_free, validate_purchasable


class CartViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Корзина: /api/purchase/cart/

    Обновлять нечего — у цифрового издания нет количества,
    поэтому только список, добавление и удаление.
    """

    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтр по пользователю здесь же — чужую строку корзины
        # не удалить и по прямому id.
        return (
            CartItem.objects.filter(user=self.request.user)
            .select_related('edition', 'edition__book')
            .prefetch_related('edition__book__authors')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        items = list(self.get_queryset())
        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': len(items),
            'total': sum(item.edition.price for item in items),
            'purchases_are_free': purchases_are_free(),
            'results': serializer.data,
        })


class CheckoutView(APIView):
    """
    POST /api/purchase/checkout/

    Оформляет всё, что лежит в корзине. Пока покупки бесплатны, заказ сразу
    получает статус «оплачен», а издания попадают на полку как купленные.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = list(
            CartItem.objects.filter(user=request.user).select_related('edition')
        )
        if not cart_items:
            raise ValidationError('Корзина пуста.')

        editions = [item.edition for item in cart_items]
        validate_purchasable(request.user, editions)

        order = place_order(request.user, editions)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class AcquireEditionView(APIView):
    """
    POST /api/purchase/editions/<edition_id>/acquire/

    Получить одну книгу, минуя корзину. Пока действует бесплатная выдача —
    это основной путь «читать сейчас» со страницы книги.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        edition = get_object_or_404(Edition, pk=pk, is_active=True)
        validate_purchasable(request.user, [edition])

        order = place_order(request.user, [edition])
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """История заказов: /api/purchase/orders/"""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        # Фильтр по пользователю здесь же — чужой заказ не достать и по прямому id.
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related('items__edition__book__authors')
        )
