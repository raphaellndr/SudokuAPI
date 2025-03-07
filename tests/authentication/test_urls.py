"""Tests authentication's URLs."""

from django.urls import resolve, reverse


def test_auth_register_url() -> None:
    """Tests that register's URL and view name are correct."""
    url = reverse("authentication:rest_register")

    assert url == "/api/auth/register/"
    assert resolve(url).view_name == "authentication:rest_register"


def test_auth_login_url() -> None:
    """Tests that login's URL and view name are correct."""
    url = reverse("authentication:rest_login")

    assert url == "/api/auth/login/"
    assert resolve(url).view_name == "authentication:rest_login"


def test_auth_logout_url() -> None:
    """Tests that logout's URL and view name are correct."""
    url = reverse("authentication:rest_logout")

    assert url == "/api/auth/logout/"
    assert resolve(url).view_name == "authentication:rest_logout"


def test_auth_user_url() -> None:
    """Tests that user's URL and view name are correct."""
    url = reverse("authentication:rest_user_details")

    assert url == "/api/auth/user/"
    assert resolve(url).view_name == "authentication:rest_user_details"


def test_auth_token_url() -> None:
    """Tests that token's URL and view name are correct."""
    url = reverse("authentication:token_obtain_pair")

    assert url == "/api/auth/token/"
    assert resolve(url).view_name == "authentication:token_obtain_pair"


def test_auth_token_verify_url() -> None:
    """Tests that token verify's URL and view name are correct."""
    url = reverse("authentication:token_verify")

    assert url == "/api/auth/token/verify/"
    assert resolve(url).view_name == "authentication:token_verify"


def test_auth_token_refresh_url() -> None:
    """Tests that token refresh's URL and view name are correct."""
    url = reverse("authentication:token_refresh")

    assert url == "/api/auth/token/refresh/"
    assert resolve(url).view_name == "authentication:token_refresh"


def test_auth_google_url() -> None:
    """Tests that google's URL and view name are correct."""
    url = reverse("authentication:google_login")

    assert url == "/api/auth/google/"
    assert resolve(url).view_name == "authentication:google_login"
