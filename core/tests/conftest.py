"""
Shared pytest fixtures for DMO-Core tests.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date
from pathlib import Path

import pytest
import pytest_asyncio

from dmo_core import ActivityCreate, DMOCreate, DmoService
from dmo_core.storage import MemoryBackend, SqliteBackend


@pytest_asyncio.fixture
async def memory_backend() -> AsyncGenerator[MemoryBackend, None]:
    """Provide an initialized MemoryBackend."""
    backend = MemoryBackend()
    await backend.init()
    yield backend
    await backend.close()


@pytest_asyncio.fixture
async def sqlite_backend(tmp_path: Path) -> AsyncGenerator[SqliteBackend, None]:
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
    dummy_id = 0
    return [
        ActivityCreate(dmo_id=dummy_id, name="Meditate 10 minutes", order=0),
        ActivityCreate(dmo_id=dummy_id, name="Review daily plan", order=1),
        ActivityCreate(dmo_id=dummy_id, name="Walk 5,000 steps", order=2),
    ]


@pytest.fixture
def today() -> date:
    """Today's date."""
    return date.today()


@pytest.fixture
def february_2026_dates() -> list[date]:
    """All dates in February 2026 (28 days)."""
    return [date(2026, 2, d) for d in range(1, 29)]
