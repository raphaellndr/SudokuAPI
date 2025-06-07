"""Celery tasks for periodic stats updates."""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from app.user.models import UserStats

logger = logging.getLogger(__name__)


@shared_task
def refresh_all_user_stats():
    """Periodic task to refresh all user stats - run daily via celery beat."""
    logger.info("Starting periodic refresh of all user stats")

    # Get all user stats that haven't been updated in the last 23 hours
    # This prevents unnecessary recalculations if stats were recently updated
    cutoff_time = timezone.now() - timedelta(hours=23)
    stale_stats = UserStats.objects.filter(updated_at__lt=cutoff_time).select_related("user")

    updated_count = 0
    for user_stats in stale_stats:
        try:
            user_stats.recalculate_from_games()
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to refresh stats for user {user_stats.user.id}: {e}")

    logger.info(f"Refreshed stats for {updated_count} users")
    return f"Refreshed {updated_count} user stats"


@shared_task
def refresh_user_stats(user_id):
    """Task to refresh a specific user's stats."""
    try:
        user_stats = UserStats.objects.select_related("user").get(user_id=user_id)
        user_stats.recalculate_from_games()
        logger.info(f"Refreshed stats for user {user_id}")
        return f"Refreshed stats for user {user_id}"
    except UserStats.DoesNotExist:
        logger.error(f"UserStats not found for user {user_id}")
        raise
    except Exception as e:
        logger.error(f"Failed to refresh stats for user {user_id}: {e}")
        raise
