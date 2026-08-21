from django.contrib import admin

from .models import Level, Trophy, UserTrophy


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'min_points', 'icon')
    ordering = ('number',)


@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'metric', 'threshold', 'points', 'is_active')
    list_filter = ('metric', 'is_active')
    search_fields = ('code', 'name')


@admin.register(UserTrophy)
class UserTrophyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trophy', 'earned_at')
    search_fields = ('user__username', 'trophy__name')
