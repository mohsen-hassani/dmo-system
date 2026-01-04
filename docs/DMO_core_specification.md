ct Structure

Create the following directory structure exactly:

```
dmo-core/
├── pyproject.toml
├── README.md
├── src/
│   └── dmo_core/
│       ├── __init__.py
│       ├── models.py          # Pydantic DTOs
│       ├── errors.py          # Custom exceptions
│       ├── utils.py           # Helper functions
│       ├── service.py         # DmoService class
│       └── storage/
│           ├── __init__.py
│           ├── base.py        # Abstract StorageBackend
│           ├── sqlite.py      # SQLite implementation
│           └── memory.py      # In-memory implementation (for testing)
└── tests/
    ├── __init__.py
    ├── conftest.py            # Shared fixtures
    ├── test_models.py
    ├── test_storage_sqlite.py
    ├── test_storage_memory.py
    ├── t# DMO-Core: Complete Implementation Specification

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Project Name** | `dmo-core` |
| **Language** | Python 3.11+ |
| **Package Manager** | `uv` (preferred) or `pip` |
| **Testing Framework** | `pytest` with `pytest-asyncio` |
| **Type Checking** | Full `mypy` strict mode compliance |
| **Code Style** | `ruff` for linting and formatting |

### Core Philosophy

> **This is a discipline-tracking system, not a task-tracking system.**
>
> The unit of truth is **"Did I complete my DMO today?"** — a single boolean judgment per DMO per day. Activities exist only as a descriptive checklist to help the user remember what "done" means. There is no per-activity execution tracking.

---

## 1. Projeest_service.py
    └── test_integration.py
```

---

## 2. Dependencies (`pyproject.toml`)

```toml
[project]
name = "dmo-core"
version = "0.1.0"
description = "Core service layer for Daily Methods of Operation tracking"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0,<3.0",
    "aiosqlite>=0.19.0,<1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "mypy>=1.8",
    "ruff>=0.3",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/dmo_core"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
asyncio_default_fixture_loop_scope = "function"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
```

---

## 3. Domain Models (`src/dmo_core/models.py`)

All models use Pydantic v2 with strict validation. Implement exactly as shown:

```python
"""
Domain models (DTOs) for the DMO-Core system.

This module defines three layers:
1. Create models (*Create) - for input validation when creating entities
2. Update models (*Update) - for partial updates with optional fields
3. Read models (*Read) - for output/response data with all fields populated
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# DMO Models
# =============================================================================


class DMOCreate(BaseModel):
    """Input model for creating a new DMO."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    timezone: Optional[str] = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip()


class DMOUpdate(BaseModel):
    """Input model for updating an existing DMO. All fields optional."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    timezone: Optional[str] = Field(default=None, max_length=50)
    active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip() if v else v


class DMORead(BaseModel):
    """Output model representing a complete DMO entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    active: bool
    timezone: Optional[str]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Activity Models
# =============================================================================


class ActivityCreate(BaseModel):
    """Input model for creating a new Activity within a DMO."""

    model_config = ConfigDict(str_strip_whitespace=True)

    dmo_id: UUID
    name: str = Field(..., min_length=1, max_length=500)
    order: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip()


class ActivityUpdate(BaseModel):
    """Input model for updating an existing Activity. All fields optional."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=500)
    order: Optional[int] = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip() if v else v


class ActivityRead(BaseModel):
    """Output model representing a complete Activity entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dmo_id: UUID
    name: str
    order: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# DMOCompletion Models
# =============================================================================


class DMOCompletionCreate(BaseModel):
    """Input model for setting/updating DMO completion status."""

    dmo_id: UUID
    date: date
    completed: bool
    note: Optional[str] = Field(default=None, max_length=2000)


class DMOCompletionRead(BaseModel):
    """Output model representing a DMO completion record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dmo_id: UUID
    date: date
    completed: bool
    note: Optional[str]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Report Models
# =============================================================================


class DMODailyStatus(BaseModel):
    """A single DMO's status for a specific day in a daily report."""

    dmo: DMORead
    completed: bool
    note: Optional[str]
    activities: list[str]  # Activity names only, ordered


class DailyReport(BaseModel):
    """Complete report for a single day across all active DMOs."""

    date: date
    dmos: list[DMODailyStatus]


class DayCompletion(BaseModel):
    """Completion status for a single day in a monthly report."""

    date: date
    completed: bool
    note: Optional[str] = None


class MonthSummary(BaseModel):
    """Aggregated statistics for a month."""

    total_days: int
    completed_days: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    current_streak: int = Field(..., ge=0)
    longest_streak: int = Field(..., ge=0)
    missed_days: list[date]


class MonthlyReport(BaseModel):
    """Complete monthly report for a single DMO."""

    dmo: DMORead
    year: int
    month: int = Field(..., ge=1, le=12)
    days: list[DayCompletion]
    summary: MonthSummary


class DMOSummary(BaseModel):
    """Summary statistics for a DMO over a date range."""

    dmo: DMORead
    start_date: date
    end_date: date
    total_days: int
    completed_days: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    current_streak: int = Field(..., ge=0)
    longest_streak: int = Field(..., ge=0)
```

---

## 4. Custom Exceptions (`src/dmo_core/errors.py`)

```python
"""
Custom exceptions for the DMO-Core system.

Exception hierarchy:
    DmoError (base)
    ├── NotFoundError
    │   ├── DmoNotFoundError
    │   ├── ActivityNotFoundError
    │   └── CompletionNotFoundError
    ├── ValidationError
    │   └── DuplicateNameError
    └── StorageError
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID


class DmoError(Exception):
    """Base exception for all DMO-Core errors."""

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(DmoError):
    """Base class for "entity not found" errors."""

    pass


class DmoNotFoundError(NotFoundError):
    """Raised when a DMO with the specified ID does not exist."""

    def __init__(self, dmo_id: UUID) -> None:
        super().__init__(
            message=f"DMO not found: {dmo_id}",
            detail=f"No DMO exists with ID '{dmo_id}'"
        )
        self.dmo_id = dmo_id


class ActivityNotFoundError(NotFoundError):
    """Raised when an Activity with the specified ID does not exist."""

    def __init__(self, activity_id: UUID) -> None:
        super().__init__(
            message=f"Activity not found: {activity_id}",
            detail=f"No Activity exists with ID '{activity_id}'"
        )
        self.activity_id = activity_id


class CompletionNotFoundError(NotFoundError):
    """Raised when a DMOCompletion record is not found."""

    def __init__(self, dmo_id: UUID, date: str) -> None:
        super().__init__(
            message=f"Completion not found for DMO {dmo_id} on {date}",
            detail=f"No completion record exists for DMO '{dmo_id}' on date '{date}'"
        )
        self.dmo_id = dmo_id
        self.date = date


class ValidationError(DmoError):
    """Base class for validation-related errors."""

    pass


class DuplicateNameError(ValidationError):
    """Raised when attempting to create/update an entity with a duplicate name."""

    def __init__(self, entity_type: str, name: str) -> None:
        super().__init__(
            message=f"Duplicate {entity_type} name: '{name}'",
            detail=f"A {entity_type} with name '{name}' already exists"
        )
        self.entity_type = entity_type
        self.name = name


class StorageError(DmoError):
    """Raised when a storage operation fails unexpectedly."""

    def __init__(self, operation: str, detail: Optional[str] = None) -> None:
        super().__init__(
            message=f"Storage operation failed: {operation}",
            detail=detail
        )
        self.operation = operation
```

