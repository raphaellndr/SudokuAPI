"""Tests Sudoku views that don't require authentication."""

from typing import Final

from django.urls import reverse
from rest_framework import status

SUDOKU_URL: Final[str] = reverse("sudokus:sudoku-list")


def test_create_sudoku_is_unauthorized(api_client, sudoku_payload) -> None:
    """Tests creating a sudoku without being authenticated."""
    response = api_client().post(SUDOKU_URL, sudoku_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_sudokus_is_unauthorized(api_client) -> None:
    """Tests retrieving sudokus without being authenticated."""
    response = api_client().get(SUDOKU_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
