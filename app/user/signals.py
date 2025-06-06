"""User signals."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from app.game_record.models import GameRecord

from .models import User, UserStats


@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs) -> None:
    """Creates UserStats when a new User is created."""
    if created:
        UserStats.objects.get_or_create(user=instance)


@receiver(post_save, sender=GameRecord)
def update_user_stats_on_game_save(sender, instance, **kwargs) -> None:
    """Update user statistics when a game record is saved."""
    stats = UserStats.get_or_create_for_user(instance.user)
    stats.recalculate_from_games()


@receiver(post_delete, sender=GameRecord)
def update_user_stats_on_game_delete(sender, instance, **kwargs) -> None:
    """Update user statistics when a game record is deleted."""
    try:
        stats = UserStats.objects.get(user=instance.user)
        stats.recalculate_from_games()
    except UserStats.DoesNotExist:
        pass
