"""Tests sudoku's URLs."""

from django.urls import resolve, reverse


def test_sudokus_url() -> None:
    """Tests that sudokus' URL and view name are correct."""
    url = reverse("sudoku:sudoku-list")

    assert url == "/api/sudoku/sudokus/"
    assert resolve(url).view_name == "sudoku:sudoku-list"
