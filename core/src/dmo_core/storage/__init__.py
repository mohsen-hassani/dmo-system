"""
Storage backends for DMO-Core.

Available backends:
- SqliteBackend: Production-ready SQLite backend using aiosqlite
- MemoryBackend: In-memory backend for testing
- PostgresBackend: Production-ready PostgreSQL backend using asyncpg (requires postgres extra)
"""

from dmo_core.storage.base import StorageBackend
from dmo_core.storage.memory import MemoryBackend
from dmo_core.storage.sqlite import SqliteBackend

# Conditionally import PostgresBackend (requires asyncpg extra)
try:
    from dmo_core.storage.postgres import PostgresBackend
    __all__ = ["StorageBackend", "SqliteBackend", "MemoryBackend", "PostgresBackend"]
except ImportError:
    __all__ = ["StorageBackend", "SqliteBackend", "MemoryBackend"]