---

## 5. Utility Functions (`src/dmo_core/utils.py`)

```python
"""
Utility functions for the DMO-Core system.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Sequence


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


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
    
    from datetime import timedelta
    
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
```

---

## 6. Storage Backend Interface (`src/dmo_core/storage/base.py`)

This is the abstract base class that defines the storage contract. All implementations must satisfy this interface.

```python
"""
Abstract storage backend interface.

This module defines the StorageBackend protocol that all storage
implementations must follow. Uses the Strategy pattern to allow
swapping storage backends without changing business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Sequence
from uuid import UUID

from dmo_core.models import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    DMOCompletionRead,
    DMOCreate,
    DMORead,
    DMOUpdate,
)


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    
    All methods are async to support both sync (via anyio) and async backends.
    Implementations must handle their own connection management and transactions.
    """

    # =========================================================================
    # Lifecycle
    # =========================================================================

    @abstractmethod
    async def init(self) -> None:
        """
        Initialize the storage backend.
        
        This should create tables/schema if they don't exist.
        Safe to call multiple times (idempotent).
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """
        Close the storage backend and release resources.
        
        After calling close(), the backend should not be used.
        """
        ...

    # =========================================================================
    # DMO Operations
    # =========================================================================

    @abstractmethod
    async def create_dmo(self, data: DMOCreate) -> DMORead:
        """
        Create a new DMO.
        
        Args:
            data: DMO creation data
        
        Returns:
            The created DMO with generated ID and timestamps
        
        Raises:
            DuplicateNameError: If a DMO with this name already exists
        """
        ...

    @abstractmethod
    async def get_dmo(self, dmo_id: UUID) -> DMORead:
        """
        Retrieve a DMO by ID.
        
        Args:
            dmo_id: The DMO's unique identifier
        
        Returns:
            The DMO data
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        """
        List all DMOs.
        
        Args:
            include_inactive: If True, include DMOs where active=False
        
        Returns:
            Sequence of DMOs, ordered by name ascending
        """
        ...

    @abstractmethod
    async def update_dmo(self, dmo_id: UUID, data: DMOUpdate) -> DMORead:
        """
        Update an existing DMO.
        
        Only fields that are not None in data will be updated.
        
        Args:
            dmo_id: The DMO's unique identifier
            data: Fields to update (None values are ignored)
        
        Returns:
            The updated DMO
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
            DuplicateNameError: If updating name to one that already exists
        """
        ...

    @abstractmethod
    async def delete_dmo(self, dmo_id: UUID) -> None:
        """
        Delete a DMO and all associated data.
        
        This performs a HARD delete of:
        - The DMO itself
        - All Activities belonging to this DMO
        - All DMOCompletion records for this DMO
        
        Args:
            dmo_id: The DMO's unique identifier
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    # =========================================================================
    # Activity Operations
    # =========================================================================

    @abstractmethod
    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        """
        Create a new Activity within a DMO.
        
        Args:
            data: Activity creation data (must include valid dmo_id)
        
        Returns:
            The created Activity with generated ID and timestamps
        
        Raises:
            DmoNotFoundError: If the referenced DMO does not exist
        """
        ...

    @abstractmethod
    async def get_activity(self, activity_id: UUID) -> ActivityRead:
        """
        Retrieve an Activity by ID.
        
        Args:
            activity_id: The Activity's unique identifier
        
        Returns:
            The Activity data
        
        Raises:
            ActivityNotFoundError: If no Activity exists with this ID
        """
        ...

    @abstractmethod
    async def list_activities(self, dmo_id: UUID) -> Sequence[ActivityRead]:
        """
        List all Activities for a DMO.
        
        Args:
            dmo_id: The DMO's unique identifier
        
        Returns:
            Sequence of Activities, ordered by 'order' field ascending
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def update_activity(
        self, activity_id: UUID, data: ActivityUpdate
    ) -> ActivityRead:
        """
        Update an existing Activity.
        
        Only fields that are not None in data will be updated.
        
        Args:
            activity_id: The Activity's unique identifier
            data: Fields to update (None values are ignored)
        
        Returns:
            The updated Activity
        
        Raises:
            ActivityNotFoundError: If no Activity exists with this ID
        """
        ...

    @abstractmethod
    async def delete_activity(self, activity_id: UUID) -> None:
        """
        Delete an Activity.
        
        Args:
            activity_id: The Activity's unique identifier
        
        Raises:
            ActivityNotFoundError: If no Activity exists with this ID
        """
        ...

    # =========================================================================
    # DMOCompletion Operations
    # =========================================================================

    @abstractmethod
    async def set_completion(
        self,
        dmo_id: UUID,
        completion_date: date,
        completed: bool,
        note: Optional[str] = None,
    ) -> DMOCompletionRead:
        """
        Set the completion status for a DMO on a specific date.
        
        This is an UPSERT operation:
        - If no record exists for (dmo_id, date): creates one
        - If a record exists: updates it
        
        This operation is idempotent.
        
        Args:
            dmo_id: The DMO's unique identifier
            completion_date: The date (user's local date)
            completed: Whether the DMO was completed
            note: Optional note about the completion
        
        Returns:
            The created or updated completion record
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def get_completion(
        self, dmo_id: UUID, completion_date: date
    ) -> Optional[DMOCompletionRead]:
        """
        Get the completion record for a DMO on a specific date.
        
        Args:
            dmo_id: The DMO's unique identifier
            completion_date: The date to query
        
        Returns:
            The completion record, or None if no record exists
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def list_completions(
        self,
        dmo_id: UUID,
        start: date,
        end: date,
    ) -> Sequence[DMOCompletionRead]:
        """
        List all completion records for a DMO within a date range.
        
        Args:
            dmo_id: The DMO's unique identifier
            start: Start date (inclusive)
            end: End date (inclusive)
        
        Returns:
            Sequence of completion records, ordered by date ascending
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
            ValueError: If start > end
        """
        ...

    @abstractmethod
    async def count_completed_days(
        self,
        dmo_id: UUID,
        start: date,
        end: date,
    ) -> int:
        """
        Count the number of completed days for a DMO in a date range.
        
        This is an optimization to avoid fetching all records when only
        the count is needed.
        
        Args:
            dmo_id: The DMO's unique identifier
            start: Start date (inclusive)
            end: End date (inclusive)
        
        Returns:
            Number of days where completed=True
        
        Raises:
            DmoNotFoundError: If no DMO exists with this ID
            ValueError: If start > end
        """
        ...
```

