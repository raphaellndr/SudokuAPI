"""Game record app configuration."""

from django.apps import AppConfig


class GameRecordConfig(AppConfig):
    """App config for the game record app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app.game_record"
