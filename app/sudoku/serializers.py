"""Serializers for sudokus."""

from typing import Any
from rest_framework import serializers

from core.models import Sudoku


class SudokuSerializer(serializers.ModelSerializer):
    """Sudoku serializer."""

    class Meta:
        model = Sudoku
        fields = [
            "id",
            "title",
            "difficulty",
            "grid",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data: Any) -> Sudoku:
        """Creates and returns a sudoku."""
        sudoku = Sudoku.objects.create(**validated_data)
        return sudoku

    def update(self, instance: Sudoku, validated_data: dict[str, Any]) -> Sudoku:
        """Updates and returns a sudoku."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
