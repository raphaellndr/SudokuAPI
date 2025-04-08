"""Views for the sudoku APIs."""

from collections.abc import Sequence

from celery import current_app
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from kombu.exceptions import OperationalError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ModelSerializer

from .base import update_sudoku_status
from .choices import SudokuStatusChoices
from .models import Sudoku
from .serializers import AnonymousSudokuSerializer, SudokuSerializer, SudokuSolutionSerializer
from .tasks import solve_sudoku


def _check_sudoku_ownership(sudoku: Sudoku, request: Request) -> Response:
    """Checks that the sudoku belongs to the current user.

    If the sudoku has a user and it"s not the current user, deny access.

    :param sudoku: Sudoku instance to check.
    :param request: Request instance.
    :return: Response with permission denied message if the user is not the owner.
    """
    if sudoku.user is not None and sudoku.user != request.user:
        return Response(
            {"detail": "You don't have permission to solve this sudoku"},
            status=status.HTTP_403_FORBIDDEN,
        )


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
    pagination_class = _CustomLimitOffsetPagination

    def get_permissions(self) -> Sequence[BasePermission]:
        """Returns custom permissions based on the action.

        - Anonymous users can access create, retrieve, list, solve, abort, solution,
        delete_solution and status endpoints.
        - Only authenticated users can access update, partial_update and destroy
        """
        if self.action in [
            "create",
            "retrieve",
            "list",
            "solve",
            "abort",
            "solution",
            "delete_solution",
            "status",
        ]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self) -> ModelSerializer:
        """Returns the appropriate serializer based on the current action.

        Uses:
        - SudokuSolutionSerializer for GET requests on the solution endpoint
        - AnonymousSudokuSerializer for anonymous users on create
        - SudokuSerializer for all other cases
        """
        if "solution" in self.action and self.request.method == "GET":
            return SudokuSolutionSerializer

        if not self.request.user.is_authenticated and self.action in ["create", "retrieve", "list"]:
            return AnonymousSudokuSerializer

        return SudokuSerializer

    def get_queryset(self) -> QuerySet[Sudoku]:
        """Retrieves sudokus for user, filtered by difficulty."""
        if not self.request.user.is_authenticated:
            queryset = Sudoku.objects.filter(user=None)
        else:
            queryset = Sudoku.objects.filter(user=self.request.user)

        difficulties = self.request.query_params.get("difficulties")
        if difficulties:
            difficulties_list = [d.strip() for d in difficulties.split(",") if d.strip()]
            if difficulties_list:
                queryset = queryset.filter(difficulty__in=difficulties_list)

        return queryset.order_by("-created_at").distinct()

    def perform_create(self, serializer: BaseSerializer[Sudoku]) -> None:
        """Creates new sudoku, associating with user only if authenticated."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)

    @action(detail=True, methods=["post"], url_path="solver", url_name="solver")
    def solve(self, request: Request, pk: str | None = None) -> Response:
        """Starts solving a sudoku puzzle."""
        sudoku = self.get_object()
        _check_sudoku_ownership(sudoku, request)

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
            task = solve_sudoku.delay(pk)

            update_sudoku_status(sudoku, SudokuStatusChoices.PENDING)
            sudoku.task_id = task.id
            sudoku.save(update_fields=["task_id"])

            return Response(
                {
                    "status": "success",
                    "message": "Sudoku solving started",
                    "sudoku_id": pk,
                    "task_id": task.id,
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to start solving: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @solve.mapping.delete
    def abort(self, request: Request, pk: str | None = None) -> Response:
        """Aborts a running sudoku solver task."""
        sudoku = self.get_object()
        _check_sudoku_ownership(sudoku, request)

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
            sudoku.task_id = None
            sudoku.save(update_fields=["task_id"])

            return Response(
                {
                    "status": "success",
                    "message": "Sudoku solving aborted",
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
    def solution(self, request: Request, pk: str | None = None) -> Response:
        """Retrieves the solution for a sudoku."""
        sudoku = self.get_object()
        _check_sudoku_ownership(sudoku, request)

        try:
            if sudoku.status != SudokuStatusChoices.COMPLETED:
                return Response(
                    {"detail": "Sudoku solution is not available yet"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            solution = sudoku.solution
            serializer = self.get_serializer_class()(solution)

            return Response(serializer.data)
        except Sudoku.solution.RelatedObjectDoesNotExist:
            return Response(
                {"detail": "No solution found for this sudoku"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @solution.mapping.delete
    def delete_solution(self, request: Request, pk: str | None = None) -> Response:
        """Removes the solution for a sudoku."""
        sudoku = self.get_object()
        _check_sudoku_ownership(sudoku, request)

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
    def status(self, request: Request, pk: str | None = None) -> Response:
        """Fetches the current status of a Sudoku."""
        sudoku = self.get_object()
        _check_sudoku_ownership(sudoku, request)

        return Response({"sudoku_status": sudoku.status})


__all__ = ["SudokuViewSet"]
