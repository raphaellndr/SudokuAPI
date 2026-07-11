"""Views for the user API."""

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from django.core.cache import cache
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from app.core.pagination import StandardResultsSetPagination
from app.game_record.models import GameRecord, GameRecordQuerySet
from app.game_record.serializers import GameRecordSerializer
from app.user.serializers import (
    GameStatsSerializer,
    LeaderboardSerializer,
    UserSerializer,
)
from app.user.tasks import refresh_user_stats

from .models import User, UserStats

# Cache lifetimes (seconds).
STATS_CACHE_TTL = 300
LEADERBOARD_CACHE_TTL = 600
# Fixed cache key + upper bound for the leaderboard (sliced per-request).
LEADERBOARD_CACHE_KEY = "leaderboard"
LEADERBOARD_MAX = 100


class ManageUserView(generics.RetrieveUpdateAPIView[User]):
    """Manage the authenticated user."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        """Retrieves and returns the authenticated user.

        :return: User.
        """
        return self.request.user  # type: ignore


class UserDetailView(generics.RetrieveAPIView[User]):
    """Retrieve user information by ID."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_object(self) -> User:
        """Retrieves and returns the user by ID.

        :return: User.
        :raises NotFound: if the user doesn't exist.
        """
        user_id = self.kwargs.get("id")

        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise NotFound("User not found")


