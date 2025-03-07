"""APIClient fixtures for testing."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def unauthenticated_client() -> APIClient:
    """Creates an unauthenticated client for testing."""
    return APIClient()


@pytest.fixture
def authenticated_client(transactional_db, create_user) -> APIClient:
    """Creates an authenticated client for testing."""
    client = APIClient()
    user = create_user()
    client.force_authenticate(user=user)
    return client