---

## 7. SQLite Backend Implementation (`src/dmo_core/storage/sqlite.py`)

```python
"""
SQLite storage backend implementation using aiosqlite.

This is the reference implementation of StorageBackend.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional, Sequence
from uuid import UUID, uuid4

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
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    timezone TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    dmo_id TEXT NOT NULL,
    name TEXT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (dmo_id) REFERENCES dmos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activities_dmo_id ON activities(dmo_id);
CREATE INDEX IF NOT EXISTS idx_activities_order ON activities(dmo_id, "order");

CREATE TABLE IF NOT EXISTS dmo_completions (
    id TEXT PRIMARY KEY,
    dmo_id TEXT NOT NULL,
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
        self._conn: Optional[aiosqlite.Connection] = None

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
            id=UUID(row["id"]),
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
            id=UUID(row["id"]),
            dmo_id=UUID(row["dmo_id"]),
            name=row["name"],
            order=row["order"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_completion(self, row: aiosqlite.Row) -> DMOCompletionRead:
        """Convert a database row to DMOCompletionRead model."""
        return DMOCompletionRead(
            id=UUID(row["id"]),
            dmo_id=UUID(row["dmo_id"]),
            date=date.fromisoformat(row["date"]),
            completed=bool(row["completed"]),
            note=row["note"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def _dmo_exists(self, dmo_id: UUID) -> bool:
        """Check if a DMO exists."""
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT 1 FROM dmos WHERE id = ?", (str(dmo_id),)
        )
        row = await cursor.fetchone()
        return row is not None

    async def _ensure_dmo_exists(self, dmo_id: UUID) -> None:
        """Raise DmoNotFoundError if DMO does not exist."""
        if not await self._dmo_exists(dmo_id):
            raise DmoNotFoundError(dmo_id)

    # =========================================================================
    # DMO Operations
    # =========================================================================

    async def create_dmo(self, data: DMOCreate) -> DMORead:
        conn = await self._get_conn()
        
        dmo_id = uuid4()
        now = utc_now().isoformat()
        
        try:
            await conn.execute(
                """
                INSERT INTO dmos (id, name, description, active, timezone, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?, ?)
                """,
                (str(dmo_id), data.name, data.description, data.timezone, now, now),
            )
            await conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: dmos.name" in str(e):
                raise DuplicateNameError("DMO", data.name) from e
            raise StorageError("create_dmo", str(e)) from e

        return await self.get_dmo(dmo_id)

    async def get_dmo(self, dmo_id: UUID) -> DMORead:
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT * FROM dmos WHERE id = ?", (str(dmo_id),)
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

    async def update_dmo(self, dmo_id: UUID, data: DMOUpdate) -> DMORead:
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
        values.append(str(dmo_id))
        
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

    async def delete_dmo(self, dmo_id: UUID) -> None:
        await self._ensure_dmo_exists(dmo_id)
        
        conn = await self._get_conn()
        await conn.execute("DELETE FROM dmos WHERE id = ?", (str(dmo_id),))
        await conn.commit()

    # =========================================================================
    # Activity Operations
    # =========================================================================

    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        await self._ensure_dmo_exists(data.dmo_id)
        
        conn = await self._get_conn()
        
        activity_id = uuid4()
        now = utc_now().isoformat()
        
        await conn.execute(
            """
            INSERT INTO activities (id, dmo_id, name, "order", created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(activity_id), str(data.dmo_id), data.name, data.order, now, now),
        )
        await conn.commit()
        
        return await self.get_activity(activity_id)

    async def get_activity(self, activity_id: UUID) -> ActivityRead:
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT * FROM activities WHERE id = ?", (str(activity_id),)
        )
        row = await cursor.fetchone()
        
        if row is None:
            raise ActivityNotFoundError(activity_id)
        
        return self._row_to_activity(row)

    async def list_activities(self, dmo_id: UUID) -> Sequence[ActivityRead]:
        await self._ensure_dmo_exists(dmo_id)
        
        conn = await self._get_conn()
        cursor = await conn.execute(
            'SELECT * FROM activities WHERE dmo_id = ? ORDER BY "order" ASC, created_at ASC',
            (str(dmo_id),),
        )
        rows = await cursor.fetchall()
        return [self._row_to_activity(row) for row in rows]

    async def update_activity(
        self, activity_id: UUID, data: ActivityUpdate
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
        values.append(str(activity_id))
        
        await conn.execute(
            f"UPDATE activities SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        await conn.commit()
        
        return await self.get_activity(activity_id)

    async def delete_activity(self, activity_id: UUID) -> None:
        # Verify activity exists
        await self.get_activity(activity_id)
        
        conn = await self._get_conn()
        await conn.execute("DELETE FROM activities WHERE id = ?", (str(activity_id),))
        await conn.commit()

    # =========================================================================
    # DMOCompletion Operations
    # =========================================================================

    async def set_completion(
        self,
        dmo_id: UUID,
        completion_date: date,
        completed: bool,
        note: Optional[str] = None,
    ) -> DMOCompletionRead:
        await self._ensure_dmo_exists(dmo_id)
        
        conn = await self._get_conn()
        now = utc_now().isoformat()
        date_str = completion_date.isoformat()
        
        # Check if record exists
        cursor = await conn.execute(
            "SELECT id FROM dmo_completions WHERE dmo_id = ? AND date = ?",
            (str(dmo_id), date_str),
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
                (1 if completed else 0, note, now, str(dmo_id), date_str),
            )
        else:
            # Insert new
            completion_id = uuid4()
            await conn.execute(
                """
                INSERT INTO dmo_completions (id, dmo_id, date, completed, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (str(completion_id), str(dmo_id), date_str, 1 if completed else 0, note, now, now),
            )
        
        await conn.commit()
        
        # Fetch and return the record
        result = await self.get_completion(dmo_id, completion_date)
        assert result is not None  # We just created/updated it
        return result

    async def get_completion(
        self, dmo_id: UUID, completion_date: date
    ) -> Optional[DMOCompletionRead]:
        await self._ensure_dmo_exists(dmo_id)
        
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT * FROM dmo_completions WHERE dmo_id = ? AND date = ?",
            (str(dmo_id), completion_date.isoformat()),
        )
        row = await cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_completion(row)

    async def list_completions(
        self,
        dmo_id: UUID,
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
            (str(dmo_id), start.isoformat(), end.isoformat()),
        )
        rows = await cursor.fetchall()
        return [self._row_to_completion(row) for row in rows]

    async def count_completed_days(
        self,
        dmo_id: UUID,
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
            (str(dmo_id), start.isoformat(), end.isoformat()),
        )
        row = await cursor.fetchone()
        return int(row["count"]) if row else 0
```

