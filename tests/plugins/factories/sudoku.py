from collections.abc import Callable

import factory
import pytest
from core.models import Sudoku


class SudokuFactory(factory.django.DjangoModelFactory):
    """Sudoku factory."""

    class Meta:
        """Sudoku factory Meta class ."""

        model = Sudoku

    title = factory.Faker("sentence", nb_words=10)
    difficulty = factory.Iterator(["Unknown", "Easy", "Medium", "Hard"])


@pytest.fixture
def create_sudoku() -> Callable:
    def _factory(**kwargs) -> Sudoku:
        return SudokuFactory(**kwargs)

    return _factory
