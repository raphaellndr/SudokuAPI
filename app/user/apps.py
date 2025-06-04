"""User app configuration."""

from django.apps import AppConfig


class UserConfig(AppConfig):
    """User app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app.user"

    def ready(self):
        """Import signals when app is ready."""
        import app.user.signals  # noqa
