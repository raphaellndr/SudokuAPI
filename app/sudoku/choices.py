"""Custom text choices."""

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from app.core.choices import ExtendedTextChoicesMeta


class SudokuDifficultyChoices(TextChoices, metaclass=ExtendedTextChoicesMeta):
    """Sudoku difficulties enum."""

    UNKNOWN = "unknown", _("Unknown")
    EASY = "easy", _("Easy")
    MEDIUM = "medium", _("Medium")
    HARD = "hard", _("Hard")


class SudokuStatusChoices(TextChoices, metaclass=ExtendedTextChoicesMeta):
    """Sudoku statuses enum."""

    CREATED = "created", _("Created")
    PENDING = "pending", _("Pending")
    RUNNING = "running", _("Running")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    ABORTED = "aborted", _("Aborted")
    INVALID = "invalid", _("Invalid")


__all__ = ["SudokuDifficultyChoices", "SudokuStatusChoices"]
