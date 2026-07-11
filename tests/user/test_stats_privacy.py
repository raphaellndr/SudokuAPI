"""Tests for user stats/game-history visibility and the leaderboard payload."""

from django.urls import reverse
from rest_framework import status

from app.game_record.models import GameRecord
from app.user.models import UserStats

LEADERBOARD_URL = reverse("users:stats-leaderboard")


def _create_game(user, **overrides) -> GameRecord:
    """Creates a minimal in-progress game record for a user."""
    defaults = {
        "user": user,
        "original_puzzle": "1" * 81,
        "solution": "1" * 81,
        "final_state": "1" * 81,
        "time_taken": 100,
    }
    defaults.update(overrides)
    return GameRecord.objects.create(**defaults)


def test_leaderboard_excludes_email(api_client, create_user) -> None:
    """Tests that the public leaderboard never exposes user emails."""
    user = create_user()
    _create_game(user)
    UserStats.get_or_create_for_user(user).recalculate_from_games()

    response = api_client().get(LEADERBOARD_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    entry = response.data["results"][0]
    assert "email" not in entry
    assert entry["username"] == user.username


def test_user_games_forbidden_for_non_owner(api_client, create_user) -> None:
    """Tests that a user cannot read another user's game history."""
    owner = create_user()
    other = create_user()
    _create_game(owner)

    url = reverse("users:user-games", kwargs={"pk": owner.id})
    response = api_client(other).get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_games_allowed_for_owner(api_client, create_user) -> None:
    """Tests that a user can read their own game history."""
    owner = create_user()
    _create_game(owner)

    url = reverse("users:user-games", kwargs={"pk": owner.id})
    response = api_client(owner).get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
