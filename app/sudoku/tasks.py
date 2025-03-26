"""Sudoku related tasks."""

from copy import copy
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from sudoku_resolver.exceptions import ConsistencyError
from sudoku_resolver.sudoku import Sudoku as SudokuResolver

from app.celery import app

from .choices import SudokuStatusChoices
from .models import Sudoku, SudokuSolution


def update_sudoku_status(sudoku: Sudoku, status: SudokuStatusChoices) -> None:
    """Updates the status of a Sudoku.

    Also sends status update via WebSocket.

    :param sudoku: udoku to update.
    :param status: new status for the Sudoku to update.
    """
    sudoku.status = status
    sudoku.save(update_fields=["status"])

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"sudoku_status_{sudoku.user.id}",
        {
            "type": "status_update",
            "sudoku_id": sudoku.id,
            "status": status,
        },
    )


def _check_consistency(sudoku_solver: SudokuResolver, /) -> bool:
    """Checks if a sudoku is consistent or not.

    :param sudoku_solver: Sudoku to check.
    :returns: True if sudoku is consistent, False otherwise.
    """
    try:
        sudoku_solver.check_consistency()
        return True
    except ConsistencyError:
        return False


@app.task
def solve_sudoku(sudoku_id: str) -> dict[str, Any]:
    """Celery task to solve a Sudoku.

    :param sudoku_id: The id of the Sudoku to solve.
    """
    try:
        sudoku = Sudoku.objects.get(id=sudoku_id)
        update_sudoku_status(sudoku, SudokuStatusChoices.RUNNING)

        grid = copy(sudoku.grid)
        sudoku_solver = SudokuResolver(values=grid)

        is_consistent = _check_consistency(sudoku_solver)
        if not is_consistent:
            update_sudoku_status(sudoku, SudokuStatusChoices.INVALID)
            return {"status": "failed", "error": "Inconsistent Sudoku"}

        sudoku_solver.solve()

        is_consistent = _check_consistency(sudoku_solver)
        if not is_consistent:
            update_sudoku_status(sudoku, SudokuStatusChoices.INVALID)
            return {"status": "failed", "error": "Inconsistent Sudoku solution"}

        solution_grid = sudoku_solver.to_string()
        SudokuSolution.objects.create(sudoku=sudoku, grid=solution_grid)
        update_sudoku_status(sudoku, SudokuStatusChoices.COMPLETED)

        return {"status": "completed", "solution": sudoku.solution.id}

    except Exception as e:
        update_sudoku_status(sudoku, SudokuStatusChoices.FAILED)
        return {"status": "failed", "error": str(e)}


__all__ = ["solve_sudoku", "update_sudoku_status"]
