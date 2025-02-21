"""Database models."""

from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager["User"]):
    """Manager for users."""

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        """Creates, saves and returns a new user.

        :param email: User email address.
        :param password: User password.
        :param extra_fields: Extra fields to add to the user.
        :return: User object.
        """
        if not email:
            raise ValueError(_("User must have an email address"))

        normalized_email = self.normalize_email(email)
        user: User = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> "User":
        """Creates, saves and returns a new superuser.

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

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    email = models.EmailField(_("email address"), max_length=255, unique=True)
    name = models.CharField(_("name"), max_length=255, blank=True)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        """Meta class for the user model."""

        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        """String representation of the user."""
        return self.email


class Sudoku(models.Model):
    """Sudoku object."""

    class _DifficultyChoices(models.TextChoices):
        """Sudoku difficulties enum."""

        UNKNOWN = "UNKNOWN", _("Unknown")
        EASY = "EASY", _("Easy")
        MEDIUM = "MEDIUM", _("Medium")
        HARD = "HARD", _("Hard")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # remove every sudoku linked to the user
    )
    title = models.CharField(max_length=255)
    difficulty = models.CharField(
        max_length=10,
        choices=_DifficultyChoices.choices,
        default=_DifficultyChoices.UNKNOWN,
    )
    grid = models.CharField(max_length=81, default="." * 81)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title
