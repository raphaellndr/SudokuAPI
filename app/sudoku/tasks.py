"""Sudoku related tasks."""

from copy import copy
from datetime import timedelta
from typing import Any

from django.utils import timezone
from sudoku_resolver.exceptions import ConsistencyError
from sudoku_resolver.sudoku import Sudoku as SudokuResolver

from app.celery import app

from .base import update_sudoku_status
from .choices import SudokuStatusChoices
from .models import Sudoku, SudokuSolution


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
    :returns: A dictionary with the status and solution id if successful.
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


@app.task
def cleanup_anonymous_sudokus(hours: int = 24) -> str:
    """Celery task to clean up anonymous Sudokus older than a certain number of hours.

    :param hours: The number of hours to keep anonymous Sudokus.
    :returns: A message indicating the number of deleted Sudokus.
    """
    cutoff_time = timezone.now() - timedelta(hours=hours)

    old_anonymous_sudokus = Sudoku.objects.filter(user__isnull=True, created_at__lt=cutoff_time)
    count = old_anonymous_sudokus.count()
    old_anonymous_sudokus.delete()

    return f"Deleted {count} anonymous Sudokus older than {hours} hours."


__all__ = ["cleanup_anonymous_sudokus", "solve_sudoku"]
