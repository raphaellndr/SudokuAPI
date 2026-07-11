---
paths:
  - "app/*/models.py"
  - "app/*/choices.py"
---

# Models & choices

Conventions for Django model and choices modules. Match the existing shape rather than inventing a new one.

## Models

- Subclass `app.core.models.TimestampedMixin` to inherit `created_at`/`updated_at` (there is no shared UUID base — declare the PK per model).
- Primary key is an explicit UUID: `id = models.UUIDField(_("..."), primary_key=True, default=uuid.uuid4, editable=False)`.
- First positional arg of every field is a `gettext_lazy as _` verbose name. Use `help_text=_(...)` and `validators=[...]` (`MinLengthValidator`, `Min/MaxValueValidator`) where the domain constrains the value.
- Foreign keys to the user reference `settings.AUTH_USER_MODEL` with an explicit `related_name` and `verbose_name`.
- Choice fields use `max_length=<Choices>.max_length` and `choices=<Choices>.choices` with a `default`.
- Give the class a docstring and a `Meta` (also with a docstring) setting `verbose_name`/`verbose_name_plural` and any `indexes`.
- Type the dunder: `def __str__(self) -> str:`.
- Keep business logic on the model (score/stat computation, `clean()`, side-effecting `save()` overrides that bust caches), not scattered in views.
- End the module with an explicit `__all__`.

Reference: `app/sudoku/models.py`, `app/core/models.py`.

## Choices

- Define enums as `TextChoices` subclasses with `metaclass=ExtendedTextChoicesMeta` (`app/core/choices.py`) so `Choices.max_length` is computed from the values and can feed `max_length=` on the field.
- Members are `NAME = "value", _("Label")`.
- End the module with `__all__`.

Reference: `app/sudoku/choices.py`, `app/game_record/choices.py`.
