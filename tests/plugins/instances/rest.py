"""Client fixture for testing."""

import pytest
from core.models import User
from django.test import Client


@pytest.fixture
def client() -> Client:
    """Creates an `Client` for testing. If a user is specified, authenticates it to the client."""

    def _factory(user: User | None = None) -> Client:
        client = Client()
        if user is not None:
            client.force_login(user=user)
        return client

    return _factory
