"""
Date Chunking Utilities
=======================

Functions for breaking large date ranges into manageable chunks
for backfill processing. This prevents API rate limiting and allows
incremental writes to the destination (crash-safe backfills).

Usage:
    from etl.core.chunking import generate_date_chunks, generate_monthly_chunks

    # Days-back mode (relative to now)
    chunks = generate_monthly_chunks(90, chunk_size_days=30)
    # Returns: [(90, 60), (60, 30), (30, 0)]

    # Explicit date range mode
    chunks = generate_date_chunks(start_date, end_date, chunk_size_days=30)
    # Returns: [(datetime1, datetime2), (datetime2, datetime3), ...]
"""

from datetime import datetime, timedelta


def generate_monthly_chunks(
    total_days: int,
    chunk_size_days: int = 30
) -> list[tuple[int, int]]:
    """
    Generate date chunks for backfill processing (days-back mode).

    Returns list of (start_days_back, end_days_back) tuples where:
    - start_days_back is the older date (further back from today)
    - end_days_back is the newer date (closer to today)

    Chunks are ordered from oldest to newest so data is written chronologically.

    Args:
        total_days: Total number of days to backfill
        chunk_size_days: Size of each chunk in days

    Returns:
        List of (start_days, end_days) tuples

    Example:
        >>> generate_monthly_chunks(90, chunk_size_days=30)
        [(90, 60), (60, 30), (30, 0)]

        This means:
        - Chunk 1: 90 days ago to 60 days ago
        - Chunk 2: 60 days ago to 30 days ago
        - Chunk 3: 30 days ago to today
    """
    chunks = []
    current_end = total_days

    while current_end > 0:
        current_start = max(0, current_end - chunk_size_days)
        chunks.append((current_end, current_start))
        current_end = current_start

    # Reverse to process oldest first (chronological order)
    chunks.reverse()
    return chunks


def generate_date_chunks(
    start_date: datetime,
    end_date: datetime,
    chunk_size_days: int = 30
) -> list[tuple[datetime, datetime]]:
    """
    Generate date chunks for backfill processing (explicit date range mode).

    Returns list of (chunk_start, chunk_end) datetime tuples.
    Chunks are ordered from oldest to newest so data is written chronologically.

    Args:
        start_date: Start of the date range
        end_date: End of the date range
        chunk_size_days: Size of each chunk in days

    Returns:
        List of (chunk_start, chunk_end) datetime tuples

    Example:
        >>> from datetime import datetime
        >>> start = datetime(2024, 1, 1)
        >>> end = datetime(2024, 3, 1)
        >>> generate_date_chunks(start, end, chunk_size_days=30)
        [
            (datetime(2024, 1, 1), datetime(2024, 1, 31)),
            (datetime(2024, 1, 31), datetime(2024, 3, 1))
        ]
    """
    chunks = []
    current_start = start_date

    while current_start < end_date:
        current_end = min(
            current_start + timedelta(days=chunk_size_days),
            end_date
        )
        chunks.append((current_start, current_end))
        current_start = current_end

    return chunks


def estimate_chunk_count(
    total_days: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    chunk_size_days: int = 30
) -> int:
    """
    Estimate the number of chunks for a backfill operation.

    Useful for progress estimation and resource planning.

    Args:
        total_days: Total days to backfill (days-back mode)
        start_date: Start date (explicit mode)
        end_date: End date (explicit mode)
        chunk_size_days: Size of each chunk

    Returns:
        Estimated number of chunks
    """
    if start_date and end_date:
        total_days = (end_date - start_date).days

    if total_days is None:
        return 0

    return (total_days + chunk_size_days - 1) // chunk_size_days
