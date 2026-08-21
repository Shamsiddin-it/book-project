from django.contrib import admin
from django.utils.html import format_html

from .models import CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ['edition']
    readonly_fields = ['unit_price']
    verbose_name = 'Позиция'
    verbose_name_plural = 'Позиции заказа'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'provider', 'total', 'amount_paid', 'free_badge', 'created_at')
    list_display_links = ('id', 'user')
    list_filter = ('status', 'provider')
    search_fields = ('user__username', 'provider_ref')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'paid_at')
    date_hierarchy = 'created_at'

    fieldsets = [
        (None, {'fields': [('user', 'status'), ('provider', 'provider_ref')]}),
        ('Деньги', {
            'fields': [('total', 'amount_paid')],
            'description': (
                'total — сумма по прайсу на момент заказа, amount_paid — сколько '
                'реально взято. При бесплатной выдаче второе равно нулю.'
            ),
        }),
        ('Даты', {'fields': [('created_at', 'paid_at')]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    @admin.display(description='Выдача')
    def free_badge(self, obj):
        if obj.is_free:
            return format_html('<span style="color:#2e7d32">бесплатно</span>')
        return format_html('<span style="color:#555">оплачено</span>')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'edition', 'added_at')
    search_fields = ('user__username', 'edition__book__name')
    autocomplete_fields = ('edition', 'user')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'edition', 'edition__book')
