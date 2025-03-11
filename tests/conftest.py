import pytest
from django.core.management import call_command

pytest_plugins = [
    "tests.plugins.factories.user",
    "tests.plugins.factories.sudoku",
    "tests.plugins.instances.clients",
    "tests.plugins.instances.payloads",
]


@pytest.fixture(autouse=True)
def db_flush_data(django_db_setup, django_db_blocker) -> None:
    """Flushes data before after test."""
    with django_db_blocker.unblock():
        call_command("flush", "--no-input")
