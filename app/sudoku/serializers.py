"""Serializers for sudokus."""

from typing import TypedDict

from core.models import Sudoku
from rest_framework import serializers


class SudokuParams(TypedDict):
    """Sudoku parameters."""

    title: str
    difficulty: str
    grid: str


class SudokuSerializer(serializers.ModelSerializer[Sudoku]):
    """Sudoku serializer."""

    class Meta:
        """Meta class for the sudoku serializer."""

        model = Sudoku
        fields = [
            "id",
            "title",
            "difficulty",
            "grid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "id"]

    def create(self, validated_data: SudokuParams) -> Sudoku:
        """Creates and returns a sudoku.

        :param validated_data: Sudoku data.
        :return: Sudoku object.
        """
        return Sudoku.objects.create(**validated_data)

    def update(self, instance: Sudoku, validated_data: SudokuParams) -> Sudoku:
        """Updates and returns a sudoku.

        :param instance: Sudoku object.
        :param validated_data: Sudoku data.
        :return: Updated sudoku object.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
