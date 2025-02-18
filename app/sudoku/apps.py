"""Sudoku app configuration."""

from django.apps import AppConfig


class SudokuConfig(AppConfig):
    """Sudoku app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "sudoku"
