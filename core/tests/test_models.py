"""
Tests for Pydantic models validation.
"""

import pytest
from pydantic import ValidationError

from dmo_core.models import (
    ActivityCreate,
    DMOCreate,
    DMOUpdate,
    MonthSummary,
)


class TestDMOCreate:
    """Tests for DMOCreate model."""

    def test_valid_minimal(self) -> None:
        """Test creating with minimal required fields."""
        dmo = DMOCreate(name="Test DMO")
        assert dmo.name == "Test DMO"
        assert dmo.description is None
        assert dmo.timezone is None

    def test_valid_full(self) -> None:
        """Test creating with all fields."""
        dmo = DMOCreate(
            name="Test DMO",
            description="A test description",
            timezone="America/New_York",
        )
        assert dmo.name == "Test DMO"
        assert dmo.description == "A test description"
        assert dmo.timezone == "America/New_York"

    def test_name_stripped(self) -> None:
        """Test that name is stripped of whitespace."""
        dmo = DMOCreate(name="  Test DMO  ")
        assert dmo.name == "Test DMO"

    def test_empty_name_rejected(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DMOCreate(name="")
        assert "name" in str(exc_info.value)

    def test_whitespace_only_name_rejected(self) -> None:
        """Test that whitespace-only name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DMOCreate(name="   ")
        assert "name" in str(exc_info.value)

    def test_name_max_length(self) -> None:
        """Test that name over 255 chars is rejected."""
        with pytest.raises(ValidationError):
            DMOCreate(name="x" * 256)


class TestDMOUpdate:
    """Tests for DMOUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional."""
        update = DMOUpdate()
        assert update.name is None
        assert update.description is None
        assert update.timezone is None
        assert update.active is None

    def test_partial_update(self) -> None:
        """Test partial update with some fields."""
        update = DMOUpdate(name="New Name", active=False)
        assert update.name == "New Name"
        assert update.active is False
        assert update.description is None


class TestActivityCreate:
    """Tests for ActivityCreate model."""

    def test_valid_minimal(self) -> None:
        """Test with minimal fields."""
        dmo_id = 1
        activity = ActivityCreate(dmo_id=dmo_id, name="Test Activity")
        assert activity.dmo_id == dmo_id
        assert activity.name == "Test Activity"
        assert activity.order == 0

    def test_custom_order(self) -> None:
        """Test with custom order."""
        dmo_id = 1
        activity = ActivityCreate(dmo_id=dmo_id, name="Test", order=5)
        assert activity.order == 5

    def test_negative_order_rejected(self) -> None:
        """Test that negative order is rejected."""
        with pytest.raises(ValidationError):
            ActivityCreate(dmo_id=1, name="Test", order=-1)


class TestMonthSummary:
    """Tests for MonthSummary model."""

    def test_completion_rate_bounds(self) -> None:
        """Test that completion_rate must be between 0 and 1."""
        # Valid
        summary = MonthSummary(
            total_days=28,
            completed_days=14,
            completion_rate=0.5,
            current_streak=0,
            longest_streak=0,
            missed_days=[],
        )
        assert summary.completion_rate == 0.5

        # Invalid - over 1
        with pytest.raises(ValidationError):
            MonthSummary(
                total_days=28,
                completed_days=14,
                completion_rate=1.5,
                current_streak=0,
                longest_streak=0,
                missed_days=[],
            )

        # Invalid - negative
        with pytest.raises(ValidationError):
            MonthSummary(
                total_days=28,
                completed_days=14,
                completion_rate=-0.1,
                current_streak=0,
                longest_streak=0,
                missed_days=[],
            )
