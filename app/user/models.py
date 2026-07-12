"""User models."""

import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.core.models import TimestampedMixin


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
    """Model to store user statistics for caching purposes."""

    id = models.UUIDField(
        _("user stats identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="stats",
        verbose_name=_("user"),
    )

    # Game counts
    total_games = models.IntegerField(
        _("total games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games played by the user."),
    )
    completed_games = models.IntegerField(
        _("completed games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games completed by the user."),
    )
    abandoned_games = models.IntegerField(
        _("abandoned games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games abandoned by the user."),
    )
    stopped_games = models.IntegerField(
        _("stopped games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games stopped by the user."),
    )
    in_progress_games = models.IntegerField(
        _("in progress games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games in progress."),
    )
    won_games = models.IntegerField(
        _("won games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games won by the user."),
    )
    lost_games = models.IntegerField(
        _("lost games"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of games lost by the user."),
    )

    # Performance metrics
    win_rate = models.FloatField(
        _("win rate"),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text=_("Player's win rate."),
    )
    total_time_seconds = models.IntegerField(
        _("total time (seconds)"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total time spent by the user across all games in seconds."),
    )
    average_time_seconds = models.FloatField(
        _("average time (seconds)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text=_("Average time spent by the user across all games in seconds."),
    )
    best_time_seconds = models.IntegerField(
        _("best time (seconds)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Best time spent by the user across all games in seconds."),
    )
    total_score = models.IntegerField(
        _("total score"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total score achieved by the user across all games."),
    )
    average_score = models.FloatField(
        _("average score"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text=_("Average score achieved by the user across all games."),
    )
    best_score = models.IntegerField(
        _("best score"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Best score achieved by the user across all games."),
    )

    # Game interaction metrics
    total_hints_used = models.IntegerField(
        _("total hints used"),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text=_("Total number of hints used by the user across all games."),
    )
    total_checks_used = models.IntegerField(
        _("total checks used"),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text=_("Total number of checks used by the user across all games."),
    )
    total_deletions = models.IntegerField(
        _("total deletions"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Total number of deletions made by the user across all games."),
    )

    class Meta:
        """Meta class for the UserStats model."""

        verbose_name = _("user stats")
        verbose_name_plural = _("user stats")
        indexes = [
            # Backs the leaderboard ordering (see UserStatsViewSet.leaderboard).
            models.Index(fields=["-total_score", "-best_score"]),
        ]

    def recalculate_from_games(self) -> None:
        """Recalculates all statistics from the user's game records."""
        # Local import to avoid a circular import between the user and game_record models.
        from app.game_record.models import GameRecord  # noqa: PLC0415

        stats = GameRecord.objects.filter(user=self.user).aggregate_stats()
        for field, value in stats.items():
            setattr(self, field, value)

        self.save(update_fields=[*stats, "updated_at"])

    @classmethod
    def get_or_create_for_user(cls, user: User) -> "UserStats":
        """Gets or creates UserStats for a user."""
        stats, created = cls.objects.get_or_create(user=user)
        if created:
            stats.recalculate_from_games()
        return stats


__all__ = ["User", "UserStats"]
