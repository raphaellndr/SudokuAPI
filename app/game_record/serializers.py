"""Game record model for tracking user game sessions."""

from datetime import timezone

from rest_framework import serializers

from .models import GameRecord


class GameRecordSerializer(serializers.ModelSerializer[GameRecord]):
    """GameRecord serializer for read operations."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    sudoku_id = serializers.UUIDField(source="sudoku.id", read_only=True, allow_null=True)

    class Meta:
        """Meta class for the GameRecord serializer."""

        model = GameRecord
        fields = [
            "id",
            "user_id",
            "sudoku_id",
            "score",
            "hints_used",
            "checks_used",
            "deletions",
            "time_taken",
            "won",
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
            "created_at",
            "updated_at",
        ]


class GameRecordCreateSerializer(serializers.ModelSerializer[GameRecord]):
    """Serializer for creating game records."""

    sudoku_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        """Meta class for the GameRecord create serializer."""

        model = GameRecord
        fields = [
            "sudoku_id",
            "score",
            "hints_used",
            "checks_used",
            "deletions",
            "time_taken",
            "won",
            "status",
            "original_puzzle",
            "solution",
            "final_state",
            "started_at",
            "completed_at",
        ]

    def validate(self, data):
        """Object-level validation for business logic."""
        # Auto-set completed_at if status is completed and not provided
        if data.get("status") == "completed" and not data.get("completed_at"):
            data["completed_at"] = timezone.now()

        # Business rule: completed won games should have a positive score
        if data.get("status") == "completed" and data.get("won") and data.get("score", 0) <= 0:
            raise serializers.ValidationError(
                "Completed winning games should have a positive score."
            )

        # Business rule: ensure time_taken is provided for completed games
        if data.get("status") == "completed" and not data.get("time_taken"):
            raise serializers.ValidationError(
                {"time_taken": ["Time taken is required for completed games."]}
            )

        # Business rule: ensure final_state is provided for completed games
        if data.get("status") == "completed" and not data.get("final_state"):
            raise serializers.ValidationError(
                {"final_state": ["Final state is required for completed games."]}
            )

        return data

    def create(self, validated_data) -> GameRecord:
        """Creates a new game record.

        Handles sudoku_id -> sudoku conversion.
        """
        sudoku_id = validated_data.pop("sudoku_id", None)
        if sudoku_id:
            from app.sudoku.models import Sudoku

            try:
                validated_data["sudoku"] = Sudoku.objects.get(id=sudoku_id)
            except Sudoku.DoesNotExist:
                validated_data["sudoku"] = None

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

    def validate(self, data):
        """Object-level validation for updates."""
        # Auto-calculate time_taken if completing the game and not provided
        if (
            data.get("status") == "completed"
            and data.get("completed_at")
            and not data.get("time_taken")
            and not self.instance.time_taken
        ):
            time_diff = data["completed_at"] - self.instance.started_at
            data["time_taken"] = int(time_diff.total_seconds())

        # Business rule: completed won games should have a positive score
        if data.get("status") == "completed" and data.get("won") and data.get("score", 0) <= 0:
            raise serializers.ValidationError(
                "Completed winning games should have a positive score."
            )

        return data

    def update(self, instance, validated_data):
        """Updates game record."""
        return super().update(instance, validated_data)
