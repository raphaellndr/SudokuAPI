"""Sudoku related tasks."""

import asyncio
import os
from copy import copy
from typing import Any

import django
from asgiref.sync import sync_to_async

from .choices import SudokuStatusChoices
from .config import REDIS_SETTINGS
from .models import Sudoku

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()


def _update_sudoku_status(sudoku_id: str, status: SudokuStatusChoices) -> None:
    """Updates the status of a Sudoku."""
    Sudoku.objects.filter(id=sudoku_id).update(status=status)


def _update_sudoku_solution(sudoku_id: str, solution: str, status: SudokuStatusChoices) -> None:
    """Updates the solution and status of a Sudoku."""
    Sudoku.objects.filter(id=sudoku_id).update(solution=solution, status=status)


async def solve_sudoku(ctx: Any, sudoku_id: str) -> dict[str, Any]:
    """Asynchronous function to solve a Sudoku."""
    # Fetch sudoku from database. Use `sync_to_async` to make a synchronous call
    sudoku = await sync_to_async(Sudoku.objects.get)(id=sudoku_id)

    # Store ARQ job id and update status
    job_id = str(ctx["job_id"])
    await sync_to_async(Sudoku.objects.filter(id=sudoku_id).update)(
        job_id=job_id, status=SudokuStatusChoices.RUNNING
    )

    try:
        grid = copy(sudoku.grid)
        solution = copy(grid)

        # TODO: replace with sudoku solving logic
        await asyncio.sleep(10)

        await sync_to_async(_update_sudoku_solution)(sudoku_id, SudokuStatusChoices.COMPLETED)
        return {"status": "completed", "solution": solution}

    except Exception as e:
        await sync_to_async(_update_sudoku_status)(sudoku_id, SudokuStatusChoices.FAILED)
        return {"status": "failed", "error": str(e)}


class WorkerSettings:
    """Settings for the ARQ worker."""

    functions = [solve_sudoku]
    allow_abort_jobs = True
    redis_settings = REDIS_SETTINGS
