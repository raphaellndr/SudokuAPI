---
paths:
  - "tests/**/*.py"
---

# Testing conventions (pytest-django)

- Tests live under `tests/` at the repo root, mirroring the app layout (`app/sudoku/…` → `tests/sudoku/test_*.py`). Per-app `tests/<app>/urls.py` helper modules hold URL constants/builders (e.g. `SUDOKUS_URL`, `sudoku_url()`, `solver_url()`).
- Prefer **`@pytest.mark.parametrize`**. Cover the success and raising paths in one table using `pytest.raises(...)` vs `contextlib.nullcontext()` (imported as `does_not_raise`).
- Seed real data with the **factory fixtures** — don't mock the ORM. The `factory_boy` factories in `tests/plugins/factories/` are private classes (`_SudokuFactory`, `_UserFactory`) exposed only through pytest fixtures that return callable builders (`create_sudoku`, `create_sudokus`, `create_user`, `create_superuser`, `create_sudoku_solution`). Add new factories there and register the module in `pytest_plugins` in `tests/conftest.py`.
- Shared fixtures live in `tests/plugins/instances/` — `clients.py` (`client` = Django `Client`, `api_client` = DRF `APIClient` with `force_authenticate`) and `payloads.py` (`sudoku_payload`, `user_payload`, `register_user_payload`). Resolve fixtures dynamically with `request.getfixturevalue(name)` when parametrizing over fixture names (e.g. `user` over `["create_user", None]`).
- The DB is real SQLite/Postgres via pytest-django. Tests use the **`transactional_db`** fixture, and an autouse `db_flush_data` fixture (`tests/conftest.py`) runs `flush` around each test.
- Reserve `monkeypatch` for error paths and to stand in for Celery/solver side effects at the view layer (e.g. patching `SudokuViewSet.solve` or `update_sudoku_status`) — Celery is not run eager in tests.
- Test files don't need module/function docstrings.

Reference: `tests/sudoku/test_views.py`, `tests/plugins/factories/sudoku.py`, `tests/conftest.py`.
