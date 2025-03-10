"""Database models."""

from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimestampedMixin


class _UserManager(BaseUserManager["User"]):
    """Manager for users."""

    def create_user(
        self,
        username: str,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Creates, saves and returns a new user.

        :param username: User username.
        :param email: User email address.
        :param password: User password.
        :param extra_fields: Extra fields to add to the user.
        :return: User object.
        """
        if not email:
            raise ValueError(_("User must have an email address"))

        normalized_email = self.normalize_email(email)
        user: User = self.model(username=username, email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        username: str,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Creates, saves and returns a new superuser.

        :param username: Superuser username.
        :param email: Superuser email address.
        :param password: Superuser password.
        :param extra_fields: Extra fields to add to the superuser.
        :return: User object with priviledges.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampedMixin):
    """User in the system."""

    username = models.CharField(_("username"), max_length=255, blank=True, null=True)
    email = models.EmailField(_("email address"), max_length=255, unique=True)
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)

    objects = _UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        """Meta class for the user model."""

        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        """String representation of the user."""
        return self.email


class Sudoku(TimestampedMixin):
    """Sudoku object."""

    class _DifficultyChoices(models.TextChoices):
        """Sudoku difficulties enum."""

        UNKNOWN = "Unknown", _("Unknown")
        EASY = "Easy", _("Easy")
        MEDIUM = "Medium", _("Medium")
        HARD = "Hard", _("Hard")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # remove every sudoku linked to the user
    )
    title = models.CharField(_("title"), max_length=255)
    difficulty = models.CharField(
        _("difficulty"),
        max_length=10,
        choices=_DifficultyChoices.choices,
        default=_DifficultyChoices.UNKNOWN,
    )
    grid = models.CharField(_("grid"), max_length=81, default="." * 81)

    def __str__(self) -> str:
        return self.title
