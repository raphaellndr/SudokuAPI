"""Sudoku related tasks."""

from copy import copy
from typing import Any

from sudoku_resolver.exceptions import ConsistencyError
from sudoku_resolver.sudoku import Sudoku as SudokuResolver

from app.celery import app

from .choices import SudokuStatusChoices
from .models import Sudoku, SudokuSolution


def _update_sudoku_status(sudoku_id: str, status: SudokuStatusChoices) -> None:
    """Updates the status of a Sudoku."""
    Sudoku.objects.filter(id=sudoku_id).update(status=status)


def _update_sudoku_solution(
    sudoku_id: str, solution: SudokuSolution, status: SudokuStatusChoices
) -> None:
    """Updates the solution and status of a Sudoku."""
    Sudoku.objects.filter(id=sudoku_id).update(solution=solution, status=status)


@app.task
def solve_sudoku(sudoku_id: str) -> dict[str, Any]:
    """Celery task to solve a Sudoku."""
    try:
        sudoku = Sudoku.objects.get(id=sudoku_id)

        Sudoku.objects.filter(id=sudoku_id).update(status=SudokuStatusChoices.RUNNING)

        grid = copy(sudoku.grid)
        sudoku_solver = SudokuResolver(grid)
        sudoku_solver.solve()

        try:
            sudoku_solver.check_consistency()
        except ConsistencyError:
            _update_sudoku_status(
                sudoku_id,
                SudokuStatusChoices.INVALID,
            )
            return {"status": "failed", "error": "Inconsistent Sudoku solution"}

        solution_grid = SudokuResolver.to_string()
        solution = SudokuSolution.objects.create(sudoku=sudoku, grid=solution_grid)
        _update_sudoku_solution(
            sudoku_id,
            solution,
            SudokuStatusChoices.COMPLETED,
        )
        return {"status": "completed", "solution": solution.id}

    except Exception as e:
        _update_sudoku_status(
            sudoku_id,
            SudokuStatusChoices.FAILED,
        )
        return {"status": "failed", "error": str(e)}


__all__ = ["solve_sudoku"]
