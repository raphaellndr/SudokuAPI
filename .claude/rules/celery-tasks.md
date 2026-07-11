---
paths:
  - "app/*/tasks.py"
---

# Celery tasks

Async work (Sudoku solving, image detection, cleanup, stats refresh) runs as Celery tasks.

- Decorate tasks with `@app.task` (`from config.celery import app`) or `@shared_task`. Both coexist; match the app's existing file.
- Type the signature; return a JSON-serializable `{"status": ..., ...}` dict on success and on handled failure.
- Tasks are dispatched from viewset actions with `task.delay(...)`, which stores the returned `task_id` on the model.
- Report progress and terminal state by updating the model's status **and** broadcasting over Channels via the helpers in `app/sudoku/base.py` (`update_sudoku_status`, `update_sudoku_detection`) — call them on both success and failure paths so the frontend WebSocket stays in sync.
- The proprietary solver is imported as `sudoku_resolver` (`from sudoku_resolver.sudoku import Sudoku as SudokuResolver`); the image pipeline lives in `app/sudoku/detection/`.
- Periodic tasks are registered by dotted path in `CELERY_BEAT_SCHEDULE` (`config/settings/base.py`) with a `crontab(...)` schedule.
- End the module with an explicit `__all__` listing the task callables.

Reference: `app/sudoku/tasks.py`, `app/user/tasks.py`.
