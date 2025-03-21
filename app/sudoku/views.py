"""Views for the sudoku APIs."""

from uuid import UUID

from celery import current_app
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ModelSerializer

from .choices import SudokuStatusChoices
from .models import Sudoku
from .serializers import SudokuSerializer, SudokuSolutionSerializer
from .tasks import solve_sudoku


class _CustomLimitOffsetPaginatiopn(LimitOffsetPagination):
    """Custom Pagination for Sudoku viewset."""

    default_limit = 5
    max_limit = 25


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "difficulties",
                OpenApiTypes.STR,
                description="Comma separated list of difficulties to sort by",
            ),
        ],
    ),
)
class SudokuViewSet(viewsets.ModelViewSet[Sudoku]):
    """View to manage sudoku APIs."""

    serializer_class = SudokuSerializer
    queryset = Sudoku.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = _CustomLimitOffsetPaginatiopn

    def get_serializer_class(self) -> ModelSerializer:
        if self.action == "retrieve":
            return SudokuSolutionSerializer
        return SudokuSerializer

    def get_queryset(self) -> QuerySet[Sudoku]:
        """Retrieves sudokus for authenticated user, filtered by difficulty."""
        queryset = Sudoku.objects.filter(user=self.request.user)  # type: ignore

        difficulties = self.request.query_params.get("difficulties")
        if difficulties:
            difficulties_list = [d.strip() for d in difficulties.split(",") if d.strip()]
            if difficulties_list:
                queryset = queryset.filter(difficulty__in=difficulties_list)

        return queryset.order_by("-id").distinct()

    def perform_create(self, serializer: BaseSerializer[Sudoku]) -> None:
        """Creates new sudoku."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="solution", url_name="solution")
    def solve(self, request: Request, pk: UUID | None = None) -> Response:
        """Starts solving a sudoku puzzle."""
        sudoku = self.get_object()

        if sudoku.status not in [
            SudokuStatusChoices.CREATED,
            SudokuStatusChoices.FAILED,
            SudokuStatusChoices.ABORTED,
        ]:
            return Response(
                {"detail": f"Cannot solve sudoku with status: {sudoku.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            task_id = solve_sudoku.delay(str(sudoku.id))

            sudoku.status = SudokuStatusChoices.PENDING
            sudoku.task_id = task_id
            sudoku.save(update_fields=["status", "task_id"])

            return Response(
                {
                    "status": "success",
                    "message": "Sudoku solving started",
                    "sudoku_id": sudoku.id,
                    "task_id": task_id,
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to start solving: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @solve.mapping.delete
    def abort(self, request: Request, pk: UUID | None = None) -> Response:
        """Aborts a running sudoku solver task."""
        sudoku = self.get_object()
        sudoku_id = sudoku.id

        if sudoku.status not in [SudokuStatusChoices.RUNNING, SudokuStatusChoices.PENDING]:
            return Response(
                {"detail": f"Cannot abort task with status: {sudoku.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: find a way to actually abort the Celery task
        current_app.control.terminate()
        aborted = True

        if aborted:
            sudoku.status = SudokuStatusChoices.ABORTED
            sudoku.save(update_fields=["status"])
            return Response(
                {
                    "status": "success",
                    "message": "Sudoku solving aborted",
                    "sudoku_id": sudoku_id,
                    "job_id": sudoku_id,
                }
            )
        return Response(
            {"detail": "Failed to abort job, it may have completed or already been aborted"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=True)
    def status(self, request: Request, pk: UUID | None = None) -> Response:
        """Fetches the current status of a Sudoku."""
        sudoku = self.get_object()
        return Response({"status": sudoku.status})


__all__ = ["SudokuViewSet"]