---

## 8. In-Memory Backend (`src/dmo_core/storage/memory.py`)

This is a lightweight implementation for testing purposes.

```python
"""
In-memory storage backend for testing.

This implementation stores all data in Python dictionaries.
It's useful for unit tests where database setup overhead is undesirable.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence
from uuid import UUID, uuid4

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
        self._dmos: dict[UUID, DMORead] = {}
        self._activities: dict[UUID, ActivityRead] = {}
        self._completions: dict[tuple[UUID, date], DMOCompletionRead] = {}
        self._completion_ids: dict[UUID, tuple[UUID, date]] = {}  # id -> (dmo_id, date)

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
        dmo = DMORead(
            id=uuid4(),
            name=data.name,
            description=data.description,
            active=True,
            timezone=data.timezone,
            created_at=now,
            updated_at=now,
        )
        self._dmos[dmo.id] = dmo
        return dmo

    async def get_dmo(self, dmo_id: UUID) -> DMORead:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)
        return self._dmos[dmo_id]

    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        dmos = list(self._dmos.values())
        if not include_inactive:
            dmos = [d for d in dmos if d.active]
        return sorted(dmos, key=lambda d: d.name)

    async def update_dmo(self, dmo_id: UUID, data: DMOUpdate) -> DMORead:
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

    async def delete_dmo(self, dmo_id: UUID) -> None:
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
            key for key in self._completions.keys() if key[0] == dmo_id
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
        activity = ActivityRead(
            id=uuid4(),
            dmo_id=data.dmo_id,
            name=data.name,
            order=data.order,
            created_at=now,
            updated_at=now,
        )
        self._activities[activity.id] = activity
        return activity

    async def get_activity(self, activity_id: UUID) -> ActivityRead:
        if activity_id not in self._activities:
            raise ActivityNotFoundError(activity_id)
        return self._activities[activity_id]

    async def list_activities(self, dmo_id: UUID) -> Sequence[ActivityRead]:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)
        
        activities = [a for a in self._activities.values() if a.dmo_id == dmo_id]
        return sorted(activities, key=lambda a: (a.order, a.created_at))

    async def update_activity(
        self, activity_id: UUID, data: ActivityUpdate
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

    async def delete_activity(self, activity_id: UUID) -> None:
        if activity_id not in self._activities:
            raise ActivityNotFoundError(activity_id)
        del self._activities[activity_id]

    # =========================================================================
    # DMOCompletion Operations
    # =========================================================================

    async def set_completion(
        self,
        dmo_id: UUID,
        completion_date: date,
        completed: bool,
        note: Optional[str] = None,
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
            completion = DMOCompletionRead(
                id=uuid4(),
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
        self, dmo_id: UUID, completion_date: date
    ) -> Optional[DMOCompletionRead]:
        if dmo_id not in self._dmos:
            raise DmoNotFoundError(dmo_id)
        
        key = (dmo_id, completion_date)
        return self._completions.get(key)

    async def list_completions(
        self,
        dmo_id: UUID,
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
        dmo_id: UUID,
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
```

---

## 9. Storage Package Init (`src/dmo_core/storage/__init__.py`)

```python
"""
Storage backends for DMO-Core.

Available backends:
- SqliteBackend: Production-ready SQLite backend using aiosqlite
- MemoryBackend: In-memory backend for testing
"""

from dmo_core.storage.base import StorageBackend
from dmo_core.storage.memory import MemoryBackend
from dmo_core.storage.sqlite import SqliteBackend

__all__ = ["StorageBackend", "SqliteBackend", "MemoryBackend"]
```

---

## 10. Service Layer (`src/dmo_core/service.py`)