class UserMeStatsView(generics.GenericAPIView):
    """View for current user's stats operations."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Refresh current user's statistics."""
        user = request.user

        task = refresh_user_stats.delay(str(user.id))

        # Clear the cache for this user's stats
        cache.delete(f"user_stats_{user.id}")

        return Response(
            {
                "message": "Your stats refresh has been initiated",
                "task_id": task.id,
                "user_id": str(user.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class UserStatsViewSet(viewsets.ViewSet):
    """ViewSet to retrieve user statistics."""

    pagination_class = StandardResultsSetPagination

    def get_permissions(self) -> Sequence[permissions.BasePermission]:
        """Returns permissions based on the action.

        The leaderboard is public; every other action requires authentication.
        """
        if self.action == "leaderboard":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self) -> type:
        """Returns the appropriate serializer class."""
        if self.action == "games":
            return GameRecordSerializer
        if self.action == "leaderboard":
            return LeaderboardSerializer
        return GameStatsSerializer

    def _get_user(self, user_id: str | None) -> User:
        """Resolves a user by ID, or the current user for the ``me`` alias.

        :param user_id: target user id, or ``"me"``.
        :return: resolved User.
        :raises NotFound: if the user doesn't exist.
        """
        if user_id == "me":
            return self.request.user
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("User not found")

    def _get_owned_user(self, user_id: str | None) -> User:
        """Resolves the target user and enforces that it is the requester (or staff).

        :param user_id: target user id, or ``"me"``.
        :return: resolved User.
        :raises PermissionDenied: if the requester is not the target user or staff.
        """
        user = self._get_user(user_id)
        if user != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only access your own game history.")
        return user

    def _calculate_stats(self, queryset: GameRecordQuerySet) -> dict[str, Any]:
        """Computes statistics from a queryset of game records."""
        return queryset.aggregate_stats()

    @action(detail=True, methods=["get"])
    def stats(self, request: Request, pk: str | None = None) -> Response:
        """Gets overall statistics for a user with caching."""
        user = self._get_user(pk)

        cache_key = f"user_stats_{user.id}"
        cached_stats = cache.get(cache_key)

        if cached_stats is None:
            queryset = GameRecord.objects.filter(user=user)
            cached_stats = self._calculate_stats(queryset)
            cache.set(cache_key, cached_stats, STATS_CACHE_TTL)

        serializer = self.get_serializer_class()(data=cached_stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def daily_stats(self, request: Request, pk: str | None = None) -> Response:
        """Gets daily statistics for a user."""
        user = self._get_user(pk)

        # Get date parameter (default to today)
        date_str = request.query_params.get("date")
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = timezone.now().date()

        queryset = GameRecord.objects.filter(user=user, created_at__date=target_date)

        stats = self._calculate_stats(queryset)
        stats["date"] = target_date.strftime("%Y-%m-%d")

        serializer = self.get_serializer_class()(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="stats/weekly")
    def weekly_stats(self, request: Request, pk: str | None = None) -> Response:
        """Get weekly stats for a user."""
        user = self._get_user(pk)

        # Get week parameter (default to current week)
        week_str = request.query_params.get("week")  # Format: 2024-W01
        year = request.query_params.get("year")

        if week_str and year:
            try:
                year_int = int(year)
                week_int = int(week_str)

                if not (1 <= week_int <= 53):
                    return Response(
                        {"error": "Week must be between 1 and 53"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Get the start of the week
                jan_1 = datetime(year_int, 1, 1)
                start_date = jan_1 + timedelta(weeks=week_int - 1)
                start_date = start_date - timedelta(days=start_date.weekday())
                end_date = start_date + timedelta(days=6)
            except ValueError:
                return Response(
                    {"error": "Invalid week format. Use year and week parameters"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Default to current week
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

        queryset = GameRecord.objects.filter(
            user=user, created_at__date__range=[start_date, end_date]
        )

        stats = self._calculate_stats(queryset)
        stats["week_start"] = start_date.strftime("%Y-%m-%d")
        stats["week_end"] = end_date.strftime("%Y-%m-%d")

        serializer = self.get_serializer_class()(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="stats/monthly")
    def monthly_stats(self, request: Request, pk: str | None = None) -> Response:
        """Get monthly stats for a user."""
        user = self._get_user(pk)

        # Get month and year parameters
        month_str = request.query_params.get("month")
        year_str = request.query_params.get("year")

        if month_str and year_str:
            try:
                month = int(month_str)
                year = int(year_str)
                if not (1 <= month <= 12):
                    return Response(
                        {"error": "Month must be between 1 and 12"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"error": "Invalid month or year"}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Default to current month
            now = timezone.now()
            month = now.month
            year = now.year

        queryset = GameRecord.objects.filter(
            user=user, created_at__year=year, created_at__month=month
        )

        stats = self._calculate_stats(queryset)
        stats["month"] = month
        stats["year"] = year

        serializer = self.get_serializer_class()(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="stats/yearly")
    def yearly_stats(self, request: Request, pk: str | None = None) -> Response:
        """Get yearly stats for a user."""
        user = self._get_user(pk)

        # Get year parameter
        year_str = request.query_params.get("year")
        if year_str:
            try:
                year = int(year_str)
            except ValueError:
                return Response({"error": "Invalid year"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to current year
            year = timezone.now().year

        queryset = GameRecord.objects.filter(user=user, created_at__year=year)

        stats = self._calculate_stats(queryset)
        stats["year"] = year

        serializer = self.get_serializer_class()(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def leaderboard(self, request: Request) -> Response:
        """Get leaderboard of top players using UserStats."""
        limit = min(int(request.query_params.get("limit", 10)), LEADERBOARD_MAX)

        cached_leaderboard = cache.get(LEADERBOARD_CACHE_KEY)

        if cached_leaderboard is None:
            leaderboard_data = (
                UserStats.objects.select_related("user")
                .filter(user__is_active=True, total_games__gt=0)
                .order_by("-total_score", "-best_score", "-win_rate", "-completed_games")[
                    :LEADERBOARD_MAX
                ]
            )

            cached_leaderboard = [
                {
                    "user_id": str(stats.user.id),
                    "username": stats.user.username,
                    "total_games": stats.total_games,
                    "won_games": stats.won_games,
                    "completed_games": stats.completed_games,
                    "win_rate": stats.win_rate,
                    "total_score": stats.total_score,
                    "best_score": stats.best_score,
                    "average_score": stats.average_score,
                    "best_time_seconds": stats.best_time_seconds,
                }
                for stats in leaderboard_data
            ]

            cache.set(LEADERBOARD_CACHE_KEY, cached_leaderboard, LEADERBOARD_CACHE_TTL)

        results = cached_leaderboard[:limit]
        return Response({"count": len(results), "results": results})

    @action(detail=True, methods=["get"])
    def games(self, request: Request, pk: str | None = None) -> Response:
        """Get game history for a user (owner or staff only)."""
        user = self._get_owned_user(pk)

        status_filter = request.query_params.get("status")

        queryset = (
            GameRecord.objects.filter(user=user)
            .select_related("user", "sudoku")
            .order_by("-created_at")
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.get_serializer_class()(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)


__all__ = ["ManageUserView", "UserDetailView", "UserMeStatsView", "UserStatsViewSet"]
