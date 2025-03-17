"""Sudoku model tests."""

from sudoku.choices import SudokuDifficultyChoices, SudokuStatusChoices


def test_create_sudoku(create_sudoku) -> None:
    """Tests creating a new sudoku."""
    sudoku = create_sudoku()

    assert sudoku.user
    assert sudoku.title == "sudoku title"
    assert sudoku.difficulty in SudokuDifficultyChoices.values
    assert len(sudoku.grid) == 81
    assert sudoku.status in SudokuStatusChoices.PENDING
    assert str(sudoku) == "sudoku title"
