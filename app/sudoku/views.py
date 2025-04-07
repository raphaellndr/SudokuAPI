"""Views for the sudoku APIs."""

from uuid import UUID

from celery import current_app
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from kombu.exceptions import OperationalError
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
from .tasks import solve_sudoku, update_sudoku_status


class _CustomLimitOffsetPagination(LimitOffsetPagination):
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
    pagination_class = _CustomLimitOffsetPagination

    def get_serializer_class(self) -> ModelSerializer:
        """Returns the appropriate serializer based on the current action.

        Uses `SudokuSolutionSerializer` only for GET request on the solution endpoint.
        """
        if "solution" in self.action and self.request.method == "GET":
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

        return queryset.order_by("-created_at").distinct()

    def perform_create(self, serializer: BaseSerializer[Sudoku]) -> None:
        """Creates new sudoku."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="solver", url_name="solver")
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
            task = solve_sudoku.delay(str(sudoku.id))

            update_sudoku_status(sudoku, SudokuStatusChoices.PENDING)
            sudoku.task_id = task.id
            sudoku.save(update_fields=["task_id"])

            return Response(
                {
                    "status": "success",
                    "message": "Sudoku solving started",
                    "sudoku_id": sudoku.id,
                    "task_id": task.id,
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

        if not sudoku.task_id:
            return Response(
                {"detail": "No task found to abort"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sudoku.status not in [SudokuStatusChoices.RUNNING, SudokuStatusChoices.PENDING]:
            return Response(
                {"detail": f"Cannot abort task with status: {sudoku.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            current_app.control.terminate(sudoku.task_id)
            update_sudoku_status(sudoku, SudokuStatusChoices.ABORTED)

            return Response(
                {
                    "status": "success",
                    "message": "Sudoku solving aborted",
                    "sudoku_id": sudoku_id,
                    "job_id": sudoku_id,
                }
            )
        except OperationalError:
            # Handle broker connectivity issues
            return Response(
                {"detail": "Service temporarily unavailable. Please try again later"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            return Response(
                {"detail": "An unexpected error occurred while aborting the job"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, url_path="solution", url_name="solution")
    def solution(self, request: Request, pk: UUID | None = None) -> Response:
        """Retrieves the solution for a sudoku."""
        sudoku = self.get_object()

        try:
            solution = sudoku.solution
            if sudoku.status != SudokuStatusChoices.COMPLETED:
                return Response(
                    {"detail": "Sudoku solution is not available yet"},
                    status=status.HTTP_202_ACCEPTED,
                )

            serializer = self.get_serializer_class()(solution)
            return Response(serializer.data)
        except Sudoku.solution.RelatedObjectDoesNotExist:
            return Response(
                {"detail": "No solution found for this sudoku"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @solution.mapping.delete
    def delete_solution(self, request: Request, pk: UUID | None = None) -> Response:
        """Removes the solution for a sudoku."""
        sudoku = self.get_object()

        try:
            solution = sudoku.solution
            if sudoku.status != SudokuStatusChoices.COMPLETED:
                return Response(
                    {"detail": "Cannot delete solution because sudoku is not yet completed"},
                    status=status.HTTP_409_CONFLICT,
                )

            solution.delete()
            update_sudoku_status(sudoku, SudokuStatusChoices.CREATED)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Sudoku.solution.RelatedObjectDoesNotExist:
            return Response(
                {"detail": "No solution found for this sudoku"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True)
    def status(self, request: Request, pk: UUID | None = None) -> Response:
        """Fetches the current status of a Sudoku."""
        sudoku = self.get_object()
        return Response({"status": sudoku.status})


__all__ = ["SudokuViewSet"]
