"""Test for the Django admin modifications."""

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status

from app.user.models import User


@pytest.fixture
def set_up_client(client, create_superuser) -> Client:
    """Sets up admin client."""
    superuser = create_superuser()
    return client(user=superuser)


def test_user_changelist(set_up_client, create_users) -> None:
    """Test that users are listed on page."""
    admin_client = set_up_client
    nb_users = 5
    create_users(size=nb_users)

    url = reverse("admin:user_user_changelist")
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    changelist = response.context["cl"]
    assert changelist.result_count == nb_users + 1
    assert changelist.full_result_count == nb_users + 1
    assert set(changelist.result_list) == set(User.objects.all())


def test_user_add(set_up_client, create_user) -> None:
    """Tests that the create user page works."""
    admin_client = set_up_client

    url = reverse("admin:user_user_add")
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK


def test_user_change(set_up_client, create_user) -> None:
    """Tests that the edit user page works."""
    admin_client = set_up_client
    user = create_user()

    url = reverse("admin:user_user_change", args=[user.id])
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
