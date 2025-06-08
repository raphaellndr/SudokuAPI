"""URL mappings for the user API."""

from django.urls import path

from app.user.views import ManageUserView, UserMeStatsView, UserStatsViewSet

app_name = "users"

urlpatterns = [
    # Current user endpoint
    path("me/", ManageUserView.as_view(), name="me"),
    path("me/stats/refresh/", UserMeStatsView.as_view(), name="me-stats-refresh"),
    # Current user stats endpoints (using "me" as identifier)
    path(
        "me/stats/",
        UserStatsViewSet.as_view({"get": "stats"}),
        name="me-stats",
    ),
    path(
        "me/stats/daily/",
        UserStatsViewSet.as_view({"get": "daily_stats"}),
        name="me-daily-stats",
    ),
    path(
        "me/stats/weekly/",
        UserStatsViewSet.as_view({"get": "weekly_stats"}),
        name="me-weekly-stats",
    ),
    path(
        "me/stats/monthly/",
        UserStatsViewSet.as_view({"get": "monthly_stats"}),
        name="me-monthly-stats",
    ),
    path(
        "me/stats/yearly/",
        UserStatsViewSet.as_view({"get": "yearly_stats"}),
        name="me-yearly-stats",
    ),
    path(
        "me/games/",
        UserStatsViewSet.as_view({"get": "games"}),
        name="me-games",
    ),
    # User-specific stats endpoints (using UUID)
    path(
        "<uuid:pk>/stats/",
        UserStatsViewSet.as_view({"get": "stats"}),
        name="user-stats",
    ),
    path(
        "<uuid:pk>/stats/daily/",
        UserStatsViewSet.as_view({"get": "daily_stats"}),
        name="user-daily-stats",
    ),
    path(
        "<uuid:pk>/stats/weekly/",
        UserStatsViewSet.as_view({"get": "weekly_stats"}),
        name="user-weekly-stats",
    ),
    path(
        "<uuid:pk>/stats/monthly/",
        UserStatsViewSet.as_view({"get": "monthly_stats"}),
        name="user-monthly-stats",
    ),
    path(
        "<uuid:pk>/stats/yearly/",
        UserStatsViewSet.as_view({"get": "yearly_stats"}),
        name="user-yearly-stats",
    ),
    path(
        "<uuid:pk>/games/",
        UserStatsViewSet.as_view({"get": "games"}),
        name="user-games",
    ),
    # Public/leaderboard endpoints
    path(
        "stats/leaderboard/",
        UserStatsViewSet.as_view({"get": "leaderboard"}),
        name="stats-leaderboard",
    ),
]
