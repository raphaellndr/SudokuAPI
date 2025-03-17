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

    UNKNOWN = "Unknown", _("Unknown")
    EASY = "Easy", _("Easy")
    MEDIUM = "Medium", _("Medium")
    HARD = "Hard", _("Hard")
