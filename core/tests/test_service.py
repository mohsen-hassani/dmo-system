"""
Tests for DmoService business logic.
"""

from datetime import date

import pytest

from dmo_core import ActivityCreate, DMOCreate, DmoService


class TestDmoServiceReports:
    """Tests for reporting functionality."""

    async def test_get_daily_report_empty(self, memory_service: DmoService) -> None:
        """Test daily report with no DMOs."""
        report = await memory_service.get_daily_report(date(2026, 1, 15))

        assert report.date == date(2026, 1, 15)
        assert len(report.dmos) == 0

    async def test_get_daily_report_with_dmo(self, memory_service: DmoService) -> None:
        """Test daily report shows DMO status correctly."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))
        await memory_service.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Step 1", order=0)
        )
        await memory_service.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Step 2", order=1)
        )

        # Not completed
        report = await memory_service.get_daily_report(date(2026, 1, 15))
        assert len(report.dmos) == 1
        assert report.dmos[0].completed is False
        assert report.dmos[0].activities == ["Step 1", "Step 2"]

        # Mark completed
        await memory_service.mark_complete(dmo.id, date(2026, 1, 15))

        report = await memory_service.get_daily_report(date(2026, 1, 15))
        assert report.dmos[0].completed is True

    async def test_get_monthly_report(self, memory_service: DmoService) -> None:
        """Test monthly report generation."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))

        # Complete some days in February 2026
        await memory_service.mark_complete(dmo.id, date(2026, 2, 1))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 2))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 3))
        await memory_service.mark_incomplete(dmo.id, date(2026, 2, 4))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 5))

        reports = await memory_service.get_monthly_report(2026, 2, dmo.id)

        assert len(reports) == 1
        report = reports[0]

        assert report.year == 2026
        assert report.month == 2
        assert len(report.days) == 28  # February 2026 has 28 days

        assert report.summary.completed_days == 4
        assert report.summary.total_days == 28
        assert report.summary.completion_rate == pytest.approx(4 / 28, abs=0.001)

    async def test_streak_calculation(self, memory_service: DmoService) -> None:
        """Test streak calculation in monthly report."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))

        # Create a pattern: 3 days on, 1 off, 5 days on
        # Days 1, 2, 3 = complete
        await memory_service.mark_complete(dmo.id, date(2026, 2, 1))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 2))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 3))
        # Day 4 = incomplete (breaks streak)
        await memory_service.mark_incomplete(dmo.id, date(2026, 2, 4))
        # Days 5-9 = complete (longest streak = 5)
        await memory_service.mark_complete(dmo.id, date(2026, 2, 5))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 6))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 7))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 8))
        await memory_service.mark_complete(dmo.id, date(2026, 2, 9))

        reports = await memory_service.get_monthly_report(2026, 2, dmo.id)
        summary = reports[0].summary

        assert summary.longest_streak == 5
        # Current streak depends on whether days after 9 exist
        # Since no data for 10+, current streak is 0 (broken by missing days)

    async def test_dmo_summary(self, memory_service: DmoService) -> None:
        """Test DMO summary over a date range."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))

        await memory_service.mark_complete(dmo.id, date(2026, 1, 1))
        await memory_service.mark_complete(dmo.id, date(2026, 1, 2))
        await memory_service.mark_incomplete(dmo.id, date(2026, 1, 3))
        await memory_service.mark_complete(dmo.id, date(2026, 1, 4))
        await memory_service.mark_complete(dmo.id, date(2026, 1, 5))

        summary = await memory_service.get_dmo_summary(
            dmo.id, date(2026, 1, 1), date(2026, 1, 5)
        )

        assert summary.total_days == 5
        assert summary.completed_days == 4
        assert summary.completion_rate == pytest.approx(0.8, abs=0.001)
        assert summary.longest_streak == 2
        assert summary.current_streak == 2  # Days 4-5


class TestDmoServiceIdempotency:
    """Tests for idempotent operations."""

    async def test_mark_complete_idempotent(self, memory_service: DmoService) -> None:
        """Test that marking complete multiple times is safe."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))

        c1 = await memory_service.mark_complete(dmo.id, date(2026, 1, 15))
        c2 = await memory_service.mark_complete(dmo.id, date(2026, 1, 15))

        assert c1.id == c2.id
        assert c1.completed is True
        assert c2.completed is True


class TestDmoServiceActivities:
    """Tests for activity management."""

    async def test_reorder_activities(self, memory_service: DmoService) -> None:
        """Test reordering activities."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))

        a1 = await memory_service.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="First", order=0)
        )
        a2 = await memory_service.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Second", order=1)
        )
        a3 = await memory_service.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Third", order=2)
        )

        # Reorder to: Third, First, Second
        reordered = await memory_service.reorder_activities(
            dmo.id, [a3.id, a1.id, a2.id]
        )

        assert reordered[0].name == "Third"
        assert reordered[1].name == "First"
        assert reordered[2].name == "Second"

    async def test_delete_activity_no_effect_on_completions(
        self, memory_service: DmoService
    ) -> None:
        """Test that deleting activities doesn't affect completions."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))
        activity = await memory_service.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Activity")
        )

        await memory_service.mark_complete(dmo.id, date(2026, 1, 15))

        # Delete the activity
        await memory_service.delete_activity(activity.id)

        # Completion should still exist
        completion = await memory_service.get_completion(dmo.id, date(2026, 1, 15))
        assert completion is not None
        assert completion.completed is True
