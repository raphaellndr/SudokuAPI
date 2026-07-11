"""Constants for the sudoku app."""

# Maximum accepted upload size for grid-detection images (10 MB).
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# Accepted content types for uploaded images (verified against decoded bytes downstream).
SUPPORTED_IMAGE_CONTENT_TYPES = ("image/jpeg", "image/jpg", "image/png")

# Upper bound on decoded image pixels, guarding against decompression bombs.
MAX_IMAGE_PIXELS = 25_000_000  # ~25 MP

__all__ = [
    "MAX_IMAGE_PIXELS",
    "MAX_IMAGE_SIZE_BYTES",
    "SUPPORTED_IMAGE_CONTENT_TYPES",
]