```python
"""
DmoService: High-level business logic layer.

This service provides the main API for interacting with the DMO system.
It handles reporting, streak calculations, and orchestrates storage operations.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence
from uuid import UUID

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

    async def get_dmo(self, dmo_id: UUID) -> DMORead:
        """Get a DMO by ID."""
        return await self._storage.get_dmo(dmo_id)

    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        """List all DMOs, optionally including inactive ones."""
        return await self._storage.list_dmos(include_inactive=include_inactive)

    async def update_dmo(self, dmo_id: UUID, data: DMOUpdate) -> DMORead:
        """Update a DMO."""
        return await self._storage.update_dmo(dmo_id, data)

    async def delete_dmo(self, dmo_id: UUID) -> None:
        """Delete a DMO and all associated data."""
        await self._storage.delete_dmo(dmo_id)

    async def deactivate_dmo(self, dmo_id: UUID) -> DMORead:
        """Soft-delete a DMO by setting active=False."""
        return await self._storage.update_dmo(dmo_id, DMOUpdate(active=False))

    async def activate_dmo(self, dmo_id: UUID) -> DMORead:
        """Re-activate a deactivated DMO."""
        return await self._storage.update_dmo(dmo_id, DMOUpdate(active=True))

    # =========================================================================
    # Activity Operations
    # =========================================================================

    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        """Create a new Activity within a DMO."""
        return await self._storage.create_activity(data)

    async def get_activity(self, activity_id: UUID) -> ActivityRead:
        """Get an Activity by ID."""
        return await self._storage.get_activity(activity_id)

    async def list_activities(self, dmo_id: UUID) -> Sequence[ActivityRead]:
        """List all Activities for a DMO, ordered by 'order' field."""
        return await self._storage.list_activities(dmo_id)

    async def update_activity(
        self, activity_id: UUID, data: ActivityUpdate
    ) -> ActivityRead:
        """Update an Activity."""
        return await self._storage.update_activity(activity_id, data)

    async def delete_activity(self, activity_id: UUID) -> None:
        """Delete an Activity."""
        await self._storage.delete_activity(activity_id)

    async def reorder_activities(
        self, dmo_id: UUID, activity_ids: Sequence[UUID]
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
        dmo_id: UUID,
        completion_date: date,
        completed: bool,
        note: Optional[str] = None,
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
        self, dmo_id: UUID, completion_date: date
    ) -> Optional[DMOCompletionRead]:
        """Get the completion record for a DMO on a specific date."""
        return await self._storage.get_completion(dmo_id, completion_date)

    async def mark_complete(
        self, dmo_id: UUID, completion_date: date, note: Optional[str] = None
    ) -> DMOCompletionRead:
        """Convenience method to mark a DMO as complete."""
        return await self.set_dmo_completion(dmo_id, completion_date, True, note)

    async def mark_incomplete(
        self, dmo_id: UUID, completion_date: date, note: Optional[str] = None
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
        dmo_id: Optional[UUID] = None,
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
        dmo_id: UUID,
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
```

---

## 11. Package Init (`src/dmo_core/__init__.py`)

```python
"""
DMO-Core: Core service layer for Daily Methods of Operation tracking.

This package provides a discipline-tracking system where the unit of truth
is "Did I complete my DMO today?" - a single boolean judgment per DMO per day.

Quick Start:
    ```python
    import asyncio
    from datetime import date
    from dmo_core import DmoService, DMOCreate
    from dmo_core.storage import SqliteBackend
    
    async def main():
        # Initialize storage
        backend = SqliteBackend("my_dmos.db")
        await backend.init()
        
        # Create service
        service = DmoService(backend)
        
        # Create a DMO
        dmo = await service.create_dmo(DMOCreate(name="Morning Routine"))
        
        # Mark it complete for today
        await service.mark_complete(dmo.id, date.today())
        
        # Get daily report
        report = await service.get_daily_report(date.today())
        print(report)
        
        # Cleanup
        await backend.close()
    
    asyncio.run(main())
    ```
"""

from dmo_core.errors import (
    ActivityNotFoundError,
    DmoError,
    DmoNotFoundError,
    DuplicateNameError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from dmo_core.models import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    DailyReport,
    DayCompletion,
    DMOCompletionCreate,
    DMOCompletionRead,
    DMOCreate,
    DMODailyStatus,
    DMORead,
    DMOSummary,
    DMOUpdate,
    MonthlyReport,
    MonthSummary,
)
from dmo_core.service import DmoService

__version__ = "0.1.0"

__all__ = [
    # Service
    "DmoService",
    # Models - DMO
    "DMOCreate",
    "DMOUpdate",
    "DMORead",
    # Models - Activity
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityRead",
    # Models - Completion
    "DMOCompletionCreate",
    "DMOCompletionRead",
    # Models - Reports
    "DailyReport",
    "DMODailyStatus",
    "DayCompletion",
    "MonthlyReport",
    "MonthSummary",
    "DMOSummary",
    # Errors
    "DmoError",
    "NotFoundError",
    "DmoNotFoundError",
    "ActivityNotFoundError",
    "ValidationError",
    "DuplicateNameError",
    "StorageError",
]
```

---

## 12. Test Configuration (`tests/conftest.py`)

```python
"""
Shared pytest fixtures for DMO-Core tests.
"""

from __future__ import annotations

from datetime import date
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio

from dmo_core import ActivityCreate, DMOCreate, DmoService
from dmo_core.storage import MemoryBackend, SqliteBackend, StorageBackend


@pytest_asyncio.fixture
async def memory_backend() -> AsyncGenerator[MemoryBackend, None]:
    """Provide an initialized MemoryBackend."""
    backend = MemoryBackend()
    await backend.init()
    yield backend
    await backend.close()


@pytest_asyncio.fixture
async def sqlite_backend(tmp_path) -> AsyncGenerator[SqliteBackend, None]:
    """Provide an initialized SqliteBackend with a temporary database."""
    db_path = str(tmp_path / "test.db")
    backend = SqliteBackend(db_path)
    await backend.init()
    yield backend
    await backend.close()


@pytest_asyncio.fixture
async def memory_service(memory_backend: MemoryBackend) -> DmoService:
    """Provide a DmoService with MemoryBackend."""
    return DmoService(memory_backend)


@pytest_asyncio.fixture
async def sqlite_service(sqlite_backend: SqliteBackend) -> DmoService:
    """Provide a DmoService with SqliteBackend."""
    return DmoService(sqlite_backend)


@pytest.fixture
def sample_dmo_create() -> DMOCreate:
    """Sample DMO creation data."""
    return DMOCreate(
        name="Morning Routine",
        description="My daily morning routine for a productive day",
        timezone="America/New_York",
    )


@pytest.fixture
def sample_activity_creates() -> list[ActivityCreate]:
    """Sample Activity creation data (requires dmo_id to be set)."""
    # Note: dmo_id must be filled in by the test
    return [
        ActivityCreate(dmo_id=UUID("00000000-0000-0000-0000-000000000000"), name="Meditate 10 minutes", order=0),
        ActivityCreate(dmo_id=UUID("00000000-0000-0000-0000-000000000000"), name="Review daily plan", order=1),
        ActivityCreate(dmo_id=UUID("00000000-0000-0000-0000-000000000000"), name="Walk 5,000 steps", order=2),
    ]


@pytest.fixture
def today() -> date:
    """Today's date."""
    return date.today()


@pytest.fixture
def february_2026_dates() -> list[date]:
    """All dates in February 2026 (28 days)."""
    return [date(2026, 2, d) for d in range(1, 29)]
```

---

## 13. Model Tests (`tests/test_models.py`)

