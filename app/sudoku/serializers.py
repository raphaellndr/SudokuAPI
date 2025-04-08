"""Serializers for sudokus."""

from typing import TypedDict
from uuid import UUID

from rest_framework import serializers

from .models import Sudoku, SudokuSolution


class SudokuSolutionSerializer(serializers.ModelSerializer[SudokuSolution]):
    """`SudokuSolution` serializer."""

    sudoku_id = serializers.UUIDField(source="sudoku.id", read_only=True)

    class Meta:
        """Meta class for the `SudokuSolution` serializer."""

        model = SudokuSolution
        fields = ["id", "sudoku_id", "grid", "created_at", "updated_at"]
        read_only_fields = ["id", "sudoku_id", "grid", "created_at", "updated_at"]


class _SudokuSolution(TypedDict):
    """Sudoku solution parameters."""

    id: UUID
    sudoku_id: UUID
    grid: str | None
    created_at: str
    updated_at: str


class _SudokuParams(TypedDict, total=False):
    """Sudoku parameters."""

    id: UUID
    user_id: UUID
    title: str
    difficulty: str
    grid: str
    status: str
    task_id: str | None
    solution: _SudokuSolution | None
    created_at: str
    updated_at: str


class AnonymousSudokuSerializer(serializers.ModelSerializer[Sudoku]):
    """`Sudoku` serializer for anonymous users."""

    solution = SudokuSolutionSerializer(required=False, allow_null=True)

    class Meta:
        """Meta class for the anonymous `Sudoku` serializer."""

        model = Sudoku
        fields = [
            "id",
            "title",
            "difficulty",
            "grid",
            "status",
            "task_id",
            "solution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "task_id", "created_at", "updated_at"]

    def create(self, validated_data: _SudokuParams) -> Sudoku:
        """Creates and returns a `Sudoku`.

        Adds a solution, if any.

        :param validated_data: Sudoku data.
        :return: `Sudoku`.
        """
        solution_data = validated_data.pop("solution", None)
        sudoku = Sudoku.objects.create(**validated_data)

        if solution_data:
            SudokuSolution.objects.create(sudoku=sudoku, **solution_data)

        return sudoku


class SudokuSerializer(AnonymousSudokuSerializer):
    """`Sudoku` serializer."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)

    class Meta(AnonymousSudokuSerializer.Meta):
        """Meta class for the `Sudoku` serializer."""

        fields = ["user_id"] + AnonymousSudokuSerializer.Meta.fields

    def update(self, instance: Sudoku, validated_data: _SudokuParams) -> Sudoku:
        """Updates and returns a `Sudoku`.

        Updates or add a solution, if any.

        :param instance: `Sudoku` object.
        :param validated_data: Sudoku data.
        :return: Updated `Sudoku`.
        """
        solution_data = validated_data.pop("solution", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if solution_data:
            if hasattr(instance, "solution"):
                solution = instance.solution
                solution.grid = solution_data.get("grid", solution.grid)
                solution.save()
            else:
                SudokuSolution.objects.create(sudoku=instance, **solution_data)

        return instance


__all__ = ["AnonymousSudokuSerializer", "SudokuSerializer", "SudokuSolutionSerializer"]
