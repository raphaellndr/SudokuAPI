"""Sudoku models."""

import uuid

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.core.models import TimestampedMixin

from .choices import SudokuDifficultyChoices, SudokuStatusChoices


class Sudoku(TimestampedMixin):
    """Model to store Sudokus and their solutions."""

    id = models.UUIDField(
        _("sudoku identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_sudokus",
        verbose_name=_("player"),
        null=True,
    )
    title = models.CharField(
        _("title"),
        max_length=255,
    )
    difficulty = models.CharField(
        _("difficulty"),
        max_length=SudokuDifficultyChoices.max_length,
        choices=SudokuDifficultyChoices.choices,
        default=SudokuDifficultyChoices.UNKNOWN,
    )
    grid = models.CharField(
        _("grid"),
        max_length=81,
        validators=[MinLengthValidator(limit_value=81)],
    )
    status = models.CharField(
        _("status"),
        max_length=SudokuStatusChoices.max_length,
        choices=SudokuStatusChoices.choices,
        default=SudokuStatusChoices.CREATED,
    )
    task_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        """Meta class for the sudoku model."""

        verbose_name = "sudoku"
        verbose_name_plural = "sudokus"

    def __str__(self) -> str:
        return f"Sudoku {self.id} - Status: {self.status}"


class SudokuSolution(TimestampedMixin):
    """Model to store Sudoku solutions."""

    id = models.UUIDField(
        _("sudoku solution identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    sudoku = models.OneToOneField(
        Sudoku,
        on_delete=models.CASCADE,
        related_name="solution",
        verbose_name=_("sudoku"),
    )
    grid = models.CharField(
        _("solution grid"),
        max_length=81,
        validators=[MinLengthValidator(limit_value=81)],
    )

    def __str__(self) -> str:
        return f"Solution for Sudoku {self.sudoku.id}"


__all__ = ["Sudoku", "SudokuSolution"]
