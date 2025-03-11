"""Sudoku factory."""

from collections.abc import Callable

import factory
import pytest
from core.models import Sudoku, User

from .providers import SudokuGridProvider

factory.Faker.add_provider(SudokuGridProvider)


class _SudokuFactory(factory.django.DjangoModelFactory):
    """Sudoku factory."""

    class Meta:
        """Sudoku factory Meta class ."""

        model = Sudoku

    title = "sudoku title"
    difficulty = factory.Iterator(["Unknown", "Easy", "Medium", "Hard"])
    grid = factory.Faker("string_grid", size=81)


@pytest.fixture
def create_sudokus(create_user) -> Callable:
    """Pytest fixture for creating a batch of new sudokus."""

    def _factory(
        size: int = 10, user: User | None = None, difficulty: str = "Unknown", **kwargs
    ) -> Sudoku:
        if user is None:
            user = create_user()
        return _SudokuFactory.create_batch(size=size, user=user, difficulty=difficulty, **kwargs)

    return _factory


@pytest.fixture
def create_sudoku(create_sudokus, create_user) -> Callable:
    """Pytest fixture for creating a new sudoku."""

    def _factory(user: User | None = None, difficulty: str = "Unknown", **kwargs) -> Sudoku:
        if user is None:
            user = create_user()
        return create_sudokus(size=1, user=user, difficulty=difficulty, **kwargs)[0]

    return _factory
