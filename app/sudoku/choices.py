"""Custom text choices."""

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class _ExtendedTextChoicesMeta(type(TextChoices)):  # type: ignore
    """Metaclass for `_ExtendedTextChoices` to dynamically compute `max_length` when defining
    the class.
    """

    @property
    def max_length(cls) -> int:
        """Returns the maximum length."""
        return max(len(value) for value in cls.values)


class SudokuDifficultyChoices(TextChoices, metaclass=_ExtendedTextChoicesMeta):
    """Sudoku difficulties enum."""

    UNKNOWN = "unknown", _("Unknown")
    EASY = "easy", _("Easy")
    MEDIUM = "medium", _("Medium")
    HARD = "hard", _("Hard")


class SudokuStatusChoices(TextChoices, metaclass=_ExtendedTextChoicesMeta):
    """Sudoku statuses enum."""

    CREATED = "created", _("Created")
    PENDING = "pending", _("Pending")
    RUNNING = "running", _("Running")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    ABORTED = "aborted", _("Aborted")
    INVALID = "invalid", _("Invalid")


__all__ = ["SudokuDifficultyChoices", "SudokuStatusChoices"]
