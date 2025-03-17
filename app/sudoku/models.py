"""Sudoku models."""

from core.base import TimestampedMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import SudokuDifficultyChoices


class Sudoku(TimestampedMixin):
    """Sudoku object."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(_("title"), max_length=255)
    difficulty = models.CharField(
        _("difficulty"),
        max_length=SudokuDifficultyChoices.max_length,
        choices=SudokuDifficultyChoices.values,
        default=SudokuDifficultyChoices.UNKNOWN,
    )
    grid = models.CharField(_("grid"), max_length=81, default="." * 81)

    class Meta:
        """Meta class for the sudoku model."""

        verbose_name = "sudoku"
        verbose_name_plural = "sudokus"

    def __str__(self) -> str:
        return self.title
