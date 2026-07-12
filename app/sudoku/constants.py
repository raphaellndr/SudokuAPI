"""Constants for the sudoku app."""

# Maximum accepted upload size for grid-detection images (10 MB).
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# Accepted content types for uploaded images (verified against decoded bytes downstream).
SUPPORTED_IMAGE_CONTENT_TYPES = ("image/jpeg", "image/jpg", "image/png")

# Upper bound on decoded image pixels, guarding against decompression bombs.
MAX_IMAGE_PIXELS = 25_000_000  # ~25 MP

# Wall-clock bound on a solve: the resolver's backtracking can thrash indefinitely on
# some under-constrained grids, and a task must never stay in RUNNING forever.
SOLVE_SOFT_TIME_LIMIT_SECONDS = 30
# Hard kill backstop; must stay above the soft limit so the FAILED cleanup can run.
SOLVE_TIME_LIMIT_SECONDS = 40

__all__ = [
    "MAX_IMAGE_PIXELS",
    "MAX_IMAGE_SIZE_BYTES",
    "SOLVE_SOFT_TIME_LIMIT_SECONDS",
    "SOLVE_TIME_LIMIT_SECONDS",
    "SUPPORTED_IMAGE_CONTENT_TYPES",
]
