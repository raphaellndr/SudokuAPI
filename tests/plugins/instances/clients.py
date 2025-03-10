"""Clients fixture for testing."""

import pytest
from core.models import User
from django.test import Client
from rest_framework.test import APIClient


@pytest.fixture
def client() -> Client:
    """Creates a `Client` for testing. If a user is specified, authenticates it to the client."""

    def _factory(user: User | None = None) -> Client:
        client = Client()
        if user is not None:
            client.force_login(user=user)
        return client

    return _factory


@pytest.fixture
def api_client(transactional_db) -> APIClient:
    """Creates an `APIClient` for testing. If a user is specified, authenticates it to the
    client.
    """

    def _factory(user: User | None = None) -> APIClient:
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client

    return _factory
