---
name: add-endpoint
description: Add a REST endpoint to the SudokuArena API following the DRF viewset/router + serializer conventions, with per-action permissions, manual ownership checks, optional Celery dispatch, and matching tests. Use when adding or extending an API route.
---

# Add an endpoint

1. **Find a sibling to model after.**
   - Router-registered CRUD resource → `app/sudoku/views.py` + `app/sudoku/urls.py`.
   - Manually-bound, action-per-path resource (stats, `me/…`) → `app/user/views.py` + `app/user/urls.py`.
2. **Define or reuse the serializer** in the app's `serializers.py`. Bodies are `ModelSerializer[Model]` with explicit `fields`/`read_only_fields`; add a separate `*CreateSerializer`/`*UpdateSerializer` if create/update diverge. Non-model payloads use plain `serializers.Serializer`.
3. **Write the handler** in the app's `views.py` — see the `endpoints` rule. Scope `get_queryset` to `self.request.user`, switch serializers in `get_serializer_class`, set permissions (static `permission_classes` or dynamic `get_permissions`), and **check object ownership manually** in the action. Extra operations are `@action` (share a URL with `@<action>.mapping.<verb>`). Document non-obvious query params/responses with drf-spectacular `@extend_schema`.
4. **Async work?** Kick off a Celery task with `task.delay(...)`, store the `task_id`, flip status, and return the id — see `.claude/rules/celery-tasks.md`.
5. **Register the route**: `router.register(...)` in the app's `urls.py`, or add a `path(..., ViewSet.as_view({...}))`. Mount a brand-new app under `/api/<prefix>/` in `config/urls.py`.
6. **Add tests** under `tests/<app>/`, mirroring the source path — see `.claude/rules/testing.md`.
