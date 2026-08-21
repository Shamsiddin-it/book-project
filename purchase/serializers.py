from rest_framework import serializers

from books.models import Edition
from shelf.serializers import ShelfEditionSerializer

from .models import CartItem, Order, OrderItem
from .services import owned_edition_ids


class CartItemSerializer(serializers.ModelSerializer):
    edition = ShelfEditionSerializer(read_only=True)
    edition_id = serializers.PrimaryKeyRelatedField(
        queryset=Edition.objects.filter(is_active=True),
        source='edition',
        write_only=True,
    )
    price = serializers.DecimalField(
        source='edition.price', max_digits=10, decimal_places=2, read_only=True,
    )

    class Meta:
        model = CartItem
        fields = ['id', 'edition', 'edition_id', 'price', 'added_at']

    def validate_edition_id(self, edition):
        user = self.context['request'].user

        if CartItem.objects.filter(user=user, edition=edition).exists():
            raise serializers.ValidationError('Это издание уже в корзине.')

        if edition.id in owned_edition_ids(user):
            raise serializers.ValidationError('Это издание уже есть в вашей библиотеке.')

        return edition


class OrderItemSerializer(serializers.ModelSerializer):
    edition = ShelfEditionSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'edition', 'unit_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_free = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display', 'provider',
            'total', 'amount_paid', 'is_free',
            'items', 'created_at', 'paid_at',
        ]
