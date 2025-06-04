"""Serializers for the user API View."""

from datetime import date, timedelta
from typing import Any, TypedDict

from rest_framework import serializers

from .models import DailyUserStats, User, UserStats


class UserStatsSerializer(serializers.ModelSerializer[UserStats]):
    """`UserStats` serializer."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    win_rate = serializers.ReadOnlyField()
    average_time_seconds = serializers.ReadOnlyField()

    class Meta:
        """Meta class for the `UserStats` serializer."""

        model = UserStats
        fields = [
            "id",
            "user_id",
            "games_played",
            "games_won",
            "games_lost",
            "total_time_seconds",
            "best_time_seconds",
            "win_rate",
            "average_time_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "created_at",
            "updated_at",
        ]


class DailyUserStatsSerializer(serializers.ModelSerializer[DailyUserStats]):
    """Daily user stats serializer."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    win_rate = serializers.ReadOnlyField()
    average_time_seconds = serializers.ReadOnlyField()

    class Meta:
        model = DailyUserStats
        fields = [
            "id",
            "user_id",
            "date",
            "games_played",
            "games_won",
            "games_lost",
            "total_time_seconds",
            "best_time_seconds",
            "win_rate",
            "average_time_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "created_at",
            "updated_at",
        ]


class DailyStatsRangeSerializer(serializers.Serializer):
    """Serializer for getting daily stats within a date range."""

    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError("Start date must be before end date")
        return data


class ChartDataSerializer(serializers.Serializer):
    """Serializer for chart data points."""

    date = serializers.DateField()
    games_played = serializers.IntegerField()
    games_won = serializers.IntegerField()
    games_lost = serializers.IntegerField()
    win_rate = serializers.FloatField()
    average_time = serializers.FloatField()


class GameResultSerializer(serializers.Serializer):
    """Serializer for recording game results."""

    won = serializers.BooleanField()
    time_seconds = serializers.IntegerField(min_value=0)

    def validate_time_seconds(self, value):
        if value < 0:
            raise serializers.ValidationError("Time cannot be negative")
        return value


class _UserParams(TypedDict):
    """User parameters."""

    username: str
    email: str
    password: str


class UserSerializer(serializers.ModelSerializer[User]):
    """`User` serializer."""

    stats = UserStatsSerializer(read_only=True)

    class Meta:
        """Meta class for the User serializer."""

        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: _UserParams) -> User:
        """Creates and returns a user with encrypted password.

        :param validated_data: User data.
        :return: `User` object.
        """
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance: User, validated_data: _UserParams) -> User:
        """Updates and returns the `User`.

        :param instance: `User` object.
        :param validated_data: `User` data.
        :return: Updated `User` object.
        """
        validated_data_copy = dict(validated_data)
        password = validated_data_copy.pop("password", None)
        user: User = super().update(instance, validated_data_copy)

        if password:
            user.set_password(password)  # type: ignore
            user.save()

        return user


class UserWithDailyStatsSerializer(serializers.ModelSerializer[User]):
    """User serializer with recent daily stats included."""

    stats = UserStatsSerializer(read_only=True)
    recent_daily_stats = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the User serializer with daily stats."""

        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "stats",
            "recent_daily_stats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_recent_daily_stats(self, obj: User) -> list[dict[str, Any]]:
        """Get daily stats for the last 30 days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=29)  # Last 30 days including today

        daily_stats = obj.daily_stats.filter(date__gte=start_date, date__lte=end_date).order_by(
            "date"
        )

        # Create a complete date range with zeros for missing days
        chart_data = []
        current_date = start_date
        stats_dict = {stat.date: stat for stat in daily_stats}

        while current_date <= end_date:
            if current_date in stats_dict:
                stat = stats_dict[current_date]
                chart_data.append(
                    {
                        "date": current_date.isoformat(),
                        "games_played": stat.games_played,
                        "games_won": stat.games_won,
                        "games_lost": stat.games_lost,
                        "win_rate": round(stat.win_rate, 2),
                        "average_time": round(stat.average_time_seconds, 2),
                        "best_time": stat.best_time_seconds,
                    }
                )
            else:
                # Fill missing days with zeros
                chart_data.append(
                    {
                        "date": current_date.isoformat(),
                        "games_played": 0,
                        "games_won": 0,
                        "games_lost": 0,
                        "win_rate": 0.0,
                        "average_time": 0.0,
                        "best_time": None,
                    }
                )
            current_date += timedelta(days=1)

        return chart_data


class WeeklyStatsSerializer(serializers.Serializer):
    """Serializer for weekly aggregated stats."""

    week_start = serializers.DateField()
    week_end = serializers.DateField()
    games_played = serializers.IntegerField()
    games_won = serializers.IntegerField()
    games_lost = serializers.IntegerField()
    win_rate = serializers.FloatField()
    total_time_seconds = serializers.IntegerField()
    average_time_seconds = serializers.FloatField()
    best_time_seconds = serializers.IntegerField(allow_null=True)


class MonthlyStatsSerializer(serializers.Serializer):
    """Serializer for monthly aggregated stats."""

    year = serializers.IntegerField()
    month = serializers.IntegerField()
    month_name = serializers.CharField()
    games_played = serializers.IntegerField()
    games_won = serializers.IntegerField()
    games_lost = serializers.IntegerField()
    win_rate = serializers.FloatField()
    total_time_seconds = serializers.IntegerField()
    average_time_seconds = serializers.FloatField()
    best_time_seconds = serializers.IntegerField(allow_null=True)


__all__ = [
    "ChartDataSerializer",
    "DailyStatsRangeSerializer",
    "DailyUserStatsSerializer",
    "GameResultSerializer",
    "MonthlyStatsSerializer",
    "UserSerializer",
    "UserStatsSerializer",
    "UserWithDailyStatsSerializer",
    "WeeklyStatsSerializer",
]
