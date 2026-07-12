import pytest
from celery.exceptions import SoftTimeLimitExceeded

from app.sudoku.choices import SudokuStatusChoices
from app.sudoku.models import Sudoku
from app.sudoku.tasks import solve_sudoku


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SoftTimeLimitExceeded, "Solving timed out"),
        (RuntimeError, "Solving failed"),
    ],
)
def test_solve_sudoku_failure_sets_terminal_status(
    transactional_db,
    monkeypatch,
    create_sudoku,
    side_effect: type[Exception],
    expected_error: str,
) -> None:
    sudoku = create_sudoku(grid="1" + "0" * 80)

    def fake_update_status(sudoku: Sudoku, status: SudokuStatusChoices) -> None:
        sudoku.status = status
        sudoku.save(update_fields=["status"])

    monkeypatch.setattr("app.sudoku.tasks.update_sudoku_status", fake_update_status)

    def raising_solve(self) -> None:
        raise side_effect

    monkeypatch.setattr("app.sudoku.tasks.SudokuResolver.solve", raising_solve)

    result = solve_sudoku(str(sudoku.id))

    assert result == {"status": "failed", "error": expected_error}
    sudoku.refresh_from_db()
    assert sudoku.status == SudokuStatusChoices.FAILED
