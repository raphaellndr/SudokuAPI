"""Sudoku factory."""

from collections.abc import Callable

import factory
import pytest
from sudoku.models import Sudoku, SudokuSolution
from user.models import User

from .providers import SudokuGridProvider

factory.Faker.add_provider(SudokuGridProvider)


class _SudokuFactory(factory.django.DjangoModelFactory):
    """Sudoku factory."""

    class Meta:
        """Sudoku factory Meta class ."""

        model = Sudoku

    title = "sudoku title"
    difficulty = factory.Iterator(["unknown", "easy", "medium", "hard"])
    grid = factory.Faker("string_grid", size=81)


@pytest.fixture
def create_sudokus() -> Callable:
    """Pytest fixture for creating a batch of new sudokus."""

    def _factory(size: int = 10, user: User | None = None, **kwargs) -> Sudoku:
        return _SudokuFactory.create_batch(size=size, user=user, **kwargs)

    return _factory


@pytest.fixture
def create_sudoku(create_sudokus) -> Callable:
    """Pytest fixture for creating a new sudoku."""

    def _factory(user: User | None = None, **kwargs) -> Sudoku:
        return create_sudokus(size=1, user=user, **kwargs)[0]

    return _factory


class _SudokuSolutionFactory(factory.django.DjangoModelFactory):
    """Sudoku solution factory."""

    class Meta:
        """Sudoku solution factory Meta class."""

        model = SudokuSolution

    grid = factory.Faker("string_grid", size=81)


@pytest.fixture
def create_sudoku_solution() -> Callable:
    """Pytest fixture for creating a new sudoku solution."""

    def _factory(sudoku: Sudoku | None, **kwargs) -> SudokuSolution:
        return _SudokuSolutionFactory.create(sudoku=sudoku, **kwargs)

    return _factory
