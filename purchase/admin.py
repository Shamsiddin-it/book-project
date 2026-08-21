from django.contrib import admin

from .models import CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ['edition']
    readonly_fields = ['unit_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'provider', 'total', 'amount_paid', 'created_at')
    list_filter = ('status', 'provider')
    search_fields = ('user__username', 'provider_ref')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'paid_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'edition', 'added_at')
    search_fields = ('user__username', 'edition__book__name')
    autocomplete_fields = ('edition',)
