"""Core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """App config for the core app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app.core"
