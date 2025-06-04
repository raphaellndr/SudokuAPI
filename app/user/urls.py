"""URL mappings for the user API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from app.user.views import (
    ManageUserView,
    UserStatsViewSet,
    UserWithStatsView,
)

router = DefaultRouter()
router.register(r"stats", UserStatsViewSet, basename="user-stats")

app_name = "user"

urlpatterns = [
    # User management endpoints
    path("me/", ManageUserView.as_view(), name="me"),
    path("me/with-stats/", UserWithStatsView.as_view(), name="me-with-stats"),
    # Stats endpoints (via ViewSet router)
    path("", include(router.urls)),
]
