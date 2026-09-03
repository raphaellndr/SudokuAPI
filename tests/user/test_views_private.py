"""Tests User views that require authentication."""

import uuid
from typing import Final

import pytest
from django.urls import reverse
from rest_framework import status

LOGOUT_URL: Final[str] = reverse("authentication:rest_logout")
USER_DETAILS_URL: Final[str] = reverse("users:me")


@pytest.fixture
def authenticated_client(api_client, create_user, user_payload):
    """Sets up a client for authenticated tests."""
    user = create_user(**user_payload)
    return api_client(user=user)


def test_retrieve_profile(authenticated_client, user_payload) -> None:
    """Tests that retrieving a profile is successful when authenticated."""
    response = authenticated_client.get(USER_DETAILS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == user_payload["username"]
    assert response.data["email"] == user_payload["email"]


def test_cannot_post_on_detail_url(authenticated_client) -> None:
    """Tests that attempting to post to the user details URL fails when authenticated."""
    response = authenticated_client.post(USER_DETAILS_URL, {})

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_update_user_profile(authenticated_client) -> None:
    """Tests that updating a user's profile is successful when authenticated."""
    new_email = "new_email@example.com"
    response = authenticated_client.patch(USER_DETAILS_URL, {"email": new_email})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == new_email


def test_retrieve_user_by_id(api_client, create_user) -> None:
    """Tests that an authenticated user can retrieve another user by id."""
    user = create_user()
    other = create_user()

    url = reverse("users:user-detail", kwargs={"pk": user.id})
    response = api_client(other).get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(user.id)
    assert response.data["username"] == user.username


def test_retrieve_unknown_user_by_id_fails(api_client, create_user) -> None:
    """Tests that retrieving a user that doesn't exist returns a 404."""
    url = reverse("users:user-detail", kwargs={"pk": uuid.uuid4()})
    response = api_client(create_user()).get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_inactive_user_by_id_fails(api_client, create_user) -> None:
    """Tests that retrieving an inactive user returns a 404."""
    inactive = create_user(is_active=False)

    url = reverse("users:user-detail", kwargs={"pk": inactive.id})
    response = api_client(create_user()).get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
