from django.contrib import admin
from django.db.models import Count

from .models import Level, Trophy, UserTrophy


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('icon', 'number', 'name', 'min_points')
    list_display_links = ('icon', 'number', 'name')
    list_editable = ('min_points',)
    ordering = ('number',)


@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = (
        'icon', 'name', 'metric', 'threshold', 'points', 'awarded_count', 'is_active',
    )
    list_display_links = ('icon', 'name')
    list_filter = ('metric', 'is_active')
    list_editable = ('threshold', 'points', 'is_active')
    search_fields = ('code', 'name')

    fieldsets = [
        (None, {'fields': [('name', 'code'), 'description', 'icon']}),
        ('Условие', {
            'fields': [('metric', 'threshold'), 'points', 'is_active'],
            'description': (
                'Награда выдаётся, когда метрика достигает порога. Новые награды '
                'заводятся прямо здесь — код менять не нужно.'
            ),
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(awards_total=Count('awards'))

    @admin.display(description='Выдано', ordering='awards_total')
    def awarded_count(self, obj):
        return obj.awards_total


@admin.register(UserTrophy)
class UserTrophyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trophy', 'earned_at')
    search_fields = ('user__username', 'trophy__name')
    autocomplete_fields = ('user',)
    date_hierarchy = 'earned_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'trophy')
