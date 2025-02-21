"""Views for the sudoku APIs."""

from core.models import Sudoku
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from sudoku import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "difficulties",
                OpenApiTypes.STR,
                description="Comma separated list of difficulties to filter",
            ),
        ],
    ),
)
class SudokuViewSet(viewsets.ModelViewSet[Sudoku]):
    """View to manage sudoku APIs."""

    serializer_class = serializers.SudokuSerializer
    queryset = Sudoku.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Sudoku]:
        """Retrieves sudokus for authenticated user, filtered by difficulty."""
        queryset = self.queryset

        if self.request.user.is_authenticated:
            user = self.request.user
            queryset = queryset.filter(user=user)

            difficulties = self.request.query_params.get("difficulties")
            if difficulties:
                difficulties_list = difficulties.split(",")
                queryset = queryset.filter(difficulty__in=difficulties_list)
        else:
            queryset = queryset.none()

        return queryset.order_by("-id").distinct()

    def perform_create(self, serializer: BaseSerializer[Sudoku]) -> None:
        """Creates new sudoku."""
        serializer.save(user=self.request.user)
