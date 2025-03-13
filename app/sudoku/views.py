"""Views for the sudoku APIs."""

from core.models import Sudoku
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from sudoku import serializers


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

    serializer_class = serializers.SudokuSerializer
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
