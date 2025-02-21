"""Tests for the Django admin notifications."""

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse


class AdminTests(TestCase):
    """Tests for the Django admin."""

    def setUp(self) -> None:
        """Sets up tests by creating a user and a client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="aminpassword123",
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="userpassword123",
            name="Test user",
        )

    def test_users_listed(self) -> None:
        """Tests that users are listed on the user page."""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self) -> None:
        """Tests that the user edit page works."""
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        assert res.status_code == 200

    def test_create_user_page(self) -> None:
        """Tests that the create user page works."""
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        assert res.status_code == 200
