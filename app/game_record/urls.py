"""Updated URL configuration for user and game record endpoints."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from app.game_record.views import GameRecordViewSet

app_name = "game_records"

router = DefaultRouter()
router.register(r"", GameRecordViewSet, basename="game-records")

urlpatterns = [
    path("", include(router.urls)),
]
