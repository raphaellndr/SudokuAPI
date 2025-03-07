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
def create_user(transactional_db) -> Callable:
    def _factory(**kwargs) -> User:
        return UserFactory(**kwargs)

    return _factory


class SuperUserFactory(UserFactory):
    """Superuser factory."""

    is_staff = True
    is_superuser = True


@pytest.fixture
def create_superuser(transactional_db) -> Callable:
    def _factory(**kwargs) -> User:
        return SuperUserFactory(**kwargs)

    return _factory
