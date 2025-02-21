"""URL mappings for the user API."""

from typing import Final

from django.urls import path
from django.urls.resolvers import URLPattern
from django.urls.resolvers import URLResolver

from user import views

app_name: Final[str] = "user"

urlpatterns: list[URLResolver | URLPattern] = [
    path("create/", views.CreateUserView.as_view(), name="create"),
    path("token/", views.CreateTokenView.as_view(), name="token"),
    path("me/", views.ManageUserView.as_view(), name="me"),
]
