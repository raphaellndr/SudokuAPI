"""Game record model for tracking user game sessions."""

import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from app.core.models import TimestampedMixin
from app.game_record.choices import GameStatusChoices
from app.sudoku.models import Sudoku


class GameRecord(TimestampedMixin):
    """Records a game session."""

    id = models.UUIDField(
        _("game record identifier"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_records",
        verbose_name=_("player"),
    )
    sudoku = models.ForeignKey(
        Sudoku,
        on_delete=models.SET_NULL,
        related_name="game_records",
        verbose_name=_("original sudoku"),
        null=True,
        blank=True,
    )

    # Game statistics
    score = models.IntegerField(
        _("score"),
        default=0,
        validators=[
            MinValueValidator(0, _("Score cannot be negative")),
            MaxValueValidator(1000, _("Score cannot exceed 1000")),
        ],
        help_text=_("Score achieved in the game, based on performance"),
    )
    hints_used = models.IntegerField(
        _("hints used"),
        default=0,
        validators=[
            MinValueValidator(0, _("Hints used cannot be negative")),
            MaxValueValidator(3, _("Hints used cannot exceed 3")),
        ],
        help_text=_("Number of hints used during the game"),
    )
    checks_used = models.IntegerField(
        _("checks used"),
        default=0,
        validators=[
            MinValueValidator(0, _("Checks used cannot be negative")),
            MaxValueValidator(3, _("Checks used cannot exceed 3")),
        ],
        help_text=_("Number of checks used during the game"),
    )
    deletions = models.IntegerField(
        _("deletions"),
        default=0,
        validators=[
            MinValueValidator(0, _("Deletions made cannot be negative")),
        ],
        help_text=_("Amount of times a user deleted a cell during the game"),
    )
    time_taken = models.DurationField(
        _("time taken"),
        help_text=_("Total time taken to complete the game"),
    )
    won = models.BooleanField(
        _("won"),
        default=False,
        help_text=_("Indicates if the player won the game"),
    )

    # Game metadata
    status = models.CharField(
        _("status"),
        max_length=GameStatusChoices.max_length,
        choices=GameStatusChoices.choices,
        default=GameStatusChoices.IN_PROGRESS,
    )
    original_puzzle = models.CharField(
        _("original puzzle"),
        max_length=81,
        validators=[
            MinLengthValidator(81, _("Puzzle must be exactly 81 characters")),
            MaxLengthValidator(81, _("Puzzle must be exactly 81 characters")),
        ],
        help_text=_("The initial puzzle state"),
    )
    solution = models.CharField(
        _("solution"),
        max_length=81,
        validators=[
            MinLengthValidator(81, _("Puzzle must be exactly 81 characters")),
            MaxLengthValidator(81, _("Puzzle must be exactly 81 characters")),
        ],
        help_text=_("The solution to the Sudoku puzzle"),
    )
    final_state = models.CharField(
        _("final state"),
        max_length=81,
        validators=[
            MinLengthValidator(81, _("Puzzle must be exactly 81 characters")),
            MaxLengthValidator(81, _("Puzzle must be exactly 81 characters")),
        ],
        help_text=_("Player's final state"),
    )

    # Timestamps
    started_at = models.DateTimeField(
        _("started at"),
        help_text=_("Timestamp when the game started"),
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(
        _("completed at"),
        help_text=_("Timestamp when the game finished"),
        null=True,
        blank=True,
    )

    class Meta:
        """Meta class for the GameRecord model."""

        verbose_name = _("game record")
        verbose_name_plural = _("game records")
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "won"]),
            models.Index(fields=["score"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """String representation of the game record."""
        return f"Game Record {self.id} - User: {self.user.email} - Status: {self.status}"

    def calculate_score(self) -> int:
        """Calculates the score based on game performance.

        The score is calculated as follows:
        - Base score of 1000.
        - Subtract 100 for each hint used.
        - Subtract 50 for each check used.
        - Subtract 5 for each deletion made.
        - Subtract 15 points for each minute taken to complete the game.
        - If the game is not completed or lost, return 0.

        :return: Calculated score.
        """
        if not self.status == GameStatusChoices.COMPLETED or not self.won:
            return 0

        base_score = 1000
        hints_penalty = self.hints_used * 100
        checks_penalty = self.checks_used * 50
        deletions_penalty = self.deletions * 5
        time_penalty = int(self.time_taken.total_seconds() // 60) * 15

        score = base_score - hints_penalty - checks_penalty - deletions_penalty - time_penalty
        return max(score, 0)

    def clean(self):
        super().clean()

        expected_score = self.calculate_score()
        if self.score != expected_score:
            raise ValidationError(
                _("Score does not match the calculated score based on game performance.")
            )

    def save(self, *args, **kwargs):
        """Overrides save method to compute score before saving."""
        if self.status == GameStatusChoices.COMPLETED:
            self.score = self.calculate_score()

        # Clear user stats cache when game record is saved
        cache.delete(f"user_stats_{self.user.id}")
        cache.delete("leaderboard")

        self.full_clean()
        super().save(*args, **kwargs)


__all__ = ["GameRecord"]
