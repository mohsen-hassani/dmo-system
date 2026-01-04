"""
DmoService: High-level business logic layer.

This service provides the main API for interacting with the DMO system.
It handles reporting, streak calculations, and orchestrates storage operations.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from dmo_core.models import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    DailyReport,
    DayCompletion,
    DMOCompletionRead,
    DMOCreate,
    DMODailyStatus,
    DMORead,
    DMOSummary,
    DMOUpdate,
    MonthlyReport,
    MonthSummary,
)
from dmo_core.storage.base import StorageBackend
from dmo_core.utils import (
    calculate_completion_rate,
    calculate_streaks,
    date_range,
    days_in_month,
)


class DmoService:
    """
    High-level service for DMO operations.

    This class provides the main API for the DMO system, including:
    - CRUD operations for DMOs and Activities
    - Completion tracking
    - Daily and monthly reports
    - Streak calculations

    Args:
        storage: A StorageBackend implementation

    Example:
        ```python
        from dmo_core import DmoService
        from dmo_core.storage import SqliteBackend

        async def main():
            backend = SqliteBackend("my_dmos.db")
            await backend.init()

            service = DmoService(backend)

            # Create a DMO
            dmo = await service.create_dmo(DMOCreate(name="Morning Routine"))

            # Mark it complete for today
            from datetime import date
            await service.set_dmo_completion(dmo.id, date.today(), True)
        ```
    """

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    # =========================================================================
    # DMO Operations
    # =========================================================================

    async def create_dmo(self, data: DMOCreate) -> DMORead:
        """Create a new DMO."""
        return await self._storage.create_dmo(data)

    async def get_dmo(self, dmo_id: int) -> DMORead:
        """Get a DMO by ID."""
        return await self._storage.get_dmo(dmo_id)

    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        """List all DMOs, optionally including inactive ones."""
        return await self._storage.list_dmos(include_inactive=include_inactive)

    async def update_dmo(self, dmo_id: int, data: DMOUpdate) -> DMORead:
        """Update a DMO."""
        return await self._storage.update_dmo(dmo_id, data)

    async def delete_dmo(self, dmo_id: int) -> None:
        """Delete a DMO and all associated data."""
        await self._storage.delete_dmo(dmo_id)

    async def deactivate_dmo(self, dmo_id: int) -> DMORead:
        """Soft-delete a DMO by setting active=False."""
        return await self._storage.update_dmo(dmo_id, DMOUpdate(active=False))

    async def activate_dmo(self, dmo_id: int) -> DMORead:
        """Re-activate a deactivated DMO."""
        return await self._storage.update_dmo(dmo_id, DMOUpdate(active=True))

    # =========================================================================
    # Activity Operations
    # =========================================================================

    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        """Create a new Activity within a DMO."""
        return await self._storage.create_activity(data)

    async def get_activity(self, activity_id: int) -> ActivityRead:
        """Get an Activity by ID."""
        return await self._storage.get_activity(activity_id)

    async def list_activities(self, dmo_id: int) -> Sequence[ActivityRead]:
        """List all Activities for a DMO, ordered by 'order' field."""
        return await self._storage.list_activities(dmo_id)

    async def update_activity(
        self, activity_id: int, data: ActivityUpdate
    ) -> ActivityRead:
        """Update an Activity."""
        return await self._storage.update_activity(activity_id, data)

    async def delete_activity(self, activity_id: int) -> None:
        """Delete an Activity."""
        await self._storage.delete_activity(activity_id)

    async def reorder_activities(
        self, dmo_id: int, activity_ids: Sequence[int]
    ) -> Sequence[ActivityRead]:
        """
        Reorder activities within a DMO.

        Sets the 'order' field based on the position in activity_ids.

        Args:
            dmo_id: The DMO's ID
            activity_ids: Activity IDs in the desired order

        Returns:
            Updated activities in their new order
        """
        for i, activity_id in enumerate(activity_ids):
            await self._storage.update_activity(
                activity_id, ActivityUpdate(order=i)
            )
        return await self._storage.list_activities(dmo_id)

    # =========================================================================
    # Completion Operations
    # =========================================================================

    async def set_dmo_completion(
        self,
        dmo_id: int,
        completion_date: date,
        completed: bool,
        note: str | None = None,
    ) -> DMOCompletionRead:
        """
        Set the completion status for a DMO on a specific date.

        This is idempotent - calling multiple times with the same parameters
        will produce the same result.

        Args:
            dmo_id: The DMO's ID
            completion_date: The date (user's local date)
            completed: Whether the DMO was completed
            note: Optional note about the completion

        Returns:
            The completion record
        """
        return await self._storage.set_completion(
            dmo_id, completion_date, completed, note
        )

    async def get_completion(
        self, dmo_id: int, completion_date: date
    ) -> DMOCompletionRead | None:
        """Get the completion record for a DMO on a specific date."""
        return await self._storage.get_completion(dmo_id, completion_date)

    async def mark_complete(
        self, dmo_id: int, completion_date: date, note: str | None = None
    ) -> DMOCompletionRead:
        """Convenience method to mark a DMO as complete."""
        return await self.set_dmo_completion(dmo_id, completion_date, True, note)

    async def mark_incomplete(
        self, dmo_id: int, completion_date: date, note: str | None = None
    ) -> DMOCompletionRead:
        """Convenience method to mark a DMO as incomplete."""
        return await self.set_dmo_completion(dmo_id, completion_date, False, note)

    # =========================================================================
    # Reports
    # =========================================================================

    async def get_daily_report(self, report_date: date) -> DailyReport:
        """
        Get a daily report showing all active DMOs and their completion status.

        For each active DMO, the report includes:
        - The DMO details
        - Whether it was completed on this date
        - The list of activity names (as a reference checklist)

        Args:
            report_date: The date to generate the report for

        Returns:
            DailyReport with all active DMOs and their status
        """
        dmos = await self._storage.list_dmos(include_inactive=False)
        dmo_statuses: list[DMODailyStatus] = []

        for dmo in dmos:
            completion = await self._storage.get_completion(dmo.id, report_date)
            activities = await self._storage.list_activities(dmo.id)

            status = DMODailyStatus(
                dmo=dmo,
                completed=completion.completed if completion else False,
                note=completion.note if completion else None,
                activities=[a.name for a in activities],
            )
            dmo_statuses.append(status)

        return DailyReport(date=report_date, dmos=dmo_statuses)

    async def get_monthly_report(
        self,
        year: int,
        month: int,
        dmo_id: int | None = None,
    ) -> list[MonthlyReport]:
        """
        Get monthly reports for DMOs.

        Args:
            year: The year (e.g., 2026)
            month: The month (1-12)
            dmo_id: Optional specific DMO ID. If None, generates reports for all active DMOs.

        Returns:
            List of MonthlyReport objects
        """
        if dmo_id:
            dmos = [await self._storage.get_dmo(dmo_id)]
        else:
            dmos = list(await self._storage.list_dmos(include_inactive=False))

        num_days = days_in_month(year, month)
        start = date(year, month, 1)
        end = date(year, month, num_days)
        all_dates = date_range(start, end)

        reports: list[MonthlyReport] = []

        for dmo in dmos:
            completions = await self._storage.list_completions(dmo.id, start, end)

            # Build a lookup of date -> completion
            completion_map: dict[date, DMOCompletionRead] = {
                c.date: c for c in completions
            }

            # Build day-by-day status
            days: list[DayCompletion] = []
            completed_dates: set[date] = set()
            missed_days: list[date] = []

            for d in all_dates:
                completion = completion_map.get(d)
                is_completed = completion.completed if completion else False

                days.append(DayCompletion(
                    date=d,
                    completed=is_completed,
                    note=completion.note if completion else None,
                ))

                if is_completed:
                    completed_dates.add(d)
                else:
                    missed_days.append(d)

            # Calculate streaks
            current_streak, longest_streak = calculate_streaks(
                completed_dates, all_dates
            )

            # Build summary
            summary = MonthSummary(
                total_days=num_days,
                completed_days=len(completed_dates),
                completion_rate=calculate_completion_rate(
                    len(completed_dates), num_days
                ),
                current_streak=current_streak,
                longest_streak=longest_streak,
                missed_days=missed_days,
            )

            reports.append(MonthlyReport(
                dmo=dmo,
                year=year,
                month=month,
                days=days,
                summary=summary,
            ))

        return reports

    async def get_dmo_summary(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> DMOSummary:
        """
        Get a summary of DMO performance over a date range.

        Args:
            dmo_id: The DMO's ID
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            DMOSummary with statistics for the date range
        """
        dmo = await self._storage.get_dmo(dmo_id)
        completions = await self._storage.list_completions(dmo_id, start, end)

        all_dates = date_range(start, end)
        completed_dates = {c.date for c in completions if c.completed}

        current_streak, longest_streak = calculate_streaks(completed_dates, all_dates)

        return DMOSummary(
            dmo=dmo,
            start_date=start,
            end_date=end,
            total_days=len(all_dates),
            completed_days=len(completed_dates),
            completion_rate=calculate_completion_rate(
                len(completed_dates), len(all_dates)
            ),
            current_streak=current_streak,
            longest_streak=longest_streak,
        )