```python
"""
Tests for Pydantic models validation.
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from dmo_core.models import (
    ActivityCreate,
    ActivityUpdate,
    DMOCreate,
    DMORead,
    DMOUpdate,
    MonthSummary,
)


class TestDMOCreate:
    """Tests for DMOCreate model."""

    def test_valid_minimal(self):
        """Test creating with minimal required fields."""
        dmo = DMOCreate(name="Test DMO")
        assert dmo.name == "Test DMO"
        assert dmo.description is None
        assert dmo.timezone is None

    def test_valid_full(self):
        """Test creating with all fields."""
        dmo = DMOCreate(
            name="Test DMO",
            description="A test description",
            timezone="America/New_York",
        )
        assert dmo.name == "Test DMO"
        assert dmo.description == "A test description"
        assert dmo.timezone == "America/New_York"

    def test_name_stripped(self):
        """Test that name is stripped of whitespace."""
        dmo = DMOCreate(name="  Test DMO  ")
        assert dmo.name == "Test DMO"

    def test_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DMOCreate(name="")
        assert "name" in str(exc_info.value)

    def test_whitespace_only_name_rejected(self):
        """Test that whitespace-only name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DMOCreate(name="   ")
        assert "name" in str(exc_info.value)

    def test_name_max_length(self):
        """Test that name over 255 chars is rejected."""
        with pytest.raises(ValidationError):
            DMOCreate(name="x" * 256)


class TestDMOUpdate:
    """Tests for DMOUpdate model."""

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        update = DMOUpdate()
        assert update.name is None
        assert update.description is None
        assert update.timezone is None
        assert update.active is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        update = DMOUpdate(name="New Name", active=False)
        assert update.name == "New Name"
        assert update.active is False
        assert update.description is None


class TestActivityCreate:
    """Tests for ActivityCreate model."""

    def test_valid_minimal(self):
        """Test with minimal fields."""
        dmo_id = uuid4()
        activity = ActivityCreate(dmo_id=dmo_id, name="Test Activity")
        assert activity.dmo_id == dmo_id
        assert activity.name == "Test Activity"
        assert activity.order == 0

    def test_custom_order(self):
        """Test with custom order."""
        dmo_id = uuid4()
        activity = ActivityCreate(dmo_id=dmo_id, name="Test", order=5)
        assert activity.order == 5

    def test_negative_order_rejected(self):
        """Test that negative order is rejected."""
        with pytest.raises(ValidationError):
            ActivityCreate(dmo_id=uuid4(), name="Test", order=-1)


class TestMonthSummary:
    """Tests for MonthSummary model."""

    def test_completion_rate_bounds(self):
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
```

---

## 14. Storage Tests (`tests/test_storage_sqlite.py`)

```python
"""
Tests for SQLite storage backend.
"""

from datetime import date
from uuid import uuid4

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

    async def test_create_dmo(self, sqlite_backend: SqliteBackend):
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

    async def test_create_dmo_duplicate_name(self, sqlite_backend: SqliteBackend):
        """Test that duplicate names are rejected."""
        await sqlite_backend.create_dmo(DMOCreate(name="Unique Name"))
        
        with pytest.raises(DuplicateNameError) as exc_info:
            await sqlite_backend.create_dmo(DMOCreate(name="Unique Name"))
        
        assert exc_info.value.name == "Unique Name"

    async def test_get_dmo(self, sqlite_backend: SqliteBackend):
        """Test retrieving a DMO by ID."""
        created = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        retrieved = await sqlite_backend.get_dmo(created.id)
        
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    async def test_get_dmo_not_found(self, sqlite_backend: SqliteBackend):
        """Test that getting non-existent DMO raises error."""
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.get_dmo(uuid4())

    async def test_list_dmos(self, sqlite_backend: SqliteBackend):
        """Test listing DMOs."""
        await sqlite_backend.create_dmo(DMOCreate(name="Alpha"))
        await sqlite_backend.create_dmo(DMOCreate(name="Beta"))
        
        dmos = await sqlite_backend.list_dmos()
        
        assert len(dmos) == 2
        assert dmos[0].name == "Alpha"  # Ordered by name
        assert dmos[1].name == "Beta"

    async def test_list_dmos_excludes_inactive(self, sqlite_backend: SqliteBackend):
        """Test that inactive DMOs are excluded by default."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        await sqlite_backend.update_dmo(dmo.id, DMOUpdate(active=False))
        
        dmos = await sqlite_backend.list_dmos()
        assert len(dmos) == 0
        
        dmos = await sqlite_backend.list_dmos(include_inactive=True)
        assert len(dmos) == 1

    async def test_update_dmo(self, sqlite_backend: SqliteBackend):
        """Test updating a DMO."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Original"))
        
        updated = await sqlite_backend.update_dmo(
            dmo.id, DMOUpdate(name="Updated", active=False)
        )
        
        assert updated.name == "Updated"
        assert updated.active is False
        assert updated.updated_at > dmo.updated_at

    async def test_delete_dmo(self, sqlite_backend: SqliteBackend):
        """Test deleting a DMO."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="To Delete"))
        await sqlite_backend.delete_dmo(dmo.id)
        
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.get_dmo(dmo.id)

    async def test_delete_dmo_cascades_activities(self, sqlite_backend: SqliteBackend):
        """Test that deleting a DMO also deletes its activities."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        activity = await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Activity")
        )
        
        await sqlite_backend.delete_dmo(dmo.id)
        
        with pytest.raises(ActivityNotFoundError):
            await sqlite_backend.get_activity(activity.id)

    async def test_delete_dmo_cascades_completions(self, sqlite_backend: SqliteBackend):
        """Test that deleting a DMO also deletes its completions."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        await sqlite_backend.set_completion(dmo.id, date(2026, 1, 1), True)
        
        await sqlite_backend.delete_dmo(dmo.id)
        
        # DMO is gone, so we can't even query completions
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.get_completion(dmo.id, date(2026, 1, 1))


class TestSqliteBackendActivity:
    """Tests for Activity operations in SQLite backend."""

    async def test_create_activity(self, sqlite_backend: SqliteBackend):
        """Test creating an activity."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        
        activity = await sqlite_backend.create_activity(
            ActivityCreate(dmo_id=dmo.id, name="Activity 1", order=0)
        )
        
        assert activity.id is not None
        assert activity.dmo_id == dmo.id
        assert activity.name == "Activity 1"
        assert activity.order == 0

    async def test_create_activity_invalid_dmo(self, sqlite_backend: SqliteBackend):
        """Test that creating activity with invalid DMO raises error."""
        with pytest.raises(DmoNotFoundError):
            await sqlite_backend.create_activity(
                ActivityCreate(dmo_id=uuid4(), name="Activity")
            )

    async def test_list_activities_ordered(self, sqlite_backend: SqliteBackend):
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

    async def test_set_completion_create(self, sqlite_backend: SqliteBackend):
        """Test creating a new completion record."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        
        completion = await sqlite_backend.set_completion(
            dmo.id, date(2026, 1, 15), True, "Great day!"
        )
        
        assert completion.dmo_id == dmo.id
        assert completion.date == date(2026, 1, 15)
        assert completion.completed is True
        assert completion.note == "Great day!"

    async def test_set_completion_update(self, sqlite_backend: SqliteBackend):
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

    async def test_set_completion_idempotent(self, sqlite_backend: SqliteBackend):
        """Test that set_completion is idempotent."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        
        c1 = await sqlite_backend.set_completion(dmo.id, date(2026, 1, 15), True)
        c2 = await sqlite_backend.set_completion(dmo.id, date(2026, 1, 15), True)
        
        assert c1.id == c2.id  # Same record

    async def test_get_completion_not_found(self, sqlite_backend: SqliteBackend):
        """Test getting non-existent completion returns None."""
        dmo = await sqlite_backend.create_dmo(DMOCreate(name="Test"))
        
        result = await sqlite_backend.get_completion(dmo.id, date(2026, 1, 15))
        
        assert result is None

    async def test_list_completions(self, sqlite_backend: SqliteBackend):
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

    async def test_count_completed_days(self, sqlite_backend: SqliteBackend):
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
```

