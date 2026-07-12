"""Views for the sudoku APIs."""

import logging
import uuid
from collections.abc import Sequence

from celery import current_app
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from kombu.exceptions import OperationalError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ModelSerializer
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .base import update_sudoku_detection, update_sudoku_status
from .choices import DetectionStatusChoices, SudokuStatusChoices
from .constants import MAX_IMAGE_SIZE_BYTES, SUPPORTED_IMAGE_CONTENT_TYPES
from .models import Sudoku
from .serializers import AnonymousSudokuSerializer, SudokuSerializer, SudokuSolutionSerializer
from .tasks import detect_sudoku_digits, solve_sudoku

logger = logging.getLogger(__name__)


class _SolveAnonThrottle(AnonRateThrottle):
    """Throttles anonymous solve requests (rate keyed by the ``solve`` scope)."""

    scope = "solve"


class _SolveUserThrottle(UserRateThrottle):
    """Throttles authenticated solve requests."""

    scope = "solve"


class _DetectAnonThrottle(AnonRateThrottle):
    """Throttles anonymous detection requests."""

    scope = "detect"


class _DetectUserThrottle(UserRateThrottle):
    """Throttles authenticated detection requests."""

    scope = "detect"


def _check_sudoku_ownership(sudoku: Sudoku, request: Request) -> None:
    """Ensures the sudoku belongs to the current user.

    Anonymous-owned sudokus (``user is None``) are shared, so access is only rejected
    when the sudoku has an owner different from the requester.

    :param sudoku: Sudoku instance to check.
    :param request: Request instance.
    :raises PermissionDenied: if the requester is not the owner.
    """
    if sudoku.user is not None and sudoku.user != request.user:
        raise PermissionDenied("You don't have permission to access this sudoku")


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
        delete_solution, status and detect_digits endpoints.
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
            "detect_digits",
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

        return queryset.select_related("user", "solution").order_by("-created_at").distinct()

    def perform_create(self, serializer: BaseSerializer[Sudoku]) -> None:
        """Creates new sudoku, associating with user only if authenticated."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)

    @action(
        detail=True,
        methods=["post"],
        url_path="solver",
        url_name="solver",
        throttle_classes=[_SolveAnonThrottle, _SolveUserThrottle],
    )
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
            # Set PENDING before dispatching: a fast task could otherwise write its
            # terminal status first and have it stomped back to PENDING here.
            update_sudoku_status(sudoku, SudokuStatusChoices.PENDING)

            task = solve_sudoku.delay(pk)
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
        except Exception:
            logger.exception("Failed to start solving sudoku %s", pk)
            update_sudoku_status(sudoku, SudokuStatusChoices.FAILED)
            return Response(
                {"detail": "Failed to start solving"},
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

    @action(
        detail=False,
        methods=["post"],
        url_path="detect",
        url_name="detect",
        parser_classes=[MultiPartParser, FormParser],
        throttle_classes=[_DetectAnonThrottle, _DetectUserThrottle],
    )
    def detect_digits(self, request: Request) -> Response:
        """Uploads an image to detect sudoku digits."""
        if "image" not in request.FILES:
            return Response(
                {"detail": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["image"]

        if image_file.size > MAX_IMAGE_SIZE_BYTES:
            return Response(
                {"detail": "Image file too large. Maximum size is 10MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if image_file.content_type not in SUPPORTED_IMAGE_CONTENT_TYPES:
            return Response(
                {"detail": "Invalid image format. Only JPEG and PNG are supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_id = request.data.get("session_id", "")
        try:
            uuid.UUID(session_id)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid or missing session_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            update_sudoku_detection(session_id, DetectionStatusChoices.PENDING)
            task = detect_sudoku_digits.delay(image_file.read(), session_id)

            return Response(
                {
                    "status": "success",
                    "message": "Digit detection started",
                    "task_id": task.id,
                }
            )
        except Exception:
            logger.exception("Failed to start digit detection")
            update_sudoku_detection(
                session_id, DetectionStatusChoices.FAILED, message="Failed to start digit detection"
            )
            return Response(
                {"detail": "Failed to start digit detection"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


__all__ = ["SudokuViewSet"]
