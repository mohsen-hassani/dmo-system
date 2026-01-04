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