---

## 15. Service Tests (`tests/test_service.py`)

```python
"""
Tests for DmoService business logic.
"""

from datetime import date

import pytest

from dmo_core import ActivityCreate, DMOCreate, DmoService


class TestDmoServiceReports:
    """Tests for reporting functionality."""

    async def test_get_daily_report_empty(self, memory_service: DmoService):
        """Test daily report with no DMOs."""
        report = await memory_service.get_daily_report(date(2026, 1, 15))
        
        assert report.date == date(2026, 1, 15)
        assert len(report.dmos) == 0

    async def test_get_daily_report_with_dmo(self, memory_service: DmoService):
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

    async def test_get_monthly_report(self, memory_service: DmoService):
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

    async def test_streak_calculation(self, memory_service: DmoService):
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

    async def test_dmo_summary(self, memory_service: DmoService):
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

    async def test_mark_complete_idempotent(self, memory_service: DmoService):
        """Test that marking complete multiple times is safe."""
        dmo = await memory_service.create_dmo(DMOCreate(name="Test"))
        
        c1 = await memory_service.mark_complete(dmo.id, date(2026, 1, 15))
        c2 = await memory_service.mark_complete(dmo.id, date(2026, 1, 15))
        
        assert c1.id == c2.id
        assert c1.completed == c2.completed == True


class TestDmoServiceActivities:
    """Tests for activity management."""

    async def test_reorder_activities(self, memory_service: DmoService):
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
    ):
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
```

---

## 16. Utility Tests (`tests/test_utils.py`)

```python
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

    def test_single_day(self):
        """Test range of a single day."""
        result = date_range(date(2026, 1, 1), date(2026, 1, 1))
        assert result == [date(2026, 1, 1)]

    def test_multiple_days(self):
        """Test range of multiple days."""
        result = date_range(date(2026, 1, 1), date(2026, 1, 5))
        assert len(result) == 5
        assert result[0] == date(2026, 1, 1)
        assert result[-1] == date(2026, 1, 5)

    def test_invalid_range(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError):
            date_range(date(2026, 1, 5), date(2026, 1, 1))


class TestDaysInMonth:
    """Tests for days_in_month function."""

    def test_january(self):
        assert days_in_month(2026, 1) == 31

    def test_february_non_leap(self):
        assert days_in_month(2026, 2) == 28

    def test_february_leap(self):
        assert days_in_month(2024, 2) == 29

    def test_april(self):
        assert days_in_month(2026, 4) == 30


class TestCalculateStreaks:
    """Tests for calculate_streaks function."""

    def test_empty_dates(self):
        """Test with no dates."""
        current, longest = calculate_streaks(set(), [])
        assert current == 0
        assert longest == 0

    def test_no_completions(self):
        """Test with dates but no completions."""
        all_dates = [date(2026, 1, d) for d in range(1, 6)]
        current, longest = calculate_streaks(set(), all_dates)
        assert current == 0
        assert longest == 0

    def test_all_completed(self):
        """Test when all days are completed."""
        all_dates = [date(2026, 1, d) for d in range(1, 6)]
        completed = set(all_dates)
        
        current, longest = calculate_streaks(completed, all_dates)
        assert current == 5
        assert longest == 5

    def test_streak_in_middle(self):
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

    def test_current_streak_broken(self):
        """Test current streak is 0 when last day is not completed."""
        all_dates = [date(2026, 1, d) for d in range(1, 6)]
        completed = {date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)}
        # Days 4, 5 not completed
        
        current, longest = calculate_streaks(completed, all_dates)
        
        assert longest == 3
        assert current == 0  # Broken by days 4, 5


class TestCalculateCompletionRate:
    """Tests for calculate_completion_rate function."""

    def test_zero_total(self):
        """Test with zero total days."""
        assert calculate_completion_rate(0, 0) == 0.0

    def test_full_completion(self):
        """Test 100% completion."""
        assert calculate_completion_rate(10, 10) == 1.0

    def test_partial_completion(self):
        """Test partial completion."""
        rate = calculate_completion_rate(7, 10)
        assert rate == pytest.approx(0.7, abs=0.001)

    def test_rounding(self):
        """Test that rate is rounded to 4 decimal places."""
        rate = calculate_completion_rate(1, 3)
        assert rate == pytest.approx(0.3333, abs=0.0001)
```

---

## 17. Integration Tests (`tests/test_integration.py`)

