"""Sudoku model tests."""


def test_create_sudoku(create_sudoku) -> None:
    """Tests creating a new sudoku."""
    sudoku = create_sudoku()

    assert sudoku.user
    assert sudoku.title
    assert sudoku.difficulty in ["Unknown", "Easy", "Medium", "Hard"]
    assert sudoku.grid
    assert str(sudoku) == "sudoku title"
