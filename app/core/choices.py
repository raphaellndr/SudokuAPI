"""Custom TextChoice metaclass."""

from django.db.models import TextChoices


class ExtendedTextChoicesMeta(type(TextChoices)):  # type: ignore
    """Metaclass for `_ExtendedTextChoices` to dynamically compute `max_length` when defining
    the class.
    """

    @property
    def max_length(cls) -> int:
        """Returns the maximum length."""
        return max(len(value) for value in cls.values)


__all__ = ["ExtendedTextChoicesMeta"]
