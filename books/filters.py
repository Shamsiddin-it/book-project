import django_filters
from django.db.models import F, Q

from .models import Book


class BookFilter(django_filters.FilterSet):
    """
    Фильтры каталога.

    on_sale и min_rating выражены через связанные таблицы, поэтому их нельзя
    описать простым filterset_fields — нужен явный FilterSet.
    """

    on_sale = django_filters.BooleanFilter(
        method='filter_on_sale',
        label='Только книги со скидкой',
    )
    min_rating = django_filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte',
        label='Средняя оценка не ниже',
    )
    max_price = django_filters.NumberFilter(
        method='filter_max_price',
        label='Цена самого дешёвого издания не выше',
    )

    class Meta:
        model = Book
        fields = ['language', 'categories', 'authors', 'is_active']

    def filter_on_sale(self, queryset, name, value):
        if not value:
            return queryset
        # distinct нужен: у книги может быть несколько изданий со скидкой,
        # и join размножит строки.
        return queryset.filter(
            Q(editions__is_active=True)
            & Q(editions__old_price__isnull=False)
            & Q(editions__old_price__gt=F('editions__price'))
        ).distinct()

    def filter_max_price(self, queryset, name, value):
        return queryset.filter(
            editions__is_active=True, editions__price__lte=value,
        ).distinct()
