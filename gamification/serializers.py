from rest_framework import serializers

from accounts.serializers import UserBriefSerializer

from .models import Level, Trophy


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['number', 'name', 'min_points', 'icon']


class TrophySerializer(serializers.ModelSerializer):
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = Trophy
        fields = [
            'id', 'code', 'name', 'description', 'icon',
            'metric', 'metric_display', 'threshold', 'points',
        ]


class EarnedTrophySerializer(serializers.Serializer):
    """Награда вместе с прогрессом — годится и для полученных, и для будущих."""

    trophy = TrophySerializer()
    earned = serializers.BooleanField()
    earned_at = serializers.DateTimeField(allow_null=True)
    current = serializers.IntegerField()
    progress = serializers.IntegerField()


class GamificationProfileSerializer(serializers.Serializer):
    user = UserBriefSerializer()
    points = serializers.IntegerField()
    level = LevelSerializer(allow_null=True)
    next_level = LevelSerializer(allow_null=True)
    points_to_next = serializers.IntegerField(allow_null=True)
    progress = serializers.IntegerField()
    metrics = serializers.DictField(child=serializers.IntegerField())
    trophies_earned = serializers.IntegerField()
    trophies_total = serializers.IntegerField()
    newly_awarded = TrophySerializer(many=True)


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user = UserBriefSerializer()
    points = serializers.IntegerField()
    level = LevelSerializer(allow_null=True)
    books_read = serializers.IntegerField()
