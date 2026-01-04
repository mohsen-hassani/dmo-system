"""
SQLite storage backend implementation using aiosqlite.

This is the reference implementation of StorageBackend.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import date, datetime

import aiosqlite

from dmo_core.errors import (
    ActivityNotFoundError,
    DmoNotFoundError,
    DuplicateNameError,
    StorageError,
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

# SQL Schema
_SCHEMA = """
CREATE TABLE IF NOT EXISTS dmos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    timezone TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dmo_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (dmo_id) REFERENCES dmos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activities_dmo_id ON activities(dmo_id);
CREATE INDEX IF NOT EXISTS idx_activities_order ON activities(dmo_id, "order");

CREATE TABLE IF NOT EXISTS dmo_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dmo_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    completed INTEGER NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (dmo_id) REFERENCES dmos(id) ON DELETE CASCADE,
    UNIQUE(dmo_id, date)
);

CREATE INDEX IF NOT EXISTS idx_completions_dmo_date ON dmo_completions(dmo_id, date);
"""


class SqliteBackend(StorageBackend):
    """
    SQLite implementation of the storage backend.

    Args:
        db_path: Path to SQLite database file. Use ":memory:" for in-memory DB.
    """

    def __init__(self, db_path: str = "dmo.db") -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def _get_conn(self) -> aiosqlite.Connection:
        """Get the database connection, raising if not initialized."""
        if self._conn is None:
            raise StorageError("init", "Database not initialized. Call init() first.")
        return self._conn

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def init(self) -> None:
        """Initialize database and create schema."""
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row

        # Enable foreign keys
        await self._conn.execute("PRAGMA foreign_keys = ON")

        # Create schema
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _row_to_dmo(self, row: aiosqlite.Row) -> DMORead:
        """Convert a database row to DMORead model."""
        return DMORead(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            active=bool(row["active"]),
            timezone=row["timezone"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity(self, row: aiosqlite.Row) -> ActivityRead:
        """Convert a database row to ActivityRead model."""
        return ActivityRead(
            id=row["id"],
            dmo_id=row["dmo_id"],
            name=row["name"],
            order=row["order"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_completion(self, row: aiosqlite.Row) -> DMOCompletionRead:
        """Convert a database row to DMOCompletionRead model."""
        return DMOCompletionRead(
            id=row["id"],
            dmo_id=row["dmo_id"],
            date=date.fromisoformat(row["date"]),
            completed=bool(row["completed"]),
            note=row["note"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def _dmo_exists(self, dmo_id: int) -> bool:
        """Check if a DMO exists."""
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT 1 FROM dmos WHERE id = ?", (dmo_id,)
        )
        row = await cursor.fetchone()
        return row is not None

    async def _ensure_dmo_exists(self, dmo_id: int) -> None:
        """Raise DmoNotFoundError if DMO does not exist."""
        if not await self._dmo_exists(dmo_id):
            raise DmoNotFoundError(dmo_id)

    # =========================================================================
    # DMO Operations
    # =========================================================================

    async def create_dmo(self, data: DMOCreate) -> DMORead:
        conn = await self._get_conn()

        now = utc_now().isoformat()

        try:
            cursor = await conn.execute(
                """
                INSERT INTO dmos (name, description, active, timezone, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?, ?)
                """,
                (data.name, data.description, data.timezone, now, now),
            )
            await conn.commit()
            dmo_id = cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: dmos.name" in str(e):
                raise DuplicateNameError("DMO", data.name) from e
            raise StorageError("create_dmo", str(e)) from e

        if dmo_id is None:
            raise StorageError("create_dmo", "Failed to get inserted row ID")

        return await self.get_dmo(dmo_id)

    async def get_dmo(self, dmo_id: int) -> DMORead:
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT * FROM dmos WHERE id = ?", (dmo_id,)
        )
        row = await cursor.fetchone()

        if row is None:
            raise DmoNotFoundError(dmo_id)

        return self._row_to_dmo(row)

    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        conn = await self._get_conn()

        if include_inactive:
            cursor = await conn.execute("SELECT * FROM dmos ORDER BY name ASC")
        else:
            cursor = await conn.execute(
                "SELECT * FROM dmos WHERE active = 1 ORDER BY name ASC"
            )

        rows = await cursor.fetchall()
        return [self._row_to_dmo(row) for row in rows]

    async def update_dmo(self, dmo_id: int, data: DMOUpdate) -> DMORead:
        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()

        # Build dynamic update
        updates: list[str] = []
        values: list[object] = []

        if data.name is not None:
            updates.append("name = ?")
            values.append(data.name)
        if data.description is not None:
            updates.append("description = ?")
            values.append(data.description)
        if data.timezone is not None:
            updates.append("timezone = ?")
            values.append(data.timezone)
        if data.active is not None:
            updates.append("active = ?")
            values.append(1 if data.active else 0)

        if not updates:
            return await self.get_dmo(dmo_id)

        updates.append("updated_at = ?")
        values.append(utc_now().isoformat())
        values.append(dmo_id)

        try:
            await conn.execute(
                f"UPDATE dmos SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            await conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: dmos.name" in str(e):
                raise DuplicateNameError("DMO", data.name or "") from e
            raise StorageError("update_dmo", str(e)) from e

        return await self.get_dmo(dmo_id)

    async def delete_dmo(self, dmo_id: int) -> None:
        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()
        await conn.execute("DELETE FROM dmos WHERE id = ?", (dmo_id,))
        await conn.commit()

    # =========================================================================
    # Activity Operations
    # =========================================================================

    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        await self._ensure_dmo_exists(data.dmo_id)

        conn = await self._get_conn()

        now = utc_now().isoformat()

        cursor = await conn.execute(
            """
            INSERT INTO activities (dmo_id, name, "order", created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data.dmo_id, data.name, data.order, now, now),
        )
        await conn.commit()
        activity_id = cursor.lastrowid

        if activity_id is None:
            raise StorageError("create_activity", "Failed to get inserted row ID")

        return await self.get_activity(activity_id)

    async def get_activity(self, activity_id: int) -> ActivityRead:
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        )
        row = await cursor.fetchone()

        if row is None:
            raise ActivityNotFoundError(activity_id)

        return self._row_to_activity(row)

    async def list_activities(self, dmo_id: int) -> Sequence[ActivityRead]:
        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()
        cursor = await conn.execute(
            'SELECT * FROM activities WHERE dmo_id = ? ORDER BY "order" ASC, created_at ASC',
            (dmo_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_activity(row) for row in rows]

    async def update_activity(
        self, activity_id: int, data: ActivityUpdate
    ) -> ActivityRead:
        # Verify activity exists
        await self.get_activity(activity_id)

        conn = await self._get_conn()

        updates: list[str] = []
        values: list[object] = []

        if data.name is not None:
            updates.append("name = ?")
            values.append(data.name)
        if data.order is not None:
            updates.append('"order" = ?')
            values.append(data.order)

        if not updates:
            return await self.get_activity(activity_id)

        updates.append("updated_at = ?")
        values.append(utc_now().isoformat())
        values.append(activity_id)

        await conn.execute(
            f"UPDATE activities SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        await conn.commit()

        return await self.get_activity(activity_id)

    async def delete_activity(self, activity_id: int) -> None:
        # Verify activity exists
        await self.get_activity(activity_id)

        conn = await self._get_conn()
        await conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        await conn.commit()

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
        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()
        now = utc_now().isoformat()
        date_str = completion_date.isoformat()

        # Check if record exists
        cursor = await conn.execute(
            "SELECT id FROM dmo_completions WHERE dmo_id = ? AND date = ?",
            (dmo_id, date_str),
        )
        existing = await cursor.fetchone()

        if existing:
            # Update existing
            await conn.execute(
                """
                UPDATE dmo_completions
                SET completed = ?, note = ?, updated_at = ?
                WHERE dmo_id = ? AND date = ?
                """,
                (1 if completed else 0, note, now, dmo_id, date_str),
            )
        else:
            # Insert new
            await conn.execute(
                """
                INSERT INTO dmo_completions
                (dmo_id, date, completed, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (dmo_id, date_str, 1 if completed else 0, note, now, now),
            )

        await conn.commit()

        # Fetch and return the record
        result = await self.get_completion(dmo_id, completion_date)
        assert result is not None  # We just created/updated it
        return result

    async def get_completion(
        self, dmo_id: int, completion_date: date
    ) -> DMOCompletionRead | None:
        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT * FROM dmo_completions WHERE dmo_id = ? AND date = ?",
            (dmo_id, completion_date.isoformat()),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return self._row_to_completion(row)

    async def list_completions(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> Sequence[DMOCompletionRead]:
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")

        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()
        cursor = await conn.execute(
            """
            SELECT * FROM dmo_completions
            WHERE dmo_id = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
            """,
            (dmo_id, start.isoformat(), end.isoformat()),
        )
        rows = await cursor.fetchall()
        return [self._row_to_completion(row) for row in rows]

    async def count_completed_days(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> int:
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")

        await self._ensure_dmo_exists(dmo_id)

        conn = await self._get_conn()
        cursor = await conn.execute(
            """
            SELECT COUNT(*) as count FROM dmo_completions
            WHERE dmo_id = ? AND date >= ? AND date <= ? AND completed = 1
            """,
            (dmo_id, start.isoformat(), end.isoformat()),
        )
        row = await cursor.fetchone()
        return int(row["count"]) if row else 0
