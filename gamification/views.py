from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .leaderboard import leaderboard_rows
from .models import Trophy
from .serializers import (
    EarnedTrophySerializer,
    GamificationProfileSerializer,
    LeaderboardEntrySerializer,
)
from .services import build_profile, trophy_catalogue

User = get_user_model()

LEADERBOARD_SIZE = 20


def _profile_payload(user, profile):
    return {
        'user': user,
        'points': profile['points'],
        'level': profile['level'],
        'next_level': profile['next_level'],
        'points_to_next': profile['points_to_next'],
        'progress': profile['progress'],
        'metrics': {str(key): value for key, value in profile['metrics'].items()},
        'trophies_earned': len(profile['earned']),
        'trophies_total': Trophy.objects.filter(is_active=True).count(),
        'newly_awarded': profile['newly_awarded'],
    }


class MyGamificationView(APIView):
    """
    GET /api/gamification/me/

    Уровень, очки и прогресс. Запрос заодно доначисляет награды, пороги которых
    уже пройдены: newly_awarded в ответе — то, что выдано прямо сейчас, чтобы
    фронт мог показать поздравление.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = build_profile(request.user)
        return Response(
            GamificationProfileSerializer(_profile_payload(request.user, profile)).data
        )


class PublicGamificationView(APIView):
    """
    GET /api/gamification/users/<id>/

    Чужой профиль достижений. Уважает тот же флаг приватности, что и полка:
    закрыв её, человек прячет и статистику чтения.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        owner = get_object_or_404(User, pk=pk)

        if not owner.is_shelf_public and owner != request.user:
            raise PermissionDenied('Этот пользователь закрыл свой профиль чтения.')

        profile = build_profile(owner)
        payload = _profile_payload(owner, profile)
        # Чужому наблюдателю нечего показывать в «только что получено».
        payload['newly_awarded'] = []
        return Response(GamificationProfileSerializer(payload).data)


class TrophyCatalogueView(APIView):
    """
    GET /api/gamification/trophies/

    Все награды с отметкой о получении и прогрессом. Анонимам отдаётся тот же
    список без прогресса — витрина достижений должна быть видна до регистрации.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        return Response(
            EarnedTrophySerializer(trophy_catalogue(request.user), many=True).data
        )


class LeaderboardView(APIView):
    """
    GET /api/gamification/leaderboard/

    Таблица лидеров. Считается теми же правилами, что и личный профиль, но без
    выдачи наград: один просмотр рейтинга иначе раздавал бы их всем участникам.
    В таблицу попадают только те, кто не закрыл профиль.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        rows = leaderboard_rows(LEADERBOARD_SIZE)
        return Response(LeaderboardEntrySerializer(rows, many=True).data)
