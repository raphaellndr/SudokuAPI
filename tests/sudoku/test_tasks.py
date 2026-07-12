from uuid import uuid4

import pytest
from celery.exceptions import SoftTimeLimitExceeded

from app.sudoku.choices import DetectionStatusChoices, SudokuStatusChoices
from app.sudoku.models import Sudoku
from app.sudoku.tasks import detect_sudoku_digits, solve_sudoku


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


def test_detect_sudoku_digits_decode_failure_broadcasts_failed(monkeypatch) -> None:
    """Tests that an undecodable image fails and broadcasts the failure to the session."""
    calls = []
    monkeypatch.setattr(
        "app.sudoku.tasks.update_sudoku_detection",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    session_id = str(uuid4())
    result = detect_sudoku_digits(b"not-an-image", session_id)

    assert result == {"status": "error", "message": "Failed to decode image"}
    assert calls == [
        ((session_id, DetectionStatusChoices.RUNNING), {}),
        ((session_id, DetectionStatusChoices.FAILED), {"message": "Failed to decode image"}),
    ]
