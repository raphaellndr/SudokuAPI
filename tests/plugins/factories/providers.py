"""Custom providers."""

from random import SystemRandom

from faker import providers


class SudokuGridProvider(providers.BaseProvider):
    """Create a custom provider to instantiate a Sudoku grid."""

    def string_grid(self, size=81):
        """Generates a string of numeric characters of the specified size."""
        return "".join(SystemRandom().choices("0123456789", k=size))
