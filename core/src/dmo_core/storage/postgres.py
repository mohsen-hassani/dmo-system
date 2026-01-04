"""
PostgreSQL storage backend implementation using asyncpg.

This implementation provides a production-ready storage backend using PostgreSQL
with connection pooling for optimal performance.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

import asyncpg

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
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    timezone TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    dmo_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (dmo_id) REFERENCES dmos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activities_dmo_id ON activities(dmo_id);
CREATE INDEX IF NOT EXISTS idx_activities_order ON activities(dmo_id, "order");

CREATE TABLE IF NOT EXISTS dmo_completions (
    id SERIAL PRIMARY KEY,
    dmo_id INTEGER NOT NULL,
    date DATE NOT NULL,
    completed BOOLEAN NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (dmo_id) REFERENCES dmos(id) ON DELETE CASCADE,
    UNIQUE(dmo_id, date)
);

CREATE INDEX IF NOT EXISTS idx_completions_dmo_date ON dmo_completions(dmo_id, date);
"""


class PostgresBackend(StorageBackend):
    """
    PostgreSQL implementation of the storage backend using asyncpg.

    Features:
    - Connection pooling for high performance
    - Native async/await support
    - Automatic reconnection on connection loss
    - Prepared statement caching

    Args:
        dsn: Full PostgreSQL connection string (overrides other params if provided)
        host: Database host (default: localhost)
        port: Database port (default: 5432)
        user: Database user (default: postgres)
        password: Database password (default: postgres)
        database: Database name (default: dmo)
        min_pool_size: Minimum connections in pool (default: 5)
        max_pool_size: Maximum connections in pool (default: 20)
    """

    def __init__(
        self,
        dsn: str | None = None,
        *,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "postgres",
        database: str = "dmo",
        min_pool_size: int = 5,
        max_pool_size: int = 20,
    ) -> None:
        if dsn:
            self._dsn = dsn
        else:
            self._dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Get the database connection pool, raising if not initialized."""
        if self._pool is None:
            raise StorageError("init", "Connection pool not initialized. Call init() first.")
        return self._pool

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def init(self) -> None:
        """Initialize database connection pool and create schema."""
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_pool_size,
            max_size=self._max_pool_size,
        )

        # Create schema
        async with self._pool.acquire() as conn:
            await conn.execute(_SCHEMA)

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _row_to_dmo(self, row: asyncpg.Record) -> DMORead:
        """Convert a database row to DMORead model."""
        return DMORead(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            active=row["active"],
            timezone=row["timezone"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_activity(self, row: asyncpg.Record) -> ActivityRead:
        """Convert a database row to ActivityRead model."""
        return ActivityRead(
            id=row["id"],
            dmo_id=row["dmo_id"],
            name=row["name"],
            order=row["order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_completion(self, row: asyncpg.Record) -> DMOCompletionRead:
        """Convert a database row to DMOCompletionRead model."""
        return DMOCompletionRead(
            id=row["id"],
            dmo_id=row["dmo_id"],
            date=row["date"],
            completed=row["completed"],
            note=row["note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def _dmo_exists(self, dmo_id: int) -> bool:
        """Check if a DMO exists."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM dmos WHERE id = $1", dmo_id
            )
            return row is not None

    async def _ensure_dmo_exists(self, dmo_id: int) -> None:
        """Raise DmoNotFoundError if DMO does not exist."""
        if not await self._dmo_exists(dmo_id):
            raise DmoNotFoundError(dmo_id)

    # =========================================================================
    # DMO Operations
    # =========================================================================

    async def create_dmo(self, data: DMOCreate) -> DMORead:
        pool = await self._get_pool()
        now = utc_now()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO dmos (name, description, active, timezone, created_at, updated_at)
                    VALUES ($1, $2, TRUE, $3, $4, $5)
                    RETURNING *
                    """,
                    data.name, data.description, data.timezone, now, now,
                )
                return self._row_to_dmo(row)
        except asyncpg.UniqueViolationError as e:
            raise DuplicateNameError("DMO", data.name) from e
        except asyncpg.PostgresError as e:
            raise StorageError("create_dmo", str(e)) from e

    async def get_dmo(self, dmo_id: int) -> DMORead:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM dmos WHERE id = $1", dmo_id
            )

            if row is None:
                raise DmoNotFoundError(dmo_id)

            return self._row_to_dmo(row)

    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            if include_inactive:
                rows = await conn.fetch("SELECT * FROM dmos ORDER BY name ASC")
            else:
                rows = await conn.fetch(
                    "SELECT * FROM dmos WHERE active = TRUE ORDER BY name ASC"
                )

        return [self._row_to_dmo(row) for row in rows]

    async def update_dmo(self, dmo_id: int, data: DMOUpdate) -> DMORead:
        await self._ensure_dmo_exists(dmo_id)

        pool = await self._get_pool()

        # Build dynamic update
        updates: list[str] = []
        values: list[object] = []
        param_num = 1

        if data.name is not None:
            updates.append(f"name = ${param_num}")
            values.append(data.name)
            param_num += 1
        if data.description is not None:
            updates.append(f"description = ${param_num}")
            values.append(data.description)
            param_num += 1
        if data.timezone is not None:
            updates.append(f"timezone = ${param_num}")
            values.append(data.timezone)
            param_num += 1
        if data.active is not None:
            updates.append(f"active = ${param_num}")
            values.append(data.active)
            param_num += 1

        if not updates:
            return await self.get_dmo(dmo_id)

        updates.append(f"updated_at = ${param_num}")
        values.append(utc_now())
        param_num += 1
        values.append(dmo_id)

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE dmos SET {', '.join(updates)} WHERE id = ${param_num}",
                    *values,
                )
        except asyncpg.UniqueViolationError as e:
            raise DuplicateNameError("DMO", data.name or "") from e
        except asyncpg.PostgresError as e:
            raise StorageError("update_dmo", str(e)) from e

        return await self.get_dmo(dmo_id)

    async def delete_dmo(self, dmo_id: int) -> None:
        await self._ensure_dmo_exists(dmo_id)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM dmos WHERE id = $1", dmo_id)

    # =========================================================================
    # Activity Operations
    # =========================================================================

    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        await self._ensure_dmo_exists(data.dmo_id)

        pool = await self._get_pool()
        now = utc_now()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO activities (dmo_id, name, "order", created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                    """,
                    data.dmo_id, data.name, data.order, now, now,
                )
                return self._row_to_activity(row)
        except asyncpg.PostgresError as e:
            raise StorageError("create_activity", str(e)) from e

    async def get_activity(self, activity_id: int) -> ActivityRead:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM activities WHERE id = $1", activity_id
            )

            if row is None:
                raise ActivityNotFoundError(activity_id)

            return self._row_to_activity(row)

    async def list_activities(self, dmo_id: int) -> Sequence[ActivityRead]:
        await self._ensure_dmo_exists(dmo_id)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM activities WHERE dmo_id = $1 ORDER BY "order" ASC, created_at ASC',
                dmo_id,
            )
        return [self._row_to_activity(row) for row in rows]

    async def update_activity(
        self, activity_id: int, data: ActivityUpdate
    ) -> ActivityRead:
        # Verify activity exists
        await self.get_activity(activity_id)

        pool = await self._get_pool()

        updates: list[str] = []
        values: list[object] = []
        param_num = 1

        if data.name is not None:
            updates.append(f"name = ${param_num}")
            values.append(data.name)
            param_num += 1
        if data.order is not None:
            updates.append(f'"order" = ${param_num}')
            values.append(data.order)
            param_num += 1

        if not updates:
            return await self.get_activity(activity_id)

        updates.append(f"updated_at = ${param_num}")
        values.append(utc_now())
        param_num += 1
        values.append(activity_id)

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE activities SET {', '.join(updates)} WHERE id = ${param_num}",
                    *values,
                )
        except asyncpg.PostgresError as e:
            raise StorageError("update_activity", str(e)) from e

        return await self.get_activity(activity_id)

    async def delete_activity(self, activity_id: int) -> None:
        # Verify activity exists
        await self.get_activity(activity_id)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM activities WHERE id = $1", activity_id)

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

        pool = await self._get_pool()
        now = utc_now()

        try:
            async with pool.acquire() as conn:
                # Use PostgreSQL's UPSERT with ON CONFLICT
                row = await conn.fetchrow(
                    """
                    INSERT INTO dmo_completions (dmo_id, date, completed, note, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (dmo_id, date)
                    DO UPDATE SET
                        completed = EXCLUDED.completed,
                        note = EXCLUDED.note,
                        updated_at = EXCLUDED.updated_at
                    RETURNING *
                    """,
                    dmo_id, completion_date, completed, note, now, now,
                )
                return self._row_to_completion(row)
        except asyncpg.PostgresError as e:
            raise StorageError("set_completion", str(e)) from e

    async def get_completion(
        self, dmo_id: int, completion_date: date
    ) -> DMOCompletionRead | None:
        await self._ensure_dmo_exists(dmo_id)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM dmo_completions WHERE dmo_id = $1 AND date = $2",
                dmo_id, completion_date,
            )

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

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM dmo_completions
                WHERE dmo_id = $1 AND date >= $2 AND date <= $3
                ORDER BY date ASC
                """,
                dmo_id, start, end,
            )
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

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(*) as count FROM dmo_completions
                WHERE dmo_id = $1 AND date >= $2 AND date <= $3 AND completed = TRUE
                """,
                dmo_id, start, end,
            )
            return int(row["count"]) if row else 0
