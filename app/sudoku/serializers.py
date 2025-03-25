"""Serializers for sudokus."""

from typing import TypedDict

from rest_framework import serializers

from .models import Sudoku, SudokuSolution


class _SudokuParams(TypedDict):
    """Sudoku parameters."""

    title: str
    difficulty: str
    grid: str


class SudokuSolutionSerializer(serializers.ModelSerializer[SudokuSolution]):
    """`SudokuSolution` serializer."""

    sudoku_id = serializers.UUIDField(source="sudoku.id", read_only=True)

    class Meta:
        """Meta class for the `SudokuSolution` serializer."""

        model = SudokuSolution
        fields = ["id", "sudoku_id", "grid", "created_at", "updated_at"]
        read_only_fields = ["id", "sudoku_id", "created_at", "updated_at"]


class SudokuSerializer(serializers.ModelSerializer[Sudoku]):
    """`Sudoku` serializer."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    solution = SudokuSolutionSerializer(required=False, allow_null=True)

    class Meta:
        """Meta class for the `Sudoku` serializer."""

        model = Sudoku
        fields = [
            "id",
            "user_id",
            "title",
            "difficulty",
            "grid",
            "status",
            "task_id",
            "solution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "status", "task_id", "created_at", "updated_at"]

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

    def update(self, instance: Sudoku, validated_data: _SudokuParams) -> Sudoku:
        """Updates and returns a `Sudoku`.

        :param instance: `Sudoku` object.
        :param validated_data: Sudoku data.
        :return: Updated `Sudoku`.
        """
        solution_data = validated_data.pop("solution", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle solution data if provided
        if solution_data:
            if hasattr(instance, "solution"):
                solution = instance.solution
                solution.grid = solution_data.get("grid", solution.grid)
                solution.save()
            else:
                SudokuSolution.objects.create(sudoku=instance, **solution_data)

        return instance


__all__ = ["SudokuSerializer", "SudokuSolutionSerializer"]
