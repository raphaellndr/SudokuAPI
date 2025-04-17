"""User factory."""

from collections.abc import Callable

import factory
import pytest

from app.user.models import User


class _UserFactory(factory.django.DjangoModelFactory):
    """User factory."""

    class Meta:
        """User factory Meta class."""

        model = User

    username = factory.Sequence(lambda n: f"username{n}")
    email = factory.Sequence(lambda n: f"email{n}@example.com")
    password = factory.django.Password("pw")


@pytest.fixture
def create_users(transactional_db: None) -> Callable:
    """Pytest fixture for creating a batch of new users."""

    def _factory(size: int = 10, **kwargs) -> list[User]:
        return _UserFactory.create_batch(size=size, **kwargs)

    return _factory


@pytest.fixture
def create_user(create_users) -> Callable:
    """Pytest fixture for creating a new user."""

    def _factory(**kwargs) -> User:
        return create_users(size=1, **kwargs)[0]

    return _factory


class _SuperUserFactory(_UserFactory):
    """Superuser factory."""

    is_staff = True
    is_superuser = True


@pytest.fixture
def create_superuser(transactional_db: None) -> Callable:
    """Pytest fixture for creating a new superuser."""

    def _factory(**kwargs) -> User:
        return _SuperUserFactory(**kwargs)

    return _factory
