"""Game record model for tracking user game sessions."""

from datetime import timezone

from rest_framework import serializers

from .models import GameRecord


class GameRecordSerializer(serializers.ModelSerializer[GameRecord]):
    """GameRecord serializer."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    sudoku_id = serializers.UUIDField(source="sudoku.id", read_only=True, allow_null=True)
    time_taken_seconds = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the GameRecord serializer."""

        model = GameRecord
        fields = [
            "id",
            "user_id",
            "sudoku_id",
            "time_taken_seconds",
            "score",
            "hints_used",
            "checks_used",
            "deletions",
            "won",
            "time_taken",
            "status",
            "original_puzzle",
            "solution",
            "final_state",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "sudoku_id",
            "time_taken_seconds",
            "created_at",
            "updated_at",
        ]

    def get_time_taken_seconds(self, obj: GameRecord) -> int | None:
        """Get time taken in seconds for easier frontend handling."""
        if obj.time_taken:
            return int(obj.time_taken.total_seconds())
        return None

    def validate(self, data):
        """Validate game record data."""
        if data.get("status") == "completed" and not data.get("completed_at"):
            data["completed_at"] = timezone.now()

        # Calculate time_taken if completed
        if data.get("completed_at") and data.get("started_at"):
            data["time_taken"] = data["completed_at"] - data["started_at"]

        return data


class GameRecordCreateSerializer(serializers.ModelSerializer[GameRecord]):
    """Serializer for creating game records."""

    class Meta:
        """Meta class for the GameRecord create serializer."""

        model = GameRecord
        fields = [
            "started_at",
            "original_puzzle",
            "solution",
            "sudoku",
        ]

    def create(self, validated_data) -> GameRecord:
        """Create a new game record."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class GameRecordUpdateSerializer(serializers.ModelSerializer[GameRecord]):
    """Serializer for updating game records."""

    class Meta:
        """Meta class for the GameRecord update serializer."""

        model = GameRecord
        fields = [
            "completed_at",
            "status",
            "hints_used",
            "checks_used",
            "deletions",
            "won",
            "score",
            "time_taken",
            "final_state",
        ]

    def update(self, instance: GameRecord, validated_data) -> GameRecord:
        """Update game record."""
        # Auto-calculate time_taken if completing the game
        if (
            validated_data.get("status") == "completed"
            and validated_data.get("completed_at")
            and not instance.time_taken
        ):
            validated_data["time_taken"] = validated_data["completed_at"] - instance.started_at

        return super().update(instance, validated_data)
