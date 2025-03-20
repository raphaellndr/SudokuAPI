"""Serializers for sudokus."""

from typing import TypedDict

from rest_framework import serializers

from .models import Sudoku


class _SudokuParams(TypedDict):
    """Sudoku parameters."""

    title: str
    difficulty: str
    grid: str


class SudokuSerializer(serializers.ModelSerializer[Sudoku]):
    """`Sudoku` serializer."""

    class Meta:
        """Meta class for the `Sudoku` serializer."""

        model = Sudoku
        fields = [
            "id",
            "title",
            "difficulty",
            "grid",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def create(self, validated_data: _SudokuParams) -> Sudoku:
        """Creates and returns a `Sudoku`.

        :param validated_data: Sudoku data.
        :return: `Sudoku`.
        """
        return Sudoku.objects.create(**validated_data)

    def update(self, instance: Sudoku, validated_data: _SudokuParams) -> Sudoku:
        """Updates and returns a `Sudoku`.

        :param instance: `Sudoku` object.
        :param validated_data: Sudoku data.
        :return: Updated `Sudoku`.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class SudokuSolutionSerializer(serializers.ModelSerializer[Sudoku]):
    """Solved sudokus serializer."""

    class Meta:
        """Meta class for the `SudokuSolution` serializer."""

        model = Sudoku
        fields = [
            "id",
            "title",
            "difficulty",
            "grid",
            "status",
            "solution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "title",
            "difficulty",
            "grid",
            "status",
            "solution",
            "created_at",
            "updated_at",
        ]


__all__ = ["SudokuSerializer", "SudokuSolutionSerializer"]