```python
"""
Integration tests verifying end-to-end workflows.
"""

from datetime import date

import pytest

from dmo_core import ActivityCreate, DMOCreate, DMOUpdate, DmoService
from dmo_core.storage import SqliteBackend


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    async def test_complete_workflow(self, sqlite_service: DmoService):
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
        dmo_status = report.dmos[0]
        assert dmo_status.completed is True
        assert dmo_status.note == "Back on track"
        assert len(dmo_status.activities) == 5
        
        # 5. Get summary for the week
        summary = await sqlite_service.get_dmo_summary(
            dmo.id, date(2026, 2, 1), date(2026, 2, 7)
        )
        
        assert summary.total_days == 7
        assert summary.completed_days == 6
        assert summary.completion_rate == pytest.approx(6 / 7, abs=0.001)
        assert summary.longest_streak == 4  # Days 4-7
        assert summary.current_streak == 4

    async def test_multiple_dmos(self, sqlite_service: DmoService):
        """Test tracking multiple DMOs simultaneously."""
        # Create two DMOs
        morning = await sqlite_service.create_dmo(
            DMOCreate(name="Morning Routine")
        )
        evening = await sqlite_service.create_dmo(
            DMOCreate(name="Evening Review")
        )
        
        # Track different patterns
        await sqlite_service.mark_complete(morning.id, date(2026, 2, 1))
        await sqlite_service.mark_incomplete(evening.id, date(2026, 2, 1))
        
        await sqlite_service.mark_complete(morning.id, date(2026, 2, 2))
        await sqlite_service.mark_complete(evening.id, date(2026, 2, 2))
        
        # Get daily report
        report = await sqlite_service.get_daily_report(date(2026, 2, 1))
        
        assert len(report.dmos) == 2
        
        morning_status = next(d for d in report.dmos if d.dmo.name == "Morning Routine")
        evening_status = next(d for d in report.dmos if d.dmo.name == "Evening Review")
        
        assert morning_status.completed is True
        assert evening_status.completed is False

    async def test_deactivation_workflow(self, sqlite_service: DmoService):
        """Test deactivating and reactivating a DMO."""
        dmo = await sqlite_service.create_dmo(DMOCreate(name="Test"))
        await sqlite_service.mark_complete(dmo.id, date(2026, 2, 1))
        
        # Deactivate
        deactivated = await sqlite_service.deactivate_dmo(dmo.id)
        assert deactivated.active is False
        
        # Should not appear in daily report
        report = await sqlite_service.get_daily_report(date(2026, 2, 1))
        assert len(report.dmos) == 0
        
        # Should appear when including inactive
        all_dmos = await sqlite_service.list_dmos(include_inactive=True)
        assert len(all_dmos) == 1
        
        # Reactivate
        reactivated = await sqlite_service.activate_dmo(dmo.id)
        assert reactivated.active is True
        
        # Should appear in daily report again
        report = await sqlite_service.get_daily_report(date(2026, 2, 1))
        assert len(report.dmos) == 1
        assert report.dmos[0].completed is True  # Historical data preserved
```

---

## 18. Implementation Checklist

Use this checklist to verify complete implementation:

### Core Files
- [ ] `pyproject.toml` with all dependencies
- [ ] `src/dmo_core/__init__.py` with public exports
- [ ] `src/dmo_core/models.py` with all Pydantic models
- [ ] `src/dmo_core/errors.py` with exception hierarchy
- [ ] `src/dmo_core/utils.py` with helper functions
- [ ] `src/dmo_core/service.py` with DmoService class

### Storage Layer
- [ ] `src/dmo_core/storage/__init__.py` with exports
- [ ] `src/dmo_core/storage/base.py` with StorageBackend ABC
- [ ] `src/dmo_core/storage/sqlite.py` with SqliteBackend
- [ ] `src/dmo_core/storage/memory.py` with MemoryBackend

### Tests
- [ ] `tests/conftest.py` with fixtures
- [ ] `tests/test_models.py` - All pass
- [ ] `tests/test_storage_sqlite.py` - All pass
- [ ] `tests/test_service.py` - All pass
- [ ] `tests/test_utils.py` - All pass
- [ ] `tests/test_integration.py` - All pass

### Quality Gates
- [ ] `mypy src tests --strict` passes with no errors
- [ ] `ruff check src tests` passes with no errors
- [ ] `pytest --cov=dmo_core --cov-report=term-missing` shows >80% coverage

---

## 19. Usage Example

Create a `README.md` with this usage example:

```markdown
# DMO-Core

A discipline-tracking library for Daily Methods of Operation.

## Quick Start

```python
import asyncio
from datetime import date
from dmo_core import DmoService, DMOCreate, ActivityCreate
from dmo_core.storage import SqliteBackend

async def main():
    # Initialize
    backend = SqliteBackend("my_dmos.db")
    await backend.init()
    service = DmoService(backend)
    
    # Create a DMO
    dmo = await service.create_dmo(DMOCreate(
        name="Morning Routine",
        description="Start every day right"
    ))
    
    # Add checklist items (for reference only)
    await service.create_activity(ActivityCreate(
        dmo_id=dmo.id, name="Meditate 10 minutes", order=0
    ))
    await service.create_activity(ActivityCreate(
        dmo_id=dmo.id, name="Review daily goals", order=1
    ))
    
    # Track completion (the only thing that matters!)
    await service.mark_complete(dmo.id, date.today(), "Felt great!")
    
    # Get your daily report
    report = await service.get_daily_report(date.today())
    print(f"Date: {report.date}")
    for status in report.dmos:
        icon = "✅" if status.completed else "❌"
        print(f"  {icon} {status.dmo.name}")
    
    # Get monthly stats
    reports = await service.get_monthly_report(2026, 2)
    for r in reports:
        print(f"\n{r.dmo.name} - February 2026")
        print(f"  Completion: {r.summary.completion_rate:.0%}")
        print(f"  Current streak: {r.summary.current_streak} days")
        print(f"  Longest streak: {r.summary.longest_streak} days")
    
    await backend.close()

asyncio.run(main())
```

## Philosophy

This is a **discipline-tracking system**, not a task manager:

- ✅ "Did I complete my DMO today?" (binary, subjective)
- ❌ "How many activities did I check off?" (not tracked)

The user decides what "done" means. Activities are just a reference checklist.
```

---

## 20. Final Notes for Implementation

1. **Type Safety**: Every function must have complete type annotations. Run `mypy --strict` and fix all errors.

2. **Async Throughout**: All storage and service methods are async. Use `async def` consistently.

3. **Error Handling**: Always raise the appropriate custom exception. Never return `None` for "not found" in methods that should raise.

4. **Immutability**: Pydantic models are the source of truth. Never mutate returned models; create new instances.

5. **Testing**: Write tests BEFORE or alongside implementation. Every public method needs test coverage.

6. **Documentation**: Include docstrings with Args, Returns, and Raises sections for all public methods.

The implementation is complete when:
- All tests pass
- Type checking passes
- Code coverage exceeds 80%
- The usage example runs successfully

