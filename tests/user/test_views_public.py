"""Tests User views that don't require authentication."""

from typing import Final

import pytest
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from user.models import User

LOGIN_URL: Final[str] = reverse("authentication:rest_login")
REGISTER_USER_URL: Final[str] = reverse("authentication:rest_register")
TOKEN_OBTAIN_PAIR_URL: Final[str] = reverse("authentication:token_obtain_pair")
TOKEN_VERIFY_URL: Final[str] = reverse("authentication:token_verify")
USER_DETAILS_URL: Final[str] = reverse("authentication:rest_user_details")


def test_create_user(api_client, register_user_payload) -> None:
    """Tests that creating a new user is successful."""
    response = api_client().post(REGISTER_USER_URL, register_user_payload)

    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(**response.data["user"])
    assert user.check_password(register_user_payload["password1"])
    assert "password" not in response.data["user"]


def test_create_user_that_exists_fails(api_client, create_user, register_user_payload) -> None:
    """Tests that creating a user that already exists fails."""
    create_user(email=register_user_payload["email"])
    with pytest.raises(IntegrityError):
        api_client().post(REGISTER_USER_URL, register_user_payload)


@pytest.mark.parametrize(
    "password",
    [
        "2short",
        "123456789",
        "password123",
        "mypassword",
    ],
)
def test_password_not_valid(api_client, register_user_payload, password: str) -> None:
    """Tests that creating a user with a password that is invalid fails."""
    register_user_payload["password1"] = password
    register_user_payload["password2"] = password

    response = api_client().post(REGISTER_USER_URL, register_user_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(email=register_user_payload["email"]).exists()


@pytest.mark.parametrize(
    "email",
    [
        "invalid_email",
        "invalid_email.com",
        "invalid_email@",
        "invalid_email@.com",
        "@invalid.com",
    ],
)
def test_email_not_valid(api_client, register_user_payload, email: str) -> None:
    """Tests that creating a user with an invalid email fails."""
    register_user_payload["email"] = email

    response = api_client().post(REGISTER_USER_URL, register_user_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(email=register_user_payload["email"]).exists()


def test_create_user_without_email(api_client, register_user_payload) -> None:
    """Tests that creating a user without an email fails."""
    del register_user_payload["email"]

    response = api_client().post(REGISTER_USER_URL, register_user_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(email=register_user_payload["username"]).exists()


def test_create_user_without_username(api_client, register_user_payload) -> None:
    """Tests that creating a user without a username is successful."""
    del register_user_payload["username"]

    response = api_client().post(REGISTER_USER_URL, register_user_payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email=register_user_payload["email"]).exists()


def test_create_user_without_passwords(api_client, register_user_payload) -> None:
    """Tests that creating a user without passwords fails."""
    del register_user_payload["password1"]
    del register_user_payload["password2"]

    response = api_client().post(REGISTER_USER_URL, register_user_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(email=register_user_payload["email"]).exists()


def test_tokens_generated_for_user(api_client, create_user, user_payload) -> None:
    """Tests that a token pair is generated for a user."""
    create_user(**user_payload)

    response = api_client().post(TOKEN_OBTAIN_PAIR_URL, user_payload)

    assert response.status_code == status.HTTP_200_OK
    assert all(item in response.data for item in ["access", "refresh"])


def test_tokens_not_generated_for_invalid_credentials(
    api_client, create_user, user_payload
) -> None:
    """Tests that a token pair is not generated when given invalid credentials."""
    create_user(**user_payload)

    user_payload["password"] = "wrong_password"
    response = api_client().post(TOKEN_OBTAIN_PAIR_URL, user_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not all(item in response.data for item in ["access", "refresh"])


def test_tokens_not_generated_for_nonexistent_user(api_client, user_payload) -> None:
    """Tests that a token pair is not generated when given a nonexistent user."""
    response = api_client().post(TOKEN_OBTAIN_PAIR_URL, user_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not all(item in response.data for item in ["access", "refresh"])


@pytest.mark.parametrize(
    "email,password",
    [
        ("email@example.com", ""),
        ("", "test_password123"),
    ],
)
def test_tokens_not_generated_with_missing_field(api_client, email: str, password: str) -> None:
    """Tests that email and password are required."""
    response = api_client().post(TOKEN_OBTAIN_PAIR_URL, {"email": email, "password": password})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not all(item in response.data for item in ["access", "refresh"])


def test_token_verification_success(api_client, create_user, user_payload) -> None:
    """Tests that a token can be verified successfully."""
    create_user(**user_payload)

    response = api_client().post(TOKEN_OBTAIN_PAIR_URL, user_payload)

    for token in ["access", "refresh"]:
        access_token = response.data[token]

        res = api_client().post(TOKEN_VERIFY_URL, {"token": access_token})
        assert res.status_code == status.HTTP_200_OK


def test_cannot_retrieve_user_if_unauthenticated(api_client) -> None:
    """Tests that a user can't retrieve their details if not authenticated."""
    response = api_client().get(USER_DETAILS_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_login(api_client, register_user_payload, user_payload) -> None:
    """Tests that a user can login successfully."""
    api_client().post(REGISTER_USER_URL, register_user_payload)
    response = api_client().post(LOGIN_URL, user_payload)

    assert response.status_code == status.HTTP_200_OK


def test_user_cannot_login_if_not_registered(api_client, user_payload) -> None:
    """Tests that a user cannot login if account does not exist."""
    response = api_client().post(LOGIN_URL, user_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
