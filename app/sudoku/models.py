"""Sudoku models."""

from core.base import TimestampedMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Sudoku(TimestampedMixin):
    """Sudoku object."""

    class _DifficultyChoices(models.TextChoices):
        """Sudoku difficulties enum."""

        UNKNOWN = "Unknown", _("Unknown")
        EASY = "Easy", _("Easy")
        MEDIUM = "Medium", _("Medium")
        HARD = "Hard", _("Hard")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # remove every sudoku linked to the user
    )
    title = models.CharField(_("title"), max_length=255)
    difficulty = models.CharField(
        _("difficulty"),
        max_length=10,
        choices=_DifficultyChoices.choices,
        default=_DifficultyChoices.UNKNOWN,
    )
    grid = models.CharField(_("grid"), max_length=81, default="." * 81)

    class Meta:
        """Meta class for the sudoku model."""

        verbose_name = "sudoku"
        verbose_name_plural = "sudokus"

    def __str__(self) -> str:
        return self.title
