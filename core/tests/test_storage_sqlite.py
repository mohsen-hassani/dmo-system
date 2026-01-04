"""
Tests for SQLite storage backend.
"""

from datetime import date

import pytest

from dmo_core import ActivityCreate, DMOCreate, DMOUpdate
from dmo_core.errors import (
    ActivityNotFoundError,
    DmoNotFoundError,
    DuplicateNameError,
)
from dmo_core.storage import SqliteBackend


class TestSqliteBackendDMO:
    """Tests for DMO operations in SQLite backend."""

    async def test_create_dmo(self, sqlite_backend: SqliteBackend) -> None:
        """Test creating a DMO."""
        dmo = await sqlite_backend.create_dmo(
            DMOCreate(name="Test DMO", description="Test description")
        )

        assert dmo.id is not None
        assert dmo.name == "Test DMO"
        assert dmo.description == "Test description"
        assert dmo.active is True
        assert dmo.created_at is not None
        assert dmo.updated_at is not None

    async def test_create_dmo_duplicate_name(self, sqlite_backend: SqliteBackend) -> None:
        """Test that duplicate names are rejected."""
        await sqlite_backend.create_dmo(DMOCreate(name="Unique Name"))

        with pytest.raises(DuplicateNameError) as exc_info:
            await sqlite_backend.create_dmo(DMOCreate(name="Unique Name"))

        assert exc_info.value.name == "Unique Name"

    async def test_get_dmo(self, sqlite_backend: SqliteBackend) -> None:
        """Test retrieving a DMO by ID."""
        created = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        retrieved = await sqlite_backend.get_dmo(created.id)

        assert retrieved.id == created.id
        assert retrieved.name == created.name

    async def test_get_dmo_not_found(self, sqlite_backend: SqliteBackend) -> None:
        """Test that getting non-existent DMO raises error."""
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.get_dmo(999999)

    async def test_list_dmos(self, sqlite_backend: SqliteBackend) -> None:
        """Test listing DMOs."""
        await sqlite_backend.create_dmo(DMOCreate(name="Alpha"))
        await sqlite_backend.create_dmo(DMOCreate(name="Beta"))

        dmos = await sqlite_backend.list_dmos()

        assert len(dmos) == 2
        assert dmos[0].name == "Alpha"  # Ordered by name
        assert dmos[1].name == "Beta"

    async def test_list_dmos_excludes_inactive(self, sqlite_backend: SqliteBackend) -> None:
        """Test that inactive DMOs are excluded by default."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        await sqlite_backend.update_dmo(dmo.id, DMOUpdate(active=False))

        dmos = await sqlite_backend.list_dmos()
        assert len(dmos) == 0

        dmos = await sqlite_backend.list_dmos(include_inactive=True)
        assert len(dmos) == 1

    async def test_update_dmo(self, sqlite_backend: SqliteBackend) -> None:
        """Test updating a DMO."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Original"))

        updated = await sqlite_backend.update_dmo(
            dmo.id, DMOUpdate(name="Updated", active=False)
        )

        assert updated.name == "Updated"
        assert updated.active is False
        assert updated.updated_at > dmo.updated_at

    async def test_delete_dmo(self, sqlite_backend: SqliteBackend) -> None:
        """Test deleting a DMO."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="To Delete"))
        await sqlite_backend.delete_dmo(dmo.id)

        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.get_dmo(dmo.id)

    async def test_delete_dmo_cascades_activities(self, sqlite_backend: SqliteBackend) -> None:
        """Test that deleting a DMO also deletes its activities."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        activity = await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Activity")
        )

        await sqlite_backend.delete_dmo(dmo.id)

        with pytest.raises(ActivityNotFoundError):
            await sqlite_backend.get_activity(activity.id)

    async def test_delete_dmo_cascades_completions(self, sqlite_backend: SqliteBackend) -> None:
        """Test that deleting a DMO also deletes its completions."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 1), True)

        await sqlite_backend.delete_dmo(dmo.id)

        # DMO is gone, so we can't even query completions
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.get_completion(dmo.id, date(2026, 1, 1))


class TestSqliteBackendActivity:
    """Tests for Activity operations in SQLite backend."""

    async def test_create_activity(self, sqlite_backend: SqliteBackend) -> None:
        """Test creating an activity."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        activity = await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Activity 1", order=0)
        )

        assert activity.id is not None
        assert activity.dmo_id == dmo.id
        assert activity.name == "Activity 1"
        assert activity.order == 0

    async def test_create_activity_invalid_dmo(self, sqlite_backend: SqliteBackend) -> None:
        """Test that creating activity with invalid DMO raises error."""
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.create_activity(
                ActivityCreate(dmo_id=999999, name="Activity")
            )

    async def test_list_activities_ordered(self, sqlite_backend: SqliteBackend) -> None:
        """Test that activities are ordered by 'order' field."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Third", order=2)
        )
        await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="First", order=0)
        )
        await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Second", order=1)
        )

        activities = await sqlite_backend.list_activities(dmo.id)

        assert len(activities) == 3
        assert activities[0].name == "First"
        assert activities[1].name == "Second"
        assert activities[2].name == "Third"


class TestSqliteBackendCompletion:
    """Tests for completion operations in SQLite backend."""

    async def test_set_completion_create(self, sqlite_backend: SqliteBackend) -> None:
        """Test creating a new completion record."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        completion = await sqlite_backend.set_completion(
            dmo.id, date(2026, 1, 15), True, "Great day!"
        )

        assert completion.dmo_id == dmo.id
        assert completion.date == date(2026, 1, 15)
        assert completion.completed is True
        assert completion.note == "Great day!"

    async def test_set_completion_update(self, sqlite_backend: SqliteBackend) -> None:
        """Test updating an existing completion record."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        # Create
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 15), True)

        # Update
        updated = await sqlite_backend.set_completion(
            dmo.id, date(2026, 1, 15), False, "Changed my mind"
        )

        assert updated.completed is False
        assert updated.note == "Changed my mind"

    async def test_set_completion_idempotent(self, sqlite_backend: SqliteBackend) -> None:
        """Test that set_completion is idempotent."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        c1 = await sqlite_backend.set_completion(dmo.id, date(2026, 1, 15), True)
        c2 = await sqlite_backend.set_completion(dmo.id, date(2026, 1, 15), True)

        assert c1.id == c2.id  # Same record

    async def test_get_completion_not_found(self, sqlite_backend: SqliteBackend) -> None:
        """Test getting non-existent completion returns None."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        result = await sqlite_backend.get_completion(dmo.id, date(2026, 1, 15))

        assert result is None

    async def test_list_completions(self, sqlite_backend: SqliteBackend) -> None:
        """Test listing completions in a date range."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 1), True)
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 5), False)
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 10), True)
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 20), True)  # Outside range

        completions = await sqlite_backend.list_completions(
            dmo.id, date(2026, 1, 1), date(2026, 1, 15)
        )

        assert len(completions) == 3
        assert completions[0].date == date(2026, 1, 1)
        assert completions[1].date == date(2026, 1, 5)
        assert completions[2].date == date(2026, 1, 10)

    async def test_count_completed_days(self, sqlite_backend: SqliteBackend) -> None:
        """Test counting completed days."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))

        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 1), True)
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 2), False)
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 3), True)
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 4), True)

        count = await sqlite_backend.count_completed_days(
            dmo.id, date(2026, 1, 1), date(2026, 1, 31)
        )

        assert count == 3
