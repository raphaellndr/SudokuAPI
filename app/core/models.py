"""Database models."""

from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(
        self, email: str, password: str | None = None, **extra_fields
    ) -> AbstractBaseUser:
        """Create, save and return a new user"""
        if not email:
            raise ValueError("User must have an email address")

        user: User = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str) -> "User":
        """Create, save and return a new superuser"""
        if not email:
            raise ValueError("Superuser must have an email address")

        user: User = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Login with Django admin or not

    objects = UserManager()

    USERNAME_FIELD = "email"


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

    def __str__(self) -> str:
        return self.title
