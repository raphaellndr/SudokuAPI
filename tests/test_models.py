"""Tests for the models of the core app."""

from core.models import Sudoku, User
from django.contrib.auth import get_user_model
from django.test import TestCase


def _sample_user(
    email: str = "user@example.com",
    password: str = "password123",
) -> User:
    """Creates a sample user."""
    return get_user_model().objects.create_user(email, password)


class ModelsTests(TestCase):
    """Tests for the models of the core app."""

    def test_new_user_with_email(self) -> None:
        """Tests that creating a new user with an email is successful."""
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        assert user.email == email
        assert user.check_password(password)

    def test_new_user_without_email(self) -> None:
        """Tests that creating a user without an email raises a `ValueError`."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_email_normalization(self) -> None:
        """Tests that the email for a new user is normalized."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            assert user.email == expected

    def test_new_superuser(self) -> None:
        """Tests creating a new superuser."""
        user = get_user_model().objects.create_superuser(
            username="testadmin",
            email="testadmin@example.com",
            password="testadmin123",
        )

        assert user.is_superuser
        assert user.is_staff

    def test_create_sudoku(self) -> None:
        """Tests creating a new sudoku."""
        user = _sample_user()
        sudoku = Sudoku.objects.create(
            user=user,
            title="Sample sudoku",
            difficulty="EASY",
            grid="." * 81,
        )

        assert str(sudoku) == sudoku.title
