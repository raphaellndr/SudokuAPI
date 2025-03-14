"""Views for the sudoku APIs."""

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from sudoku.serializers import SudokuSerializer

from .models import Sudoku


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


class SudokuSolveView(APIView):
    """API view to handle solving Sudoku puzzles and retrieving these results."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, id: int) -> Response:
        """Retrieve a solved sudoku."""
        try:
            sudoku = Sudoku.objects.get(id=id, user=request.user)  # type: ignore
            serializer = SudokuSerializer(sudoku)
            return Response(serializer.data, status=200)
        except Sudoku.DoesNotExist:
            return Response({"error": "Sudoku not found."}, status=404)

    def post(self, request: Request, id: int) -> Response:
        """Solve a sudoku puzzle."""
        # TODO: run task
        return Response({"status": "Sudoku solving task initiated."})
