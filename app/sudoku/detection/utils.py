from collections.abc import Sequence

import cv2
import numpy as np
from cv2.typing import MatLike


def preprocess_image(image: MatLike) -> MatLike:
    """Preprocesses the input image.

    This function converts the image to grayscale, applies Gaussian blur, and then applies adaptive
    thresholding.

    Args:
        image (MatLike): input image.

    Returns:
        MatLike: preprocessed image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1)
    thresh = cv2.adaptiveThreshold(blurred, 255, 1, 1, 11, 2)
    return thresh


def get_biggest_contour(contours: Sequence[MatLike]) -> np.ndarray:
    """Finds the biggest contour in the image.

    Args:
        contours (Sequence[MatLike]): input contours.

    Returns:
        np.ndarray: the biggest contour found in the image.
    """
    biggest = np.array([])
    max_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 50:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4 and area > max_area:
                biggest = approx
                max_area = area

    return biggest


def reorder(points: np.ndarray) -> np.ndarray:
    """Reorders the points in a contour to a specific order.

    Args:
        points (np.ndarray): input points.

    Returns:
        np.ndarray: reordered points.
    """
    points = points.reshape((4, 2))
    new_points = np.zeros((4, 1, 2), dtype=np.int32)

    add = points.sum(1)
    new_points[0] = points[np.argmin(add)]
    new_points[3] = points[np.argmax(add)]

    diff = np.diff(points, axis=1)
    new_points[1] = points[np.argmin(diff)]
    new_points[2] = points[np.argmax(diff)]

    return new_points


def split_into_boxes(image: MatLike) -> list[MatLike]:
    """Splits the image into 81 boxes.

    Args:
        image (MatLike): input image.

    Returns:
        list[MatLike]: list of 81 boxes.
    """
    rows = np.vsplit(image, 9)
    boxes = []
    for row in rows:
        cols = np.hsplit(row, 9)
        for box in cols:
            boxes.append(box)
    return boxes


__all__ = [
    "get_biggest_contour",
    "preprocess_image",
    "reorder",
    "split_into_boxes",
]
