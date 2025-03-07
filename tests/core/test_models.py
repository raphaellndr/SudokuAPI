import pytest
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError


def test_create_user(create_user) -> None:
    """Tests creating a new user."""
    user = create_user()

    assert user.username == "username0"
    assert user.email == "email0@example.com"
    assert check_password("pw", user.password)
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.parametrize(
    "username",
    [
        None,
        "",
    ],
)
def test_create_user_without_username(create_user, username: str | None) -> None:
    """Tests creating a new user without a username."""
    user = create_user(username=username)

    assert user.username == username
    assert user.email
    assert check_password("pw", user.password)
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


def test_create_user_without_email(create_user) -> None:
    """Tests creating a new user without an email.

    :raises IntegrityError: cannot create a new user without an email.
    """
    with pytest.raises(IntegrityError):
        create_user(email=None)


def test_create_user_without_password(create_user) -> None:
    """Tests creating a new user without a password results in the user not having a usable
    password.
    """
    user = create_user(password=None)

    assert user.has_usable_password() is not True
    assert user.username
    assert user.email
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


def test_create_superuser(create_superuser) -> None:
    """Tests creating a new superuser."""

    superuser = create_superuser()

    assert superuser.username
    assert superuser.email
    assert check_password("pw", superuser.password)
    assert superuser.is_active is True
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
