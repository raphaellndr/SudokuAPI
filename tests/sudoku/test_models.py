"""Tests Sudoku models for both authenticated and anonymous users."""

import pytest
from django.db import IntegrityError
from sudoku.choices import SudokuDifficultyChoices, SudokuStatusChoices
from sudoku.models import SudokuSolution


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_create_sudoku(request, create_sudoku, user: str | None) -> None:
    """Tests that creating a new sudoku is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    sudoku = create_sudoku(user=user)

    assert sudoku.user == user
    assert sudoku.title == "sudoku title"
    assert sudoku.difficulty in SudokuDifficultyChoices.values
    assert sudoku.grid
    assert sudoku.status in SudokuStatusChoices.CREATED
    assert str(sudoku) == f"Sudoku {sudoku.id} - Status: {sudoku.status}"


@pytest.mark.django_db
def test_create_sudoku_solution_without_sudoku(create_sudoku_solution) -> None:
    """Tests that creating a new solution without a sudoku is not possible."""
    with pytest.raises(IntegrityError):
        create_sudoku_solution(sudoku=None)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_create_sudoku_with_solution(
    request, create_sudoku, create_sudoku_solution, user: str | None
) -> None:
    """Tests creating a new sudoku with a solution is successful.

    Checks that the solution exists and that the related sudoku is the correct one.
    """
    if user is not None:
        user = request.getfixturevalue(user)()
    sudoku = create_sudoku(user=user)

    sudoku_solution = create_sudoku_solution(sudoku=sudoku)

    assert sudoku.solution.grid
    assert sudoku_solution.sudoku.id == sudoku.id
    assert str(sudoku_solution) == f"Solution for Sudoku {sudoku.id}"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_create_sudoku_with_two_solution(
    request, create_sudoku, create_sudoku_solution, user
) -> None:
    """Tests that creating a new sudoku with more than one solution is not possible."""
    if user is not None:
        user = request.getfixturevalue(user)()
    sudoku = create_sudoku(user=user)

    create_sudoku_solution(sudoku=sudoku)

    with pytest.raises(IntegrityError):
        SudokuSolution.objects.create(sudoku=sudoku)
