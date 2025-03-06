"""Tests for the user API."""

from typing import Any

from core.models import User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
ME_URL = reverse("user:me")


def create_user(**params: Any) -> User:
    """Creates and returns a new user.

    :param params: User parameters.
    :return: User object.
    """
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Tests for the public features of the user API."""

    def setUp(self) -> None:
        """Sets up tests."""
        self.client = APIClient()

    def test_create_user_success(self) -> None:
        """Tests that creating a user is successful."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "test name",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        assert res.status_code == status.HTTP_201_CREATED
        user = get_user_model().objects.get(email=payload["email"])
        assert user.check_password(payload["password"])
        assert "password" not in res.json()

    def test_user_with_email_exists_error(self) -> None:
        """Tests that an error is returned if email already exists when creating a user."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "test name",
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_too_short_error(self) -> None:
        """Tests that an error is returned if password is less than 5 chars."""
        payload = {
            "email": "test@example.com",
            "password": "1234",
            "name": "test name",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        assert not user_exists


    def test_retrieve_user_unauthorize(self) -> None:
        """Tests authentification is required for users."""
        res = self.client.get(ME_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class PrivateUserAPITests(TestCase):
    """Tests API requests that require authentification."""

    def setUp(self) -> None:
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
            username="test name",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self) -> None:
        """Tests retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        assert res.status_code == status.HTTP_200_OK
        self.assertDictContainsSubset(
            {"username": self.user.username, "email": self.user.email},
            res.json(),
        )

    def test_post_me_not_allowed(self) -> None:
        """Tests POST is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_user_profile(self) -> None:
        """Tests updating the user profile for the authenticated user."""
        payload = {"username": "Updated name", "password": "newpassword123"}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        assert self.user.username == payload["username"]
        assert self.user.check_password(payload["password"])
        assert res.status_code == status.HTTP_200_OK
