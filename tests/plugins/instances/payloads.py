"""Fixtures returning useful payloads."""

from collections.abc import Mapping

import pytest


@pytest.fixture
def user_payload() -> Mapping[str, str]:
    """Returns a user payload for testing."""
    return {
        "username": "test_user",
        "email": "test_user@example.com",
        "password": "test_password123",
    }


@pytest.fixture
def register_user_payload(user_payload) -> Mapping[str, str]:
    """Returns a user payload for testing."""
    return {
        "username": user_payload["username"],
        "email": user_payload["email"],
        "password1": user_payload["password"],
        "password2": user_payload["password"],
    }
