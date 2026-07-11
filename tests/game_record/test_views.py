"""Tests for the GameRecord API."""

from django.urls import reverse
from rest_framework import status

from app.game_record.models import GameRecord

GAMES_URL = reverse("game_records:game-records-list")


def _completed_payload(**overrides) -> dict:
    """Builds a valid payload for a completed, won game (without ``completed_at``)."""
    payload = {
        "original_puzzle": "1" * 81,
        "solution": "1" * 81,
        "final_state": "1" * 81,
        "status": "completed",
        "won": True,
        "score": 500,
        "time_taken": 100,
    }
    payload.update(overrides)
    return payload


def test_complete_game_without_completed_at_sets_it(api_client, create_user) -> None:
    """Tests that creating a completed game auto-populates ``completed_at`` (timezone fix)."""
    user = create_user()

    response = api_client(user).post(GAMES_URL, _completed_payload(), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    game = GameRecord.objects.get(user=user)
    assert game.completed_at is not None
