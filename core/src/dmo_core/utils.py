"""
Utility functions for the DMO-Core system.
"""

from __future__ import annotations

from calendar import monthrange
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(UTC)


def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month."""
    return monthrange(year, month)[1]


def date_range(start: date, end: date) -> list[date]:
    """
    Generate a list of dates from start to end (inclusive).

    Args:
        start: Start date (inclusive)
        end: End date (inclusive)

    Returns:
        List of date objects from start to end

    Raises:
        ValueError: If start > end
    """
    if start > end:
        raise ValueError(f"start date ({start}) must be <= end date ({end})")

    result: list[date] = []
    current = start
    while current <= end:
        result.append(current)
        current += timedelta(days=1)
    return result


def calculate_streaks(
    dates_completed: set[date],
    all_dates: Sequence[date]
) -> tuple[int, int]:
    """
    Calculate current and longest streaks from completion data.

    A streak is a sequence of consecutive days where completed == True.
    The current streak is measured backwards from the last date in all_dates.

    Args:
        dates_completed: Set of dates where DMO was completed
        all_dates: Ordered sequence of all dates in the range (must be sorted ascending)

    Returns:
        Tuple of (current_streak, longest_streak)
    """
    if not all_dates:
        return 0, 0

    # Ensure sorted for streak calculation
    sorted_dates = sorted(all_dates)

    longest_streak = 0
    current_run = 0

    for d in sorted_dates:
        if d in dates_completed:
            current_run += 1
            longest_streak = max(longest_streak, current_run)
        else:
            current_run = 0

    # Current streak: count backwards from the last date
    current_streak = 0
    for d in reversed(sorted_dates):
        if d in dates_completed:
            current_streak += 1
        else:
            break

    return current_streak, longest_streak


def calculate_completion_rate(completed_days: int, total_days: int) -> float:
    """
    Calculate completion rate as a float between 0.0 and 1.0.

    Args:
        completed_days: Number of days completed
        total_days: Total number of days in range

    Returns:
        Completion rate (0.0 to 1.0), returns 0.0 if total_days is 0
    """
    if total_days == 0:
        return 0.0
    return round(completed_days / total_days, 4)
