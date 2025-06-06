"""Serializers for the user API View."""

from typing import TypedDict

from rest_framework import serializers

from .models import User, UserStats


class UserStatsSerializer(serializers.ModelSerializer):
    """`UserStats` serializer."""

    class Meta:
        """Meta class for the UserStats serializer."""

        model = UserStats
        fields = [
            "total_games",
            "completed_games",
            "abandoned_games",
            "stopped_games",
            "in_progress_games",
            "won_games",
            "lost_games",
            "win_rate",
            "total_time_seconds",
            "average_time_seconds",
            "best_time_seconds",
            "average_score",
            "best_score",
            "total_hints_used",
            "total_checks_used",
            "total_deletions",
        ]
        read_only_fields = fields


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


class GameStatsSerializer(serializers.Serializer):
    """Serializer for user game statistics."""

    total_games = serializers.IntegerField()
    completed_games = serializers.IntegerField()
    abandoned_games = serializers.IntegerField()
    stopped_games = serializers.IntegerField()
    in_progress_games = serializers.IntegerField()
    won_games = serializers.IntegerField()
    lost_games = serializers.IntegerField()
    win_rate = serializers.FloatField()
    total_time_seconds = serializers.IntegerField()
    average_time_seconds = serializers.IntegerField(allow_null=True)
    best_time_seconds = serializers.IntegerField(allow_null=True)
    total_score = serializers.IntegerField()
    average_score = serializers.FloatField(allow_null=True)
    best_score = serializers.IntegerField(allow_null=True)
    total_hints_used = serializers.IntegerField()
    total_checks_used = serializers.IntegerField()
    total_deletions = serializers.IntegerField()


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for leaderboard entries."""

    user_id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    total_games = serializers.IntegerField()
    won_games = serializers.IntegerField()
    completed_games = serializers.IntegerField()
    win_rate = serializers.FloatField()
    total_score = serializers.IntegerField()
    best_score = serializers.IntegerField(allow_null=True)
    average_score = serializers.FloatField(allow_null=True)
    best_time_seconds = serializers.IntegerField(allow_null=True)
    total_time_seconds = serializers.IntegerField(allow_null=True)


__all__ = [
    "GameStatsSerializer",
    "LeaderboardSerializer",
    "UserSerializer",
    "UserStatsSerializer",
]
