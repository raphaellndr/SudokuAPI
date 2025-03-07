"""Custom providers."""

import random

from faker import providers


class SudokuGridProvider(providers.BaseProvider):
    """Create a custom provider to instantiate a Sudoku grid."""

    def numeric_grid(self, size=81):
        """Generates a string of numeric characters of the specified size."""
        return "".join(random.choices("0123456789", k=size))
