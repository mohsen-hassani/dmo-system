"""
In-memory storage backend for testing.

This implementation stores all data in Python dictionaries.
It's useful for unit tests where database setup overhead is undesirable.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from dmo_core.errors import (
    ActivityNotFoundError,
    DmoNotFoundError,
    DuplicateNameError,
)
from dmo_core.models import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    DMOCompletionRead,
    DMOCreate,
    DMORead,
    DMOUpdate,
)
from dmo_core.storage.base import StorageBackend
from dmo_core.utils import utc_now


class MemoryBackend(StorageBackend):
    """
    In-memory storage backend for testing.

    All data is lost when the instance is garbage collected.
    """

    def __init__(self) -> None:
        self._dmos: dict[int, DMORead] = {}
        self._activities: dict[int, ActivityRead] = {}
        self._completions: dict[tuple[int, date], DMOCompletionRead] = {}
        self._completion_ids: dict[int, tuple[int, date]] = {}  # id -> (dmo_id, date)
        # Auto-increment counters
        self._next_dmo_id = 1
        self._next_activity_id = 1
        self._next_completion_id = 1

    async def init(self) -> None:
        """No-op for memory backend."""
        pass

    async def close(self) -> None:
        """Clear all data."""
        self._dmos.clear()
        self._activities.clear()
        self._completions.clear()
        self._completion_ids.clear()

    # =========================================================================
    # DMO Operations
    # =========================================================================

    async def create_dmo(self, data: DMOCreate) -> DMORead:
        # Check for duplicate name
        for dmo in self._dmos.values():
            if dmo.name == data.name:
                raise DuplicateNameError("DMO", data.name)

        now = utc_now()
        dmo_id = self._next_dmo_id
        self._next_dmo_id += 1

        dmo = DMORead(
            id=dmo_id,
            name=data.name,
            description=data.description,
            active=True,
            timezone=data.timezone,
            created_at=now,
            updated_at=now,
        )
        self._dmos[dmo.id] = dmo
        return dmo

    async def get_dmo(self, dmo_id: int) -> DMORead:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)
        return self._dmos[dmo_id]

    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        dmos = list(self._dmos.values())
        if not include_inactive:
            dmos = [d for d in dmos if d.active]
        return sorted(dmos, key=lambda d: d.name)

    async def update_dmo(self, dmo_id: int, data: DMOUpdate) -> DMORead:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        existing = self._dmos[dmo_id]

        # Check for duplicate name
        if data.name is not None and data.name != existing.name:
            for dmo in self._dmos.values():
                if dmo.name == data.name and dmo.id != dmo_id:
                    raise DuplicateNameError("DMO", data.name)

        updated = DMORead(
            id=existing.id,
            name=data.name if data.name is not None else existing.name,
            description=data.description if data.description is not None else existing.description,
            active=data.active if data.active is not None else existing.active,
            timezone=data.timezone if data.timezone is not None else existing.timezone,
            created_at=existing.created_at,
            updated_at=utc_now(),
        )
        self._dmos[dmo_id] = updated
        return updated

    async def delete_dmo(self, dmo_id: int) -> None:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        # Delete associated activities
        activities_to_delete = [
            aid for aid, a in self._activities.items() if a.dmo_id == dmo_id
        ]
        for aid in activities_to_delete:
            del self._activities[aid]

        # Delete associated completions
        completions_to_delete = [
            key for key in self._completions if key[0] == dmo_id
        ]
        for key in completions_to_delete:
            completion = self._completions[key]
            del self._completion_ids[completion.id]
            del self._completions[key]

        del self._dmos[dmo_id]

    # =========================================================================
    # Activity Operations
    # =========================================================================

    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        if data.dmo_id not in self._dmos:
            raise DmoNotFoundError(data.dmo_id)

        now = utc_now()
        activity_id = self._next_activity_id
        self._next_activity_id += 1

        activity = ActivityRead(
            id=activity_id,
            dmo_id=data.dmo_id,
            name=data.name,
            order=data.order,
            created_at=now,
            updated_at=now,
        )
        self._activities[activity.id] = activity
        return activity

    async def get_activity(self, activity_id: int) -> ActivityRead:
        if activity_id not in self._activities:
            raise ActivityNotFoundError(activity_id)
        return self._activities[activity_id]

    async def list_activities(self, dmo_id: int) -> Sequence[ActivityRead]:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        activities = [a for a in self._activities.values() if a.dmo_id == dmo_id]
        return sorted(activities, key=lambda a: (a.order, a.created_at))

    async def update_activity(
        self, activity_id: int, data: ActivityUpdate
    ) -> ActivityRead:
        if activity_id not in self._activities:
            raise ActivityNotFoundError(activity_id)

        existing = self._activities[activity_id]

        updated = ActivityRead(
            id=existing.id,
            dmo_id=existing.dmo_id,
            name=data.name if data.name is not None else existing.name,
            order=data.order if data.order is not None else existing.order,
            created_at=existing.created_at,
            updated_at=utc_now(),
        )
        self._activities[activity_id] = updated
        return updated

    async def delete_activity(self, activity_id: int) -> None:
        if activity_id not in self._activities:
            raise ActivityNotFoundError(activity_id)
        del self._activities[activity_id]

    # =========================================================================
    # DMOCompletion Operations
    # =========================================================================

    async def set_completion(
        self,
        dmo_id: int,
        completion_date: date,
        completed: bool,
        note: str | None = None,
    ) -> DMOCompletionRead:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        key = (dmo_id, completion_date)
        now = utc_now()

        if key in self._completions:
            existing = self._completions[key]
            updated = DMOCompletionRead(
                id=existing.id,
                dmo_id=dmo_id,
                date=completion_date,
                completed=completed,
                note=note,
                created_at=existing.created_at,
                updated_at=now,
            )
            self._completions[key] = updated
            return updated
        else:
            completion_id = self._next_completion_id
            self._next_completion_id += 1

            completion = DMOCompletionRead(
                id=completion_id,
                dmo_id=dmo_id,
                date=completion_date,
                completed=completed,
                note=note,
                created_at=now,
                updated_at=now,
            )
            self._completions[key] = completion
            self._completion_ids[completion.id] = key
            return completion

    async def get_completion(
        self, dmo_id: int, completion_date: date
    ) -> DMOCompletionRead | None:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        key = (dmo_id, completion_date)
        return self._completions.get(key)

    async def list_completions(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> Sequence[DMOCompletionRead]:
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")

        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        completions = [
            c for (did, d), c in self._completions.items()
            if did == dmo_id and start <= d <= end
        ]
        return sorted(completions, key=lambda c: c.date)

    async def count_completed_days(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> int:
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")

        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)

        return sum(
            1 for (did, d), c in self._completions.items()
            if did == dmo_id and start <= d <= end and c.completed
        )
