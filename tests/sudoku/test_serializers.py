from sudoku.models import SudokuSolution
from sudoku.serializers import SudokuSerializer, SudokuSolutionSerializer


def test_serialize_sudoku(create_user, create_sudoku) -> None:
    """Tests that serializing a sudoku works as expected."""
    user = create_user()
    sudoku = create_sudoku(user=user)
    serializer = SudokuSerializer(sudoku)

    assert serializer.data["id"] == str(sudoku.id)
    assert serializer.data["user_id"] == str(user.id)
    assert serializer.data["title"] == sudoku.title
    assert serializer.data["difficulty"] == sudoku.difficulty
    assert len(serializer.data["grid"]) == 81
    assert serializer.data["status"] == sudoku.status
    assert serializer.data["task_id"] is None
    assert serializer.data["solution"] is None
    assert serializer.data["created_at"] == sudoku.created_at.isoformat().replace("+00:00", "Z")
    assert serializer.data["updated_at"] == sudoku.updated_at.isoformat().replace("+00:00", "Z")


def test_serialize_sudoku_solution(create_user, create_sudoku) -> None:
    """Tests that serializing a sudoku solution works as expected."""
    user = create_user()
    sudoku = create_sudoku(user=user)
    solution_grid = "8" * 81
    sudoku_solution = SudokuSolution.objects.create(sudoku=sudoku, grid=solution_grid)
    serializer = SudokuSolutionSerializer(sudoku_solution)

    assert serializer.data["id"] == str(sudoku_solution.id)
    assert serializer.data["sudoku_id"] == str(sudoku.id)
    assert serializer.data["grid"] == solution_grid
    assert serializer.data["created_at"] == sudoku_solution.created_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert serializer.data["updated_at"] == sudoku_solution.updated_at.isoformat().replace(
        "+00:00", "Z"
    )


def test_serialize_sudoku_with_solution(create_user, create_sudoku) -> None:
    """Tests that serializing a sudoku with a solution works as expected."""
    user = create_user()
    sudoku = create_sudoku(user=user)
    solution_grid = "8" * 81
    sudoku_solution = SudokuSolution.objects.create(sudoku=sudoku, grid=solution_grid)
    serializer = SudokuSerializer(sudoku)

    assert serializer.data["id"] == str(sudoku.id)
    assert serializer.data["user_id"] == str(user.id)
    assert serializer.data["title"] == sudoku.title
    assert serializer.data["difficulty"] == sudoku.difficulty
    assert len(serializer.data["grid"]) == 81
    assert serializer.data["status"] == sudoku.status
    assert serializer.data["task_id"] is None
    assert serializer.data["created_at"] == sudoku.created_at.isoformat().replace("+00:00", "Z")
    assert serializer.data["updated_at"] == sudoku.updated_at.isoformat().replace("+00:00", "Z")

    assert serializer.data["solution"]["id"] == str(sudoku_solution.id)
    assert serializer.data["solution"]["sudoku_id"] == str(sudoku.id)
    assert serializer.data["solution"]["grid"] == solution_grid
    assert serializer.data["solution"][
        "created_at"
    ] == sudoku_solution.created_at.isoformat().replace("+00:00", "Z")
    assert serializer.data["solution"][
        "updated_at"
    ] == sudoku_solution.updated_at.isoformat().replace("+00:00", "Z")
