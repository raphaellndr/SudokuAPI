"""Views for the user API."""

from calendar import month_name
from datetime import date, timedelta
from typing import Any

from django.db.models import Min, Sum
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from app.user.serializers import (
    DailyStatsRangeSerializer,
    DailyUserStatsSerializer,
    GameResultSerializer,
    MonthlyStatsSerializer,
    UserSerializer,
    UserStatsSerializer,
    UserWithDailyStatsSerializer,
    WeeklyStatsSerializer,
)

from .models import DailyUserStats, User, UserStats


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


class UserWithStatsView(generics.RetrieveAPIView[User]):
    """Retrieves user with comprehensive stats data."""

    queryset = User.objects.all()
    serializer_class = UserWithDailyStatsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        """Retrieves and returns the authenticated user.

        :return: User.
        """
        return self.request.user  # type: ignore


class UserStatsViewSet(ViewSet):
    """ViewSet for user statistics operations."""

    permission_classes = [permissions.IsAuthenticated]

    def get_user_stats(self) -> UserStats:
        """Get user stats for the authenticated user."""
        return self.request.user.stats

    @action(detail=False, methods=["get"])
    def overview(self, request) -> Response:
        """Gets overall user statistics."""
        stats = self.get_user_stats()
        serializer = UserStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def record_game(self, request) -> Response:
        """Records a game result."""
        serializer = GameResultSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            won = serializer.validated_data["won"]
            time_seconds = serializer.validated_data["time_seconds"]

            # Record in daily stats
            daily_stats = DailyUserStats.get_or_create_today(user)
            daily_stats.record_game(won, time_seconds)

            # Update aggregated stats
            user_stats = self.get_user_stats()
            user_stats.update_from_daily_stats()

            return Response(
                {
                    "message": "Game recorded successfully",
                    "daily_stats": DailyUserStatsSerializer(daily_stats).data,
                    "overall_stats": UserStatsSerializer(user_stats).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def daily(self, request) -> Response:
        """Gets daily statistics."""
        user = request.user

        # Check if date range is provided
        serializer = DailyStatsRangeSerializer(data=request.query_params)
        if serializer.is_valid():
            start_date = serializer.validated_data["start_date"]
            end_date = serializer.validated_data["end_date"]
        else:
            # Default to last 30 days
            end_date = date.today()
            start_date = end_date - timedelta(days=29)

        daily_stats = DailyUserStats.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).order_by("date")

        serializer = DailyUserStatsSerializer(daily_stats, many=True)
        return Response({"start_date": start_date, "end_date": end_date, "stats": serializer.data})

    @action(detail=False, methods=["get"])
    def weekly(self, request) -> Response:
        """Gets weekly aggregated statistics."""
        user = request.user
        weeks_back = int(request.query_params.get("weeks", 12))  # Default 12 weeks

        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks_back)

        # Get all daily stats in the range
        daily_stats = DailyUserStats.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).order_by("date")

        # Group by week
        weekly_data: list[dict[str, Any]] = []
        current_week_start = start_date - timedelta(days=start_date.weekday())

        while current_week_start <= end_date:
            week_end = current_week_start + timedelta(days=6)
            week_stats = daily_stats.filter(date__gte=current_week_start, date__lte=week_end)

            if week_stats.exists():
                aggregated = week_stats.aggregate(
                    total_games=Sum("games_played"),
                    total_won=Sum("games_won"),
                    total_lost=Sum("games_lost"),
                    total_time=Sum("total_time_seconds"),
                    best_time=Min("best_time_seconds"),
                )

                total_games = aggregated["total_games"] or 0
                total_won = aggregated["total_won"] or 0
                total_time = aggregated["total_time"] or 0

                weekly_data.append(
                    {
                        "week_start": current_week_start,
                        "week_end": week_end,
                        "games_played": total_games,
                        "games_won": total_won,
                        "games_lost": aggregated["total_lost"] or 0,
                        "win_rate": round(
                            (total_won / total_games * 100) if total_games > 0 else 0, 2
                        ),
                        "total_time_seconds": total_time,
                        "average_time_seconds": round(
                            total_time / total_games if total_games > 0 else 0, 2
                        ),
                        "best_time_seconds": aggregated["best_time"],
                    }
                )

            current_week_start += timedelta(weeks=1)

        serializer = WeeklyStatsSerializer(weekly_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def monthly(self, request) -> Response:
        """Gets monthly aggregated statistics."""
        user = request.user
        months_back = int(request.query_params.get("months", 12))  # Default 12 months

        end_date = date.today()
        start_date = date(end_date.year, end_date.month, 1) - timedelta(days=1)
        for _ in range(months_back - 1):
            start_date = date(start_date.year, start_date.month, 1) - timedelta(days=1)
        start_date = date(start_date.year, start_date.month, 1)

        # Get all daily stats in the range
        daily_stats = DailyUserStats.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        )

        # Group by month
        monthly_data: list[dict[str, Any]] = []
        current_date = start_date

        while current_date <= end_date:
            month_start = date(current_date.year, current_date.month, 1)
            # Get last day of month
            if current_date.month == 12:
                month_end = date(current_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)

            month_stats = daily_stats.filter(date__gte=month_start, date__lte=month_end)

            if month_stats.exists():
                aggregated = month_stats.aggregate(
                    total_games=Sum("games_played"),
                    total_won=Sum("games_won"),
                    total_lost=Sum("games_lost"),
                    total_time=Sum("total_time_seconds"),
                    best_time=Min("best_time_seconds"),
                )

                total_games = aggregated["total_games"] or 0
                total_won = aggregated["total_won"] or 0
                total_time = aggregated["total_time"] or 0

                monthly_data.append(
                    {
                        "year": current_date.year,
                        "month": current_date.month,
                        "month_name": month_name[current_date.month],
                        "games_played": total_games,
                        "games_won": total_won,
                        "games_lost": aggregated["total_lost"] or 0,
                        "win_rate": round(
                            (total_won / total_games * 100) if total_games > 0 else 0, 2
                        ),
                        "total_time_seconds": total_time,
                        "average_time_seconds": round(
                            total_time / total_games if total_games > 0 else 0, 2
                        ),
                        "best_time_seconds": aggregated["best_time"],
                    }
                )

            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)

        serializer = MonthlyStatsSerializer(monthly_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def today(self, request) -> Response:
        """Gets today's statistics."""
        user = request.user
        today_stats = DailyUserStats.get_or_create_today(user)
        serializer = DailyUserStatsSerializer(today_stats)
        return Response(serializer.data)


__all__ = ["ManageUserView", "UserStatsViewSet", "UserWithStatsView"]
