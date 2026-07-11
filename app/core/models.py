"""Base models."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedMixin(models.Model):
    """Abstract model adding self-managed `created_at`/`updated_at` timestamps."""

    created_at = models.DateTimeField(_("date joined"), auto_now_add=True)
    updated_at = models.DateTimeField(_("last update"), auto_now=True)

    class Meta:
        """Meta options for the timestamped mixin."""

        abstract = True


__all__ = ["TimestampedMixin"]
