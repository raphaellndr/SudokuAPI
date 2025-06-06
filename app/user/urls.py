"""URL mappings for the user API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from app.user.views import ManageUserView, UserStatsViewSet

router = DefaultRouter()
router.register(r"", UserStatsViewSet, basename="users")

app_name = "users"

urlpatterns = [
    path("me/", ManageUserView.as_view(), name="me"),
    path("", include(router.urls)),
]
