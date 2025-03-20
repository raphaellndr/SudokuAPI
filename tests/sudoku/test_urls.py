"""Tests sudoku's URLs."""

import uuid

from django.urls import resolve, reverse


def test_sudokus_url() -> None:
    """Tests that sudokus' URL and view name are correct."""
    url = reverse("sudoku:sudoku-list")

    assert url == "/api/sudoku/sudokus/"
    assert resolve(url).view_name == "sudoku:sudoku-list"


def test_sudoku_detail_url() -> None:
    """Tests that sudoku's detail URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudoku:sudoku-detail", kwargs={"pk": pk})

    assert url == f"/api/sudoku/sudokus/{pk}/"
    assert resolve(url).view_name == "sudoku:sudoku-detail"


def test_sudoku_solution_url() -> None:
    """Tests that sudoku's solution URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudoku:sudoku-solution", kwargs={"pk": pk})

    assert url == f"/api/sudoku/sudokus/{pk}/solution/"
    assert resolve(url).view_name == "sudoku:sudoku-solution"


def test_sudoku_abort_url() -> None:
    """Tests that sudoku's abort URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudoku:sudoku-abort", kwargs={"pk": pk})

    assert url == f"/api/sudoku/sudokus/{pk}/abort/"
    assert resolve(url).view_name == "sudoku:sudoku-abort"


def test_sudoku_status_url() -> None:
    """Tests that sudoku's status URL and view name are correct."""
    pk = uuid.uuid4()
    url = reverse("sudoku:sudoku-status", kwargs={"pk": pk})

    assert url == f"/api/sudoku/sudokus/{pk}/status/"
    assert resolve(url).view_name == "sudoku:sudoku-status"
