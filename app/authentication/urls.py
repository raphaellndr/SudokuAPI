"""URL mappings for the authentication API."""

from typing import Final

from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from dj_rest_auth.views import LogoutView
from django.urls import path
from django.urls.resolvers import URLPattern
from django.urls.resolvers import URLResolver
from rest_framework_simplejwt.views import TokenVerifyView
from user.views import ManageUserView

from authentication import views

app_name: Final[str] = "authentication"

urlpatterns: list[URLResolver | URLPattern] = [
    path("register/", RegisterView.as_view(), name="rest_register"),
    path("login/", LoginView.as_view(), name="rest_login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("user/", ManageUserView.as_view(), name="rest_user_details"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/refresh/", get_refresh_view().as_view(), name="token_refresh"),  # type: ignore
    path("google/", views.GoogleLoginView.as_view(), name="google_login"),
]
