"""Settings file for local development."""

from datetime import timedelta

from .base import *  # noqa: F403
from .base import env

# General settings

DEBUG = True

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="!!!SET DJANGO_SECRET_KEY!!!",
)

ALLOWED_HOSTS: list[str] = ["localhost", "0.0.0.0", "127.0.0.1", "192.168.1.160"]


# JWT settings

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "SIGNING_KEY": env(
        "DJANGO_SECRET_KEY",
        default="!!!SET DJANGO_SECRET_KEY!!!",
    ),
    "ALGORITHM": "HS256",
}
