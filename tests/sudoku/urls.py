"""URLs used in Sudoku tests."""

from typing import Final
from uuid import UUID

from django.urls import reverse

SUDOKUS_URL: Final[str] = reverse("sudokus:sudoku-list")


def sudoku_url(sudoku_id: UUID, /) -> str:
    """Returns the URL for a sudoku.

    :param sudoku_id: The id of the Sudoku.
    :return: The URL for solving the sudoku.
    """
    return reverse("sudokus:sudoku-detail", kwargs={"pk": sudoku_id})


def solution_url(sudoku_id: UUID, /) -> str:
    """Returns the URL for a sudoku solution.

    :param sudoku_id: The id of the Sudoku.
    :return: The URL for the sudoku solution.
    """
    return reverse("sudokus:sudoku-solution", kwargs={"pk": sudoku_id})


def solver_url(sudoku_id: UUID, /) -> str:
    """Returns the URL for a sudoku solver.

    :param sudoku_id: The id of the Sudoku.
    :return: The URL for the sudoku solver.
    """
    return reverse("sudokus:sudoku-solver", kwargs={"pk": sudoku_id})


__all__ = ["SUDOKUS_URL", "solution_url", "sudoku_url"]
