"""ViewSet for GameRecord CRUD operations."""

from django.db.models import QuerySet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from app.game_record.choices import GameStatusChoices
from app.game_record.models import GameRecord
from app.game_record.serializers import (
    GameRecordCreateSerializer,
    GameRecordSerializer,
    GameRecordUpdateSerializer,
)
from app.user.models import UserStats


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class GameRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing GameRecord CRUD operations."""

    queryset = GameRecord.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self) -> BaseSerializer:
        """Returns appropriate serializer class based on action."""
        if self.action == "create":
            return GameRecordCreateSerializer
        if self.action in ["update", "partial_update"]:
            return GameRecordUpdateSerializer
        return GameRecordSerializer

    def get_queryset(self) -> QuerySet[GameRecord]:
        """Filters queryset to only show user's own game records."""
        queryset = GameRecord.objects.filter(user=self.request.user).order_by("-created_at")

        status_filter = self.request.query_params.get("status")
        won_filter = self.request.query_params.get("won")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if won_filter is not None:
            won_value = won_filter.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(won=won_value)

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def perform_create(self, serializer) -> GameRecord:
        """Creates a new game record for the authenticated user."""
        game_record = serializer.save(user=self.request.user)
        self._update_user_stats()
        return game_record

    def perform_update(self, serializer) -> GameRecord:
        """Updates game record and refresh user stats."""
        game_record = serializer.save()
        self._update_user_stats()
        return game_record

    def perform_destroy(self, instance) -> None:
        """Deletes game record and refresh user stats."""
        instance.delete()
        self._update_user_stats()

    def _update_user_stats(self):
        """Updates user statistics after CRUD operations."""
        user_stats = UserStats.get_or_create_for_user(self.request.user)
        user_stats.recalculate_from_games()

    def _check_ownership(self, obj):
        """Checks if the user owns the game record."""
        if obj.user != self.request.user:
            raise PermissionDenied("You can only access your own game records.")

    def retrieve(self, request, *args, **kwargs):
        """Retrieves a specific game record."""
        instance = self.get_object()
        self._check_ownership(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Updates a specific game record."""
        instance = self.get_object()
        self._check_ownership(instance)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partially updates a specific game record."""
        instance = self.get_object()
        self._check_ownership(instance)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Deletes a specific game record."""
        instance = self.get_object()
        self._check_ownership(instance)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def recent(self, request: Request) -> Response:
        """Gets recent game records (last 10 by default)."""
        limit = min(int(request.query_params.get("limit", 10)), 50)

        queryset = self.get_queryset()[:limit]
        serializer = self.get_serializer(queryset, many=True)

        return Response({"count": len(serializer.data), "results": serializer.data})

    @action(detail=False, methods=["get"])
    def best_scores(self, request: Request) -> Response:
        """Gets games with best scores."""
        limit = min(int(request.query_params.get("limit", 10)), 50)

        queryset = self.get_queryset().filter(score__isnull=False).order_by("-score")[:limit]

        serializer = self.get_serializer(queryset, many=True)

        return Response({"count": len(serializer.data), "results": serializer.data})

    @action(detail=False, methods=["get"])
    def best_times(self, request: Request) -> Response:
        """Gets games with best times (fastest completion)."""
        limit = min(int(request.query_params.get("limit", 10)), 50)

        queryset = (
            self.get_queryset()
            .filter(time_taken__isnull=False, status=GameStatusChoices.COMPLETED)
            .order_by("time_taken")[:limit]
        )

        serializer = self.get_serializer(queryset, many=True)

        return Response({"count": len(serializer.data), "results": serializer.data})

    @action(detail=True, methods=["post"])
    def complete(self, request: Request, pk=None) -> Response:
        """Marks a game as completed."""
        instance = self.get_object()
        self._check_ownership(instance)

        if instance.status == GameStatusChoices.COMPLETED:
            return Response(
                {"error": "Game is already completed"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update the game status and other completion data from request
        serializer = GameRecordUpdateSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            # Ensure status is set to completed
            serializer.validated_data["status"] = GameStatusChoices.COMPLETED
            game_record = serializer.save()

            # Update user stats
            self._update_user_stats()

            response_serializer = GameRecordSerializer(game_record)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def abandon(self, request: Request, pk=None) -> Response:
        """Marks a game as abandoned."""
        instance = self.get_object()
        self._check_ownership(instance)

        if instance.status in [
            GameStatusChoices.COMPLETED,
            GameStatusChoices.STOPPED,
            GameStatusChoices.ABANDONED,
        ]:
            return Response(
                {"error": "Cannot abandon a completed, stopped or already abandoned game"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = GameStatusChoices.STOP
        instance.save()

        # Update user stats
        self._update_user_stats()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def stop(self, request: Request, pk=None) -> Response:
        """Marks a game as stopped."""
        instance = self.get_object()
        self._check_ownership(instance)

        if instance.status in [
            GameStatusChoices.COMPLETED,
            GameStatusChoices.STOPPED,
            GameStatusChoices.ABANDONED,
        ]:
            return Response(
                {"error": "Cannot stop a completed, stopped or already abandoned game"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = GameStatusChoices.ABANDONED
        instance.save()

        # Update user stats
        self._update_user_stats()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request: Request) -> Response:
        """Bulk deletes game records by IDs."""
        ids = request.data.get("ids", [])

        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        if len(ids) > 100:  # Limit bulk operations
            return Response(
                {"error": "Cannot delete more than 100 records at once"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter to only user's own records
        queryset = self.get_queryset().filter(id__in=ids)
        deleted_count = queryset.count()

        if deleted_count == 0:
            return Response(
                {"error": "No records found to delete"}, status=status.HTTP_404_NOT_FOUND
            )

        queryset.delete()

        # Update user stats
        self._update_user_stats()

        return Response({"message": f"Successfully deleted {deleted_count} game records"})


__all__ = ["GameRecordViewSet"]
