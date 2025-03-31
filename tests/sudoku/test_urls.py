"""Tests sudoku's URLs."""

import uuid

from django.urls import resolve, reverse


def test_sudokus_url() -> None:
    """Tests that sudokus' URL and view name are correct."""
    url = reverse("sudokus:sudoku-list")

    assert url == "/api/sudokus/"
    assert resolve(url).view_name == "sudokus:sudoku-list"


def test_sudoku_detail_url() -> None:
    """Tests that sudoku's detail URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudokus:sudoku-detail", kwargs={"pk": pk})

    assert url == f"/api/sudokus/{pk}/"
    assert resolve(url).view_name == "sudokus:sudoku-detail"


def test_sudoku_solution_url() -> None:
    """Tests that sudoku's solution URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudokus:sudoku-solution", kwargs={"pk": pk})

    assert url == f"/api/sudokus/{pk}/solution/"
    assert resolve(url).view_name == "sudokus:sudoku-solution"


def test_sudoku_status_url() -> None:
    """Tests that sudoku's status URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudokus:sudoku-status", kwargs={"pk": pk})

    assert url == f"/api/sudokus/{pk}/status/"
    assert resolve(url).view_name == "sudokus:sudoku-status"
