"""Sudoku related tasks."""

from copy import copy
from datetime import timedelta
from typing import Any

import cv2
import numpy as np
from django.utils import timezone
from sudoku_resolver.exceptions import ConsistencyError
from sudoku_resolver.sudoku import Sudoku as SudokuResolver

from config.celery import app

from .base import update_sudoku_detection, update_sudoku_status
from .choices import DetectionStatusChoices, SudokuStatusChoices
from .detection.digits_recognition import detect_digits
from .detection.utils import get_biggest_contour, preprocess_image, reorder, split_into_boxes
from .models import Sudoku, SudokuSolution

IMG_WIDTH, IMG_HEIGHT = 450, 450


def _check_consistency(sudoku_solver: SudokuResolver, /) -> bool:
    """Checks if a sudoku is consistent or not.

    :param sudoku_solver: Sudoku to check.
    :returns: True if sudoku is consistent, False otherwise.
    """
    try:
        sudoku_solver.check_consistency()
        return True
    except ConsistencyError:
        return False


@app.task
def solve_sudoku(sudoku_id: str) -> dict[str, Any]:
    """Celery task to solve a Sudoku.

    :param sudoku_id: The id of the Sudoku to solve.
    :returns: A dictionary with the status and solution id if successful.
    """
    try:
        sudoku = Sudoku.objects.get(id=sudoku_id)
        update_sudoku_status(sudoku, SudokuStatusChoices.RUNNING)

        grid = copy(sudoku.grid)
        sudoku_solver = SudokuResolver(values=grid)

        is_consistent = _check_consistency(sudoku_solver)
        if not is_consistent:
            update_sudoku_status(sudoku, SudokuStatusChoices.INVALID)
            return {"status": "failed", "error": "Inconsistent Sudoku"}

        sudoku_solver.solve()

        is_consistent = _check_consistency(sudoku_solver)
        if not is_consistent:
            update_sudoku_status(sudoku, SudokuStatusChoices.INVALID)
            return {"status": "failed", "error": "Inconsistent Sudoku solution"}

        solution_grid = sudoku_solver.to_string()
        SudokuSolution.objects.create(sudoku=sudoku, grid=solution_grid)
        update_sudoku_status(sudoku, SudokuStatusChoices.COMPLETED)

        return {"status": "completed", "solution": sudoku.solution.id}

    except Exception as e:
        update_sudoku_status(sudoku, SudokuStatusChoices.FAILED)
        return {"status": "failed", "error": str(e)}


@app.task
def cleanup_anonymous_sudokus(hours: int = 24) -> str:
    """Celery task to clean up anonymous Sudokus older than a certain number of hours.

    :param hours: The number of hours to keep anonymous Sudokus.
    :returns: A message indicating the number of deleted Sudokus.
    """
    cutoff_time = timezone.now() - timedelta(hours=hours)

    old_anonymous_sudokus = Sudoku.objects.filter(user__isnull=True, created_at__lt=cutoff_time)
    count = old_anonymous_sudokus.count()
    old_anonymous_sudokus.delete()

    return f"Deleted {count} anonymous Sudokus older than {hours} hours."


@app.task
def detect_sudoku_digits(image_data: bytes) -> dict[str, Any]:
    """Detect digits from a sudoku image using OpenCV pipeline.

    Args:
        image_data: The raw image file data.

    Returns:
        Dict containing the detected grid and processing status.
    """
    try:
        update_sudoku_detection(DetectionStatusChoices.RUNNING)

        # Convert bytes to OpenCV image
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return {"status": "error", "message": "Failed to decode image"}

        # Resize image to standard dimensions
        image = cv2.resize(image, (IMG_WIDTH, IMG_HEIGHT))

        # Preprocess the image to get binary threshold
        thresh = preprocess_image(image)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get the biggest contour (should be the sudoku grid)
        biggest_contour = get_biggest_contour(contours)

        if biggest_contour.size == 0:
            return {
                "status": "error",
                "message": "No suitable sudoku grid contour found in the image",
            }

        # Reorder the contour points for perspective transformation
        biggest_contour = reorder(biggest_contour)

        # Perform perspective transformation to get a straight view of the sudoku
        points_1 = np.float32(biggest_contour)
        points_2 = np.float32(
            [
                [0, 0],
                [IMG_WIDTH, 0],
                [0, IMG_HEIGHT],
                [IMG_WIDTH, IMG_HEIGHT],
            ]
        )
        matrix = cv2.getPerspectiveTransform(points_1, points_2)
        warped = cv2.warpPerspective(image, matrix, (IMG_WIDTH, IMG_HEIGHT))

        # Convert to grayscale for digit detection
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

        # Split the sudoku grid into individual boxes
        boxes = split_into_boxes(gray)

        # Detect digits in each box
        digits = detect_digits(boxes)

        update_sudoku_detection(DetectionStatusChoices.COMPLETED)

        return {
            "status": "success",
            "message": "Digit detection completed successfully",
            "grid": "".join(str(d) for d in digits),
        }

    except Exception as e:
        update_sudoku_detection(DetectionStatusChoices.FAILED)
        return {"status": "error", "message": f"Digit detection failed: {e!s}"}


__all__ = ["cleanup_anonymous_sudokus", "detect_sudoku", "detect_sudoku_digits", "solve_sudoku"]
