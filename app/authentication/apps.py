"""Authentication app configuration."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """App config for the authentication app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app.authentication"
