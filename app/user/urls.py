"""URL mappings for the user API."""

from django.urls import path

from app.user.views import ManageUserView, UserStatsViewSet, UserMeStatsView

app_name = "users"

urlpatterns = [
    # Current user endpoint
    path("me/", ManageUserView.as_view(), name="me"),
    path("me/stats/refresh/", UserMeStatsView.as_view(), name="me-stats-refresh"),
    
    # User-specific stats endpoints
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
    # Public/leaderboard endpoints
    path(
        "stats/leaderboard/",
        UserStatsViewSet.as_view({"get": "leaderboard"}),
        name="stats-leaderboard",
    ),
]
