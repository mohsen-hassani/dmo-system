"""
Tests for utility functions.
"""

from datetime import date

import pytest

from dmo_core.utils import (
    calculate_completion_rate,
    calculate_streaks,
    date_range,
    days_in_month,
)


class TestDateRange:
    """Tests for date_range function."""

    def test_single_day(self) -> None:
        """Test range of a single day."""
        result = date_range(date(2026, 1, 1), date(2026, 1, 1))
        assert result == [date(2026, 1, 1)]

    def test_multiple_days(self) -> None:
        """Test range of multiple days."""
        result = date_range(date(2026, 1, 1), date(2026, 1, 5))
        assert len(result) == 5
        assert result[0] == date(2026, 1, 1)
        assert result[-1] == date(2026, 1, 5)

    def test_invalid_range(self) -> None:
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError):
            date_range(date(2026, 1, 5), date(2026, 1, 1))


class TestDaysInMonth:
    """Tests for days_in_month function."""

    def test_january(self) -> None:
        assert days_in_month(2026, 1) == 31

    def test_february_non_leap(self) -> None:
        assert days_in_month(2026, 2) == 28

    def test_february_leap(self) -> None:
        assert days_in_month(2024, 2) == 29

    def test_april(self) -> None:
        assert days_in_month(2026, 4) == 30


class TestCalculateStreaks:
    """Tests for calculate_streaks function."""

    def test_empty_dates(self) -> None:
        """Test with no dates."""
        current, longest = calculate_streaks(set(), [])
        assert current == 0
        assert longest == 0

    def test_no_completions(self) -> None:
        """Test with dates but no completions."""
        all_dates = [date(2026, 1, d) for d in range(1, 6)]
        current, longest = calculate_streaks(set(), all_dates)
        assert current == 0
        assert longest == 0

    def test_all_completed(self) -> None:
        """Test when all days are completed."""
        all_dates = [date(2026, 1, d) for d in range(1, 6)]
        completed = set(all_dates)

        current, longest = calculate_streaks(completed, all_dates)
        assert current == 5
        assert longest == 5

    def test_streak_in_middle(self) -> None:
        """Test streak calculation with gap."""
        all_dates = [date(2026, 1, d) for d in range(1, 11)]
        # Complete: 1, 2, 3, skip 4, 5, 6, 7, 8, skip 9, 10
        completed = {
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 1, 3),
            date(2026, 1, 5),
            date(2026, 1, 6),
            date(2026, 1, 7),
            date(2026, 1, 8),
            date(2026, 1, 10),
        }

        current, longest = calculate_streaks(completed, all_dates)

        assert longest == 4  # Days 5-8
        assert current == 1  # Only day 10

    def test_current_streak_broken(self) -> None:
        """Test current streak is 0 when last day is not completed."""
        all_dates = [date(2026, 1, d) for d in range(1, 6)]
        completed = {date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)}
        # Days 4, 5 not completed

        current, longest = calculate_streaks(completed, all_dates)

        assert longest == 3
        assert current == 0  # Broken by days 4, 5


class TestCalculateCompletionRate:
    """Tests for calculate_completion_rate function."""

    def test_zero_total(self) -> None:
        """Test with zero total days."""
        assert calculate_completion_rate(0, 0) == 0.0

    def test_full_completion(self) -> None:
        """Test 100% completion."""
        assert calculate_completion_rate(10, 10) == 1.0

    def test_partial_completion(self) -> None:
        """Test partial completion."""
        rate = calculate_completion_rate(7, 10)
        assert rate == pytest.approx(0.7, abs=0.001)

    def test_rounding(self) -> None:
        """Test that rate is rounded to 4 decimal places."""
        rate = calculate_completion_rate(1, 3)
        assert rate == pytest.approx(0.3333, abs=0.0001)
