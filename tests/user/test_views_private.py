"""Tests User views that require authentication."""

from typing import Final

import pytest
from django.urls import reverse
from rest_framework import status

LOGOUT_URL: Final[str] = reverse("authentication:rest_logout")
USER_DETAILS_URL: Final[str] = reverse("authentication:rest_user_details")


@pytest.fixture
def authenticated_client(api_client, create_user, user_payload):
    """Sets up a client for authenticated tests."""
    user = create_user(**user_payload)
    client = api_client(user=user)
    return client


def test_retrieve_profile(authenticated_client, user_payload) -> None:
    """Tests that retrieving a profile is successful when authenticated."""
    response = authenticated_client.get(USER_DETAILS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "username": user_payload["username"],
        "email": user_payload["email"],
    }


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
