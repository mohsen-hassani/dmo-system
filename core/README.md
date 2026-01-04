# DMO-Core

Core service layer for Daily Methods of Operation (DMO) tracking - a discipline-tracking system focused on daily completion.

## Overview

**DMO-Core** is a Python library for tracking Daily Methods of Operation. This is a **discipline-tracking system, NOT a task manager**.

The single most important concept: **A DMO is either completed or not completed on any given day**. This is a binary, subjective judgment by the user. Activities exist only as a descriptive checklist to help remember what "done" means—they have zero effect on completion logic.

## Features

- **Simple completion tracking**: Mark DMOs as complete or incomplete for any day
- **Activity checklists**: Define activities as reference only (no per-activity tracking)
- **Flexible storage**: SQLite and in-memory backends with pluggable architecture
- **Rich reporting**: Daily reports, monthly summaries, and streak calculations
- **Type-safe**: Full mypy strict mode compliance
- **Async-first**: Built on async/await for modern Python applications
- **Well-tested**: 85%+ test coverage with comprehensive test suite

## Installation

This package is part of a UV workspace. Install from the workspace root:

```bash
# Navigate to workspace root
cd /path/to/dmo_app

# Sync all workspace dependencies
uv sync

# The core package will be installed automatically as a workspace member
```

## Requirements

- Python 3.11+
- pydantic >= 2.0
- aiosqlite >= 0.19.0

**Note**: CLI dependencies (typer, rich) are in the separate `cli` package.

## Quick Start

### Command Line Interface

DMO-Core provides a Python API for building applications. For command-line usage, see the separate [CLI package](../cli/README.md) which provides the `dmo` command.

To use the CLI after workspace installation:
```bash
# From workspace root
uv run dmo --help
```

### Python API

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
    dmo = await service.create_dmo(
        DMOCreate(
            name="Morning Routine",
            description="My daily morning ritual",
            timezone="America/New_York"
        )
    )

    # Add activities (reference checklist only)
    from dmo_core import ActivityCreate
    await service.create_activity(
        ActivityCreate(dmo_id=dmo.id, name="Meditate 10 minutes", order=0)
    )
    await service.create_activity(
        ActivityCreate(dmo_id=dmo.id, name="Exercise 30 minutes", order=1)
    )

    # Mark complete for today
    await service.mark_complete(dmo.id, date.today(), "Great day!")

    # Get daily report
    report = await service.get_daily_report(date.today())
    print(f"DMOs for {report.date}:")
    for dmo_status in report.dmos:
        status = "✓" if dmo_status.completed else "✗"
        print(f"  {status} {dmo_status.dmo.name}")
        for activity in dmo_status.activities:
            print(f"    - {activity}")

    # Get monthly report
    reports = await service.get_monthly_report(2026, 1, dmo.id)
    summary = reports[0].summary
    print(f"\nMonthly Summary:")
    print(f"  Completed: {summary.completed_days}/{summary.total_days}")
    print(f"  Rate: {summary.completion_rate:.1%}")
    print(f"  Current Streak: {summary.current_streak} days")
    print(f"  Longest Streak: {summary.longest_streak} days")

    # Cleanup
    await backend.close()

asyncio.run(main())
```

## Architecture

### Core Concepts

1. **DMO (Daily Method of Operation)**: A discipline you want to track daily
2. **Activity**: A reference checklist item (doesn't affect completion)
3. **Completion**: Binary status (completed/not completed) for a DMO on a specific date
4. **Reports**: Daily and monthly views of completion status with streak calculations

### Storage Backends

- **SqliteBackend**: Production-ready SQLite storage with aiosqlite
- **MemoryBackend**: In-memory storage for testing

### Service Layer

The `DmoService` class provides the main API:

- **DMO Operations**: CRUD for DMOs
- **Activity Operations**: CRUD for activities with ordering
- **Completion Tracking**: Mark complete/incomplete with notes
- **Reporting**: Daily reports, monthly summaries, and custom date ranges

## Development

All development commands should be run from the workspace root using `uv run`:

### Running Tests

```bash
# Run all core tests
uv run pytest core/tests

# Run with coverage
uv run pytest core/tests --cov=dmo_core --cov-report=term-missing

# Run specific test file
uv run pytest core/tests/test_service.py -v
```

### Type Checking

```bash
# Check core package
uv run mypy core/src core/tests --strict
```

### Linting

```bash
# Lint core package
uv run ruff check core/src core/tests
```

### Code Formatting

```bash
# Format core package
uv run ruff format core/src core/tests
```

## Project Structure

This package is part of the DMO workspace:

```
dmo_app/                         # Workspace root
├── pyproject.toml              # Workspace configuration
├── core/                       # This package (dmo-core)
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── dmo_core/
│   │       ├── __init__.py     # Public API
│   │       ├── models.py       # Pydantic models
│   │       ├── errors.py       # Custom exceptions
│   │       ├── utils.py        # Utility functions
│   │       ├── service.py      # DmoService class
│   │       └── storage/
│   │           ├── __init__.py
│   │           ├── base.py     # Abstract backend
│   │           ├── sqlite.py   # SQLite backend
│   │           └── memory.py   # In-memory backend
│   └── tests/
│       ├── conftest.py         # Pytest fixtures
│       ├── test_models.py
│       ├── test_utils.py
│       ├── test_storage_sqlite.py
│       ├── test_service.py
│       └── test_integration.py
├── cli/                        # CLI package (dmo-cli)
│   └── ...                     # See cli/README.md
├── api/                        # API package (future)
│   └── ...
└── web/                        # Web interface (future)
    └── ...
```

## API Documentation

### Models

- `DMOCreate`, `DMOUpdate`, `DMORead`: DMO data models
- `ActivityCreate`, `ActivityUpdate`, `ActivityRead`: Activity models
- `DMOCompletionRead`: Completion record
- `DailyReport`, `MonthlyReport`, `DMOSummary`: Report models

### Errors

- `DmoNotFoundError`: DMO not found
- `ActivityNotFoundError`: Activity not found
- `DuplicateNameError`: Duplicate entity name
- `StorageError`: Storage operation failed

## Philosophy

This library embodies a specific philosophy:

> **"Did I complete my DMO today?"** is the only question that matters.

- No partial completion
- No task-level tracking
- No dependency chains
- Just a binary decision: done or not done

Activities serve as a reminder checklist, but completion is a holistic judgment call by the user.

## License

MIT

## Contributing

Contributions are welcome! Please ensure (from workspace root):

1. All tests pass: `uv run pytest core/tests`
2. Type checking passes: `uv run mypy core/src core/tests --strict`
3. Linting passes: `uv run ruff check core/src core/tests`
4. Code coverage stays above 80%

## Version

Current version: 0.1.0
