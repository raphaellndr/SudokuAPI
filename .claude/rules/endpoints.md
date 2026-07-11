---
paths:
  - "app/*/views.py"
  - "app/*/urls.py"
  - "app/*/serializers.py"
---

# Endpoints (viewsets, serializers, urls)

DRF conventions across the API. Prefer extending an existing sibling over introducing a new pattern.

## Views

- CRUD resources are `viewsets.ModelViewSet[Model]`; aggregation-only resources are a plain `viewsets.ViewSet`; singletons use `generics.*APIView`. Type return values (`-> Response`, `-> QuerySet[Model]`) and params (`request: Request, pk: str | None = None`).
- Override `get_queryset` to scope to `self.request.user` (or `user=None` for anonymous-owned sudokus) and apply `self.request.query_params` filters.
- Override `get_serializer_class` to switch serializer by `self.action` (e.g. create vs update vs read).
- Attach the user and trigger side effects in `perform_create` / `perform_update` / `perform_destroy`.
- Extra operations are `@action(...)`. Share a URL across verbs with `@<action>.mapping.<verb>` (e.g. POST `solver` + `@solve.mapping.delete` for abort). Async operations kick off Celery with `task.delay(...)`, store `task_id`, flip status, and return the id.
- Pagination is a small inline class per viewset (`LimitOffsetPagination` / `PageNumberPagination` subclass) set as `pagination_class`.
- Permissions are the built-ins (`IsAuthenticated`, `AllowAny`), selected either statically via `permission_classes` or dynamically via `get_permissions(self)` keyed on `self.action`.
- **Object-level ownership is checked manually** inside each action — there are no custom `BasePermission` classes. Either raise `rest_framework.exceptions.PermissionDenied` (game_record style) or return a 403 `Response` via a module-level helper (sudoku's `_check_sudoku_ownership`). If using the return-a-Response helper, call it first thing in the action.
- Document query params / non-obvious responses with drf-spectacular `@extend_schema` / `@extend_schema_view` + `OpenApiParameter`.

Reference: `app/sudoku/views.py`, `app/game_record/views.py`, `app/user/views.py`.

## Serializers

- One `serializers.py` per app; parameterize with the model generic: `serializers.ModelSerializer[Model]`.
- `Meta` has a docstring, explicit `fields = [...]` and `read_only_fields = [...]`. Expose FK ids via `serializers.UUIDField(source="user.id", read_only=True)`.
- Use a separate serializer per operation when they diverge (read / `*CreateSerializer` / `*UpdateSerializer`), or subclass and extend `Meta.fields` (see `SudokuSerializer(AnonymousSudokuSerializer)`).
- Business validation lives in `validate(self, data)` raising `serializers.ValidationError`; nested writes are handled in overridden `create`/`update`.
- Type `validated_data` with a module-private `TypedDict` (e.g. `_SudokuParams`).
- Non-model payloads use plain `serializers.Serializer`.

## URLs

- Router-based apps: `DefaultRouter()`, `router.register("", ViewSet[, basename=...])`, `urlpatterns = [path("", include(router.urls))]`, with `app_name` set. Type the list as `list[URLResolver | URLPattern]`.
- Non-router apps (user stats): bind viewset actions explicitly with `ViewSet.as_view({"get": "stats"})` and `<uuid:pk>` / `kwargs={"pk": "me"}` path segments.
- Mount a new app under `/api/<prefix>/` in `config/urls.py`.

Reference: `app/sudoku/urls.py`, `app/game_record/urls.py`, `app/user/urls.py`.
