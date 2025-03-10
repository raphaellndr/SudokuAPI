"""Sudoku factory."""

from collections.abc import Callable

import factory
import pytest
from core.models import Sudoku

from .providers import SudokuGridProvider

factory.Faker.add_provider(SudokuGridProvider)


class SudokuFactory(factory.django.DjangoModelFactory):
    """Sudoku factory."""

    class Meta:
        """Sudoku factory Meta class ."""

        model = Sudoku

    title = "sudoku title"
    difficulty = factory.Iterator(["Unknown", "Easy", "Medium", "Hard"])
    grid = factory.Faker("numeric_grid", size=81)


@pytest.fixture
def create_sudoku(transactional_db: None, create_user) -> Callable:
    """Pytest fixture for creating a new sudoku."""

    def _factory(**kwargs) -> Sudoku:
        user = create_user()
        return SudokuFactory(user=user, **kwargs)

    return _factory
