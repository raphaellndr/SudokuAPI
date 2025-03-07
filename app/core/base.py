"""Base models."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedMixin(models.Model):
    created_at = models.DateTimeField(_("date joined"), auto_now_add=True)
    updated_at = models.DateTimeField(_("last update"), auto_now=True)
    deleted_at = models.DateTimeField(_("date deleted"), null=True)

    class Meta:
        abstract = True


__all__ = ["TimestampedMixin"]
