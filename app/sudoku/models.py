"""Sudoku models."""

import uuid

from core.base import TimestampedMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

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
    )
    title = models.CharField(
        _("title"),
        max_length=255,
    )
    difficulty = models.CharField(
        _("difficulty"),
        max_length=SudokuDifficultyChoices.max_length,
        choices=SudokuDifficultyChoices.values,
        default=SudokuDifficultyChoices.UNKNOWN,
    )
    grid = models.CharField(
        _("grid"),
        max_length=81,
        default="." * 81,
    )
    # TODO: créer un modèle SudokuSolution avec solution et statut
    solution = models.CharField(
        _("solution"),
        max_length=81,
        blank=True,
        null=True,
    )
    status = models.CharField(
        _("status"),
        max_length=SudokuStatusChoices.max_length,
        choices=SudokuStatusChoices.choices,
        default=SudokuStatusChoices.CREATED,
    )

    class Meta:
        """Meta class for the sudoku model."""

        verbose_name = "sudoku"
        verbose_name_plural = "sudokus"

    def __str__(self) -> str:
        return f"Sudoku {self.id} - Status: {self.status}"
    

__all__ = ["Sudoku"]
