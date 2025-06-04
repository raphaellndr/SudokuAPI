"""User models."""

import uuid
from datetime import date
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.core.base import TimestampedMixin


class _UserManager(BaseUserManager["User"]):
    """Manager for users."""

    def create_user(
        self,
        username: str,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Creates, saves and returns a new `User`.

        :param username: User username.
        :param email: User email address.
        :param password: User password.
        :param extra_fields: Extra fields to add to the user.
        :return: `User`.
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
        :return: `User` with priviledges.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampedMixin):
    """Model to store users and their information."""

    id = models.UUIDField(
        _("user identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
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


class UserStats(TimestampedMixin):
    """Model to store user game statistics (aggregated)."""

    id = models.UUIDField(
        _("user stats identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="stats", verbose_name=_("user")
    )
    games_played = models.PositiveIntegerField(_("games played"), default=0)
    games_won = models.PositiveIntegerField(_("games won"), default=0)
    games_lost = models.PositiveIntegerField(_("games lost"), default=0)
    total_time_seconds = models.PositiveIntegerField(_("total time in seconds"), default=0)
    best_time_seconds = models.PositiveIntegerField(
        _("best time in seconds"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("user statistics")
        verbose_name_plural = _("user statistics")

    def __str__(self) -> str:
        return f"Stats for {self.user.email}"

    @property
    def win_rate(self) -> float:
        """Calculates win rate as percentage."""
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100

    @property
    def average_time_seconds(self) -> float:
        """Calculates average time per game."""
        if self.games_played == 0:
            return 0.0
        return self.total_time_seconds / self.games_played

    def update_from_daily_stats(self) -> None:
        """Update aggregated stats from daily stats."""
        daily_stats = self.user.daily_stats.all()

        self.games_played = sum(ds.games_played for ds in daily_stats)
        self.games_won = sum(ds.games_won for ds in daily_stats)
        self.games_lost = sum(ds.games_lost for ds in daily_stats)
        self.total_time_seconds = sum(ds.total_time_seconds for ds in daily_stats)

        # Get best time across all days
        best_times = [ds.best_time_seconds for ds in daily_stats if ds.best_time_seconds]
        self.best_time_seconds = min(best_times) if best_times else None

        self.save()


class DailyUserStats(TimestampedMixin):
    """Model to store daily user game statistics."""

    id = models.UUIDField(
        _("daily stats identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_stats", verbose_name=_("user")
    )
    date = models.DateField(_("date"), default=date.today)
    games_played = models.PositiveIntegerField(_("games played"), default=0)
    games_won = models.PositiveIntegerField(_("games won"), default=0)
    games_lost = models.PositiveIntegerField(_("games lost"), default=0)
    total_time_seconds = models.PositiveIntegerField(_("total time in seconds"), default=0)
    best_time_seconds = models.PositiveIntegerField(
        _("best time in seconds"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("daily user statistics")
        verbose_name_plural = _("daily user statistics")
        unique_together = ["user", "date"]  # One record per user per day
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"Stats for {self.user.email} on {self.date}"

    @property
    def win_rate(self) -> float:
        """Calculates win rate as percentage."""
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100

    @property
    def average_time_seconds(self) -> float:
        """Calculates average time per game."""
        if self.games_played == 0:
            return 0.0
        return self.total_time_seconds / self.games_played

    @classmethod
    def get_or_create_today(cls, user: User) -> "DailyUserStats":
        """Get or create today's stats for a user."""
        today = date.today()
        daily_stats, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                "games_played": 0,
                "games_won": 0,
                "games_lost": 0,
                "total_time_seconds": 0,
            },
        )
        return daily_stats

    def record_game(self, won: bool, time_seconds: int) -> None:
        """Record a game result for this day."""
        self.games_played += 1
        if won:
            self.games_won += 1
        else:
            self.games_lost += 1

        self.total_time_seconds += time_seconds

        # Update best time if this is better
        if self.best_time_seconds is None or time_seconds < self.best_time_seconds:
            self.best_time_seconds = time_seconds

        self.save()


__all__ = ["DailyUserStats", "User", "UserStats"]
