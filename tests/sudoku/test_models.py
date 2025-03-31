"""Sudoku model tests."""

import pytest
from django.db import IntegrityError
from sudoku.choices import SudokuDifficultyChoices, SudokuStatusChoices
from sudoku.models import Sudoku, SudokuSolution


def test_cannot_create_sudoku_without_user(transactional_db) -> None:
    """Tests that creating a new sudoku without a user is not possible."""
    with pytest.raises(IntegrityError):
        Sudoku.objects.create(title="Test Sudoku")


def test_create_sudoku(create_sudoku) -> None:
    """Tests creating a new sudoku."""
    sudoku = create_sudoku()

    assert sudoku.user
    assert sudoku.title == "sudoku title"
    assert sudoku.difficulty in SudokuDifficultyChoices.values
    assert len(sudoku.grid) == 81
    assert sudoku.status in SudokuStatusChoices.CREATED
    assert str(sudoku) == f"Sudoku {sudoku.id} - Status: {sudoku.status}"


def test_create_sudoku_solution(transactional_db) -> None:
    """Tests that creating a new solution without a sudoku is not possible."""
    with pytest.raises(IntegrityError):
        SudokuSolution.objects.create()


def test_create_sudoku_with_solution(create_sudoku) -> None:
    """Tests creating a new sudoku with a solution.

    Checks that the solution exists and that the related sudoku is the correct one.
    """
    sudoku = create_sudoku()
    solution_grid = "8" * 81
    sudoku_solution = SudokuSolution.objects.create(sudoku=sudoku, grid=solution_grid)

    assert sudoku.solution.grid == solution_grid
    assert sudoku_solution.sudoku.id == sudoku.id
    assert str(sudoku_solution) == f"Solution for Sudoku {sudoku.id}"
