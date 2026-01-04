"""
Dependency injection for FastAPI application with backend selection support.

Provides dependency functions for database connections and service initialization.
Supports both SQLite and PostgreSQL backends via environment variables.
"""

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from dmo_core import DmoService
from dmo_core.storage import StorageBackend, SqliteBackend

# Conditionally import PostgresBackend
try:
    from dmo_core.storage import PostgresBackend
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

# Default database location for SQLite
DEFAULT_DB_DIR = Path.home() / ".dmo"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "dmo.db"


def get_db_path() -> Path:
    """Get the database path, creating directory if needed."""
    db_dir = DEFAULT_DB_DIR
    db_dir.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH


def get_backend() -> StorageBackend:
    """
    Get storage backend based on environment configuration.

    Checks STORAGE_BACKEND and DATABASE_URL environment variables:
    - STORAGE_BACKEND=postgres: Use PostgresBackend with DATABASE_URL
    - Otherwise: Use SqliteBackend (default)

    Returns:
        StorageBackend: Configured storage backend

    Raises:
        RuntimeError: If postgres requested but not installed or no DATABASE_URL
    """
    storage_type = os.getenv("STORAGE_BACKEND", "sqlite").lower()

    if storage_type == "postgres":
        if not HAS_POSTGRES:
            raise RuntimeError(
                "PostgreSQL backend requested but asyncpg not installed. "
                "Install with: pip install 'dmo-core[postgres]'"
            )

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL environment variable required for Postgres backend"
            )

        return PostgresBackend(dsn=database_url)

    else:
        # SQLite backend (default)
        db_path = get_db_path()
        return SqliteBackend(str(db_path))


async def get_service() -> AsyncGenerator[DmoService, None]:
    """
    Dependency that provides a DmoService instance.

    Initializes the configured backend and yields a service instance.
    Automatically closes the backend when the request completes.

    Yields:
        DmoService: Initialized service instance
    """
    backend = get_backend()
    await backend.init()
    service = DmoService(backend)

    try:
        yield service
    finally:
        await backend.close()


# Type annotation for dependency injection
ServiceDep = Annotated[DmoService, Depends(get_service)]
