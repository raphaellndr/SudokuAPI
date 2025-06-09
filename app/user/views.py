"""Views for the user API."""

from datetime import datetime, timedelta
from typing import Any

from django.core.cache import cache
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.db.models.query import QuerySet
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from app.game_record.choices import GameStatusChoices
from app.game_record.models import GameRecord
from app.game_record.serializers import (
    GameRecordCreateSerializer,
    GameRecordSerializer,
    GameRecordUpdateSerializer,
)
from app.user.serializers import (
    GameStatsSerializer,
    LeaderboardSerializer,
    UserSerializer,
)
from app.user.tasks import refresh_user_stats

from .models import User, UserStats


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


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


class UserMeStatsView(generics.GenericAPIView):
    """View for current user's stats operations."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Refresh current user's statistics."""
        user = request.user

        try:
            task = refresh_user_stats.delay(str(user.id))

            # Clear the cache for this user's stats
            cache_key = f"user_stats_{user.id}"
            cache.delete(cache_key)

            return Response(
                {
                    "message": "Your stats refresh has been initiated",
                    "task_id": task.id,
                    "user_id": str(user.id),
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to initiate stats refresh: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserStatsViewSet(viewsets.ViewSet):
    """ViewSet to retrieve user statistics."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return GameRecord.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Returns the appropriate serializer class."""
        if self.action == "create":
            return GameRecordCreateSerializer
        if self.action in ["update", "partial_update"]:
            return GameRecordUpdateSerializer
        if self.action == "games":
            return GameRecordSerializer
        if self.action == "leaderboard":
            return LeaderboardSerializer
        return GameStatsSerializer

    def _get_user(self, user_id: str | None) -> User:
        """Get user by ID or return current user if 'me'."""
        if user_id == "me":
            return self.request.user
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("User not found")

    def _empty_stats(self) -> dict[str, Any]:
        """Returns empty stats structure."""
        return {
            "total_games": 0,
            "won_games": 0,
            "lost_games": 0,
            "win_rate": 0.0,
            "completed_games": 0,
            "abandoned_games": 0,
            "stopped_games": 0,
            "in_progress_games": 0,
            "total_time_seconds": 0,
            "average_time_seconds": None,
            "best_time_seconds": None,
            "total_score": 0,
            "average_score": None,
            "best_score": None,
            "total_hints_used": 0,
            "total_checks_used": 0,
            "total_deletions": 0,
        }

    def _calculate_stats(self, queryset: QuerySet[GameRecord]) -> dict[str, Any]:
        """Calculates statistics from a queryset of game records."""
        if not queryset.exists():
            self._empty_stats()

        # Single database query to get all aggregated data
        stats = queryset.aggregate(
            total_games=Count("id"),
            won_games=Count("id", filter=Q(won=True)),
            lost_games=Count("id", filter=Q(won=False)),
            completed_games=Count("id", filter=Q(status=GameStatusChoices.COMPLETED)),
            abandoned_games=Count("id", filter=Q(status=GameStatusChoices.ABANDONED)),
            stopped_games=Count("id", filter=Q(status=GameStatusChoices.STOPPED)),
            in_progress_games=Count("id", filter=Q(status=GameStatusChoices.IN_PROGRESS)),
            total_time_seconds=Sum("time_taken"),
            average_time_seconds=Avg("time_taken"),
            best_time_seconds=Min("time_taken"),
            total_score=Sum("score"),
            average_score=Avg("score"),
            best_score=Max("score"),
            total_hints_used=Sum("hints_used"),
            total_checks_used=Sum("checks_used"),
            total_deletions=Sum("deletions"),
        )

        # Win rate
        win_rate = stats["won_games"] / stats["total_games"] if stats["total_games"] > 0 else 0.0

        # Convert time durations to seconds
        total_time_seconds = stats["total_time_seconds"] or 0
        average_time_seconds = stats["average_time_seconds"] or None
        best_time_seconds = stats["best_time_seconds"] or None

        return {
            "total_games": stats["total_games"],
            "won_games": stats["won_games"],
            "lost_games": stats["lost_games"],
            "win_rate": round(win_rate, 2),
            "completed_games": stats["completed_games"],
            "abandoned_games": stats["abandoned_games"],
            "stopped_games": stats["stopped_games"],
            "in_progress_games": stats["in_progress_games"],
            "total_time_seconds": total_time_seconds,
            "average_time_seconds": average_time_seconds,
            "best_time_seconds": best_time_seconds,
            "total_score": stats["total_score"] or 0,
            "average_score": round(stats["average_score"], 2) if stats["average_score"] else None,
            "best_score": stats["best_score"],
            "total_hints_used": stats["total_hints_used"] or 0,
            "total_checks_used": stats["total_checks_used"] or 0,
            "total_deletions": stats["total_deletions"] or 0,
        }

    @action(detail=True, methods=["get"])
    def stats(self, request: Request, pk: str | None = None) -> Response:
        """Gets overall statistics for a user with caching."""
        user = self._get_user(pk)

        # Try to get from cache first
        cache_key = f"user_stats_{user.id}"
        cached_stats = cache.get(cache_key)

        if cached_stats is None:
            queryset = GameRecord.objects.filter(user=user)
            cached_stats = self._calculate_stats(queryset)
            # Cache for 5 minutes
            cache.set(cache_key, cached_stats, 300)

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

        # Filter games for the specific day
        queryset = GameRecord.objects.filter(user=user, created_at__date=target_date)

        stats = self._calculate_stats(queryset)
        stats["date"] = target_date.strftime("%Y-%m-%d")

        serializer = self.get_serializer_class()(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="stats/weekly")
    def weekly_stats(self, request: Request, pk: str = None) -> Response:
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

        # Filter games for the specific week
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
    def monthly_stats(self, request: Request, pk: str = None) -> Response:
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

        # Filter games for the specific month
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
    def yearly_stats(self, request: Request, pk: str = None) -> Response:
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

        # Filter games for the specific year
        queryset = GameRecord.objects.filter(user=user, created_at__year=year)

        stats = self._calculate_stats(queryset)
        stats["year"] = year

        serializer = self.get_serializer_class()(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def leaderboard(self, request: Request) -> Response:
        """Get leaderboard of top players using UserStats."""
        limit = min(int(request.query_params.get("limit", 10)), 100)

        # Check cache first
        cache_key = f"leaderboard_{limit}"
        cached_leaderboard = cache.get(cache_key)

        if cached_leaderboard is None:
            leaderboard_data = (
                UserStats.objects.select_related("user")
                .filter(user__is_active=True, total_games__gt=0)
                .order_by("-total_score", "-best_score", "-win_rate", "-completed_games")[:limit]
            )

            # Convert to list with proper formatting
            cached_leaderboard = []
            for stats in leaderboard_data:
                cached_leaderboard.append(
                    {
                        "user_id": str(stats.user.id),
                        "username": stats.user.username,
                        "email": stats.user.email,
                        "total_games": stats.total_games,
                        "won_games": stats.won_games,
                        "completed_games": stats.completed_games,
                        "win_rate": stats.win_rate,
                        "total_score": stats.total_score,
                        "best_score": stats.best_score,
                        "average_score": stats.average_score,
                        "best_time_seconds": stats.best_time_seconds,
                    }
                )

            # Cache for 10 minutes
            cache.set(cache_key, cached_leaderboard, 600)

        return Response({"count": len(cached_leaderboard), "results": cached_leaderboard})

    @action(detail=True, methods=["get"])
    def games(self, request: Request, pk: str = None) -> Response:
        """Get game history for a user with improved pagination."""
        user = self._get_user(pk)

        # Filter parameters
        status_filter = request.query_params.get("status")

        queryset = GameRecord.objects.filter(user=user).order_by("-created_at")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Use pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.get_serializer_class()(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)


__all__ = ["ManageUserView", "UserStatsViewSet"]
