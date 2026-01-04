"""
Integration tests verifying end-to-end workflows.
"""

from datetime import date

from dmo_core import ActivityCreate, DMOCreate, DmoService


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    async def test_complete_workflow(self, sqlite_service: DmoService) -> None:
        """Test a complete real-world workflow."""
        # 1. Create a DMO
        dmo = await sqlite_service.create_dmo(
            DMOCreate(
                name="Morning Routine",
                description="My daily morning ritual",
                timezone="America/New_York",
            )
        )
        assert dmo.name == "Morning Routine"

        # 2. Add activities
        activities = [
            ("Wake up at 6 AM", 0),
            ("Meditate 10 minutes", 1),
            ("Exercise 30 minutes", 2),
            ("Healthy breakfast", 3),
            ("Review daily goals", 4),
        ]

        for name, order in activities:
            await sqlite_service.create_activity(
                ActivityCreate(dmo_id=dmo.id, name=name, order=order)
            )

        # 3. Track a week of completions
        test_week = [
            (date(2026, 2, 1), True, "Great start!"),
            (date(2026, 2, 2), True, None),
            (date(2026, 2, 3), False, "Slept in"),
            (date(2026, 2, 4), True, None),
            (date(2026, 2, 5), True, "Back on track"),
            (date(2026, 2, 6), True, None),
            (date(2026, 2, 7), True, "Perfect week ending!"),
        ]

        for d, completed, note in test_week:
            if completed:
                await sqlite_service.mark_complete(dmo.id, d, note)
            else:
                await sqlite_service.mark_incomplete(dmo.id, d, note)

        # 4. Get daily report for a specific day
        report = await sqlite_service.get_daily_report(date(2026, 2, 5))

        assert len(report.dmos) == 1
        assert report.dmos[0].completed is True
        assert report.dmos[0].note == "Back on track"
        assert len(report.dmos[0].activities) == 5

        # 5. Get monthly report
        monthly_reports = await sqlite_service.get_monthly_report(2026, 2, dmo.id)

        assert len(monthly_reports) == 1
        monthly = monthly_reports[0]

        assert monthly.summary.completed_days == 6  # Out of 7 tracked days
        assert monthly.summary.total_days == 28  # February has 28 days

        # 6. Get summary for the week
        summary = await sqlite_service.get_dmo_summary(
            dmo.id, date(2026, 2, 1), date(2026, 2, 7)
        )

        assert summary.total_days == 7
        assert summary.completed_days == 6
        assert summary.current_streak == 4  # Days 4-7
