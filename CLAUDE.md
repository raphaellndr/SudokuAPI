# CLAUDE.md

Project context for the **SudokuArena API** (Python 3.12 / Django 5.1 / DRF, async via Celery + Channels). A REST API powering the [SudokuArena](https://github.com/raphaellndr/sudoku-front-end) React frontend — users register, solve/play Sudoku puzzles, track stats, and compete on a leaderboard; images can be uploaded to detect a grid. See @README.md for setup.

## Behavioral guidelines

Guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Commands

Package manager is **Poetry**. The dev/prod runner is **Docker Compose** (there is no Makefile or `scripts/`). The active settings module is `config.settings.local` (default in `manage.py`).

- `docker compose -f docker-compose.local.yml up --build` — build + run the full stack (web, postgres, redis, celery worker, celery beat)
- `docker compose -f docker-compose.local.yml down` — tear down
- Migrations run automatically on web startup (`compose/local/entrypoint.sh`); to run manually: `python manage.py makemigrations` / `migrate`
- `celery -A config worker` / `celery -A config beat` — Celery worker / scheduler (run by their own compose services)
- `docker compose -f docker-compose.local.yml exec web pytest` — run the test suite (or `poetry run pytest` locally)
- `ruff format` then `ruff check . --fix` — format + lint (also run by pre-commit)

Git hooks (**pre-commit**): on commit, `ruff format` + `ruff check --fix`. The mypy hook exists but is currently commented out, so type-checking is not enforced automatically — run `mypy` manually.

## Architecture

A Django project (`config/`) with feature apps under `app/`. A few things not obvious from the code:

- **Entry flow**: `manage.py` (dev) / `config/asgi.py` (serving). `asgi.py` builds a `ProtocolTypeRouter` — HTTP goes to the Django ASGI app, WebSockets go through `AuthMiddlewareStack` to `app.sudoku.routing`. `daphne` (first in `INSTALLED_APPS`) serves ASGI so `runserver` handles WebSockets too.
- **Config** is split: `config/settings/base.py` with `local.py` / `production.py` doing `from .base import *`. Selected via `DJANGO_SETTINGS_MODULE` (`config.settings.local` by default).
- **Routing**: apps are mounted in `config/urls.py` under `/api/{auth,users,games,sudokus}/`. Most apps use a DRF `DefaultRouter`; the `user` app binds actions manually with `as_view({...})` — see `.claude/rules/endpoints.md`.
- **Schema**: drf-spectacular serves the OpenAPI spec at `/api/schema/` and Swagger UI at `/api/docs/`. Document endpoints with `@extend_schema` / `@extend_schema_view`.
- **Async work**: solving and image detection are Celery tasks dispatched from viewset actions with `.delay()`; the returned `task_id` is stored on the model. Progress is pushed to the frontend over Channels from `app/sudoku/base.py` (`update_sudoku_status`, `update_sudoku_detection`) — see `.claude/rules/celery-tasks.md`.
- **Solver & detection**: the proprietary solver is a git dependency imported as `sudoku_resolver`. The image pipeline (OpenCV + a bundled ONNX classifier) lives in `app/sudoku/detection/` and is not fully wired end-to-end yet.
- **Auth**: SimpleJWT bearer tokens + dj-rest-auth (register/login/logout) + allauth Google OAuth. The user model is a custom email-based `user.User` with a UUID PK. Signals in `app/user/signals.py` auto-create and refresh `UserStats`.

## Conventions

- Docstring format: `.claude/rules/docstrings.md` (Sphinx). Models/choices: `.claude/rules/django-models.md`. Endpoints: `.claude/rules/endpoints.md`. Tasks: `.claude/rules/celery-tasks.md`. Tests: `.claude/rules/testing.md`.
- Modules declare an explicit `__all__`.
- Type hints are used pervasively (mypy strict-ish with `django-stubs`/`drf-stubs`). Ruff line length is 100.
- **Target is Python 3.11 syntax** (`.ruff.toml`/mypy `py311`) even though the runtime is 3.12 — do **not** use PEP 695 (`type` aliases, `class Foo[T]`); use `TypeVar`, `TypedDict`, and PEP 604 unions instead.

## Key gotchas

Known rough edges (documented, not yet fixed — candidates for a later cleanup pass):

- `pytest.ini` and `.mypy.ini` reference `app.settings`, which does not exist — the real settings module is `config.settings.*`.
- `config/settings/production.py` sets `DEBUG = True`.
- Ruff and mypy target `py311` while the project runs on Python 3.12.
- `app/sudoku/tasks.py`'s `__all__` lists a non-existent `detect_sudoku`.
- The README references `docker-compose.production.yml`; the actual production compose file is `docker-compose.yml`.
- The proprietary `sudoku-resolver` is a **git** dependency (`pyproject.toml`), not a private package index.
