"""Custom TextChoice metaclass."""

from django.db.models import TextChoices


class ExtendedTextChoicesMeta(type(TextChoices)):  # type: ignore
    """Dynamically computes ``max_length`` from the choice values.

    Lets a `TextChoices` subclass expose ``max_length`` for use in model field definitions.
    """

    @property
    def max_length(cls) -> int:
        """Returns the maximum length."""
        return max(len(value) for value in cls.values)


__all__ = ["ExtendedTextChoicesMeta"]
