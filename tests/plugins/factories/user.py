"""User factory."""

from collections.abc import Callable

import factory
import pytest
from core.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """User factory."""

    class Meta:
        """User factory Meta class."""

        model = User

    username = factory.Sequence(lambda n: f"username{n}")
    email = factory.Sequence(lambda n: f"email{n}@example.com")
    password = factory.django.Password("pw")


@pytest.fixture
def create_user(transactional_db: None) -> Callable:
    """Pytest fixture for creating a new user."""

    def _factory(**kwargs) -> User:
        return UserFactory(**kwargs)

    return _factory


@pytest.fixture
def create_users(transactional_db: None) -> Callable:
    """Pytest fixture for creating a batch of new users."""

    def _factory(size: int = 10, **kwargs) -> list[User]:
        return UserFactory.create_batch(size=size, **kwargs)

    return _factory


class SuperUserFactory(UserFactory):
    """Superuser factory."""

    is_staff = True
    is_superuser = True


@pytest.fixture
def create_superuser(transactional_db: None) -> Callable:
    """Pytest fixture for creating a new superuser."""

    def _factory(**kwargs) -> User:
        return SuperUserFactory(**kwargs)

    return _factory
