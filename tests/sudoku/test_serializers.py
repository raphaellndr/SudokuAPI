"""Tests Sudoku serializers."""

import pytest
from sudoku.serializers import (
    AnonymousSudokuSerializer,
    SudokuSerializer,
    SudokuSolutionSerializer,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_serialize_sudoku(request, create_sudoku, user: str | None) -> None:
    """Tests that serializing a sudoku with and without a user works as expected."""
    if user is not None:
        user = request.getfixturevalue(user)()
    sudoku = create_sudoku(user=user)

    if user is not None:
        serializer = SudokuSerializer(sudoku)
    else:
        serializer = AnonymousSudokuSerializer(sudoku)

    assert serializer.data["id"] == str(sudoku.id)
    assert serializer.data["title"] == sudoku.title
    assert serializer.data["difficulty"] == sudoku.difficulty
    assert len(serializer.data["grid"]) == 81
    assert serializer.data["status"] == sudoku.status
    assert serializer.data["task_id"] is None
    assert serializer.data["solution"] is None
    assert serializer.data["created_at"] == sudoku.created_at.isoformat().replace("+00:00", "Z")
    assert serializer.data["updated_at"] == sudoku.updated_at.isoformat().replace("+00:00", "Z")
    if user is not None:
        assert serializer.data["user_id"] == str(user.id)
    else:
        with pytest.raises(KeyError):
            assert serializer.data["user_id"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_serialize_sudoku_solution(
    request, create_sudoku, create_sudoku_solution, user: str | None
) -> None:
    """Tests that serializing a sudoku solution with and without a user works as expected."""
    if user is not None:
        user = request.getfixturevalue(user)()
    sudoku = create_sudoku(user=user)

    sudoku_solution = create_sudoku_solution(sudoku=sudoku)
    serializer = SudokuSolutionSerializer(sudoku_solution)

    assert serializer.data["id"] == str(sudoku_solution.id)
    assert serializer.data["sudoku_id"] == str(sudoku.id)
    assert sudoku_solution.grid
    assert serializer.data["created_at"] == sudoku_solution.created_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert serializer.data["updated_at"] == sudoku_solution.updated_at.isoformat().replace(
        "+00:00", "Z"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_serialize_sudoku_with_solution(
    request, create_sudoku, create_sudoku_solution, user: str | None
) -> None:
    """Tests that serializing a sudoku with a solution works as expected."""
    if user is not None:
        user = request.getfixturevalue(user)()
    sudoku = create_sudoku(user=user)

    sudoku_solution = create_sudoku_solution(sudoku=sudoku)

    if user is not None:
        serializer = SudokuSerializer(sudoku)
    else:
        serializer = AnonymousSudokuSerializer(sudoku)

    assert serializer.data["id"] == str(sudoku.id)
    assert serializer.data["title"] == sudoku.title
    assert serializer.data["difficulty"] == sudoku.difficulty
    assert len(serializer.data["grid"]) == 81
    assert serializer.data["status"] == sudoku.status
    assert serializer.data["task_id"] is None
    assert serializer.data["created_at"] == sudoku.created_at.isoformat().replace("+00:00", "Z")
    assert serializer.data["updated_at"] == sudoku.updated_at.isoformat().replace("+00:00", "Z")

    assert serializer.data["solution"]["id"] == str(sudoku_solution.id)
    assert serializer.data["solution"]["sudoku_id"] == str(sudoku.id)
    assert serializer.data["solution"]["grid"]
    assert serializer.data["solution"][
        "created_at"
    ] == sudoku_solution.created_at.isoformat().replace("+00:00", "Z")
    assert serializer.data["solution"][
        "updated_at"
    ] == sudoku_solution.updated_at.isoformat().replace("+00:00", "Z")
    if user is not None:
        assert serializer.data["user_id"] == str(user.id)
    else:
        with pytest.raises(KeyError):
            assert serializer.data["user_id"]
