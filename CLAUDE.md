# CLAUDE.md - DMO Implementation Guide

## Project Overview

You are implementing the **DMO system**, a discipline-tracking application for Daily Methods of Operation. This is organized as a **UV workspace** with multiple packages:

- **`core/`** - `dmo-core`: Python library with core business logic
- **`cli/`** - `dmo-cli`: Command-line interface (depends on `dmo-core`)
- **`api/`** - `dmo-api`: REST API (future)
- **`web/`** - Web interface (future)

This is a **discipline-tracking system, NOT a task manager**.

**The single most important concept**: A DMO is either completed or not completed on any given day. This is a binary, subjective judgment by the user. Activities exist only as a descriptive checklist—they have zero effect on completion logic.

## Specification

The complete implementation specification is in `dmo-core-specification.md`. **Read the entire specification before writing any code.** It contains:
- All Pydantic models with exact field definitions
- Complete storage backend interface
- Full SQLite and Memory implementations
- Service layer with all methods
- Complete test suite
- Every code snippet you need

## Tech Stack

| Component | Choice |
|-----------|--------|
| Package Manager | UV (workspace mode) |
| Python | 3.11+ |
| Validation | Pydantic v2 |
| Async SQLite | aiosqlite |
| CLI Framework | Typer + Rich |
| Testing | pytest + pytest-asyncio |
| Type Checking | mypy (strict mode) |
| Linting | ruff |

## Implementation Order

Follow this sequence exactly:

1. **Workspace Setup**
   ```bash
   # Create workspace root pyproject.toml with workspace members
   # Run from workspace root: uv sync
   ```

2. **Core Package** (`core/`)

   a. **Project Setup**
   ```bash
   mkdir -p core/src/dmo_core/storage core/tests
   ```
   Create `core/pyproject.toml` first.

   b. **Core Layer** (in order)
   - `core/src/dmo_core/errors.py` - Exception classes
   - `core/src/dmo_core/utils.py` - Helper functions
   - `core/src/dmo_core/models.py` - All Pydantic DTOs

   c. **Storage Layer** (in order)
   - `core/src/dmo_core/storage/base.py` - Abstract interface
   - `core/src/dmo_core/storage/memory.py` - In-memory implementation
   - `core/src/dmo_core/storage/sqlite.py` - SQLite implementation
   - `core/src/dmo_core/storage/__init__.py` - Exports

   d. **Service Layer**
   - `core/src/dmo_core/service.py` - Business logic
   - `core/src/dmo_core/__init__.py` - Public API exports

   e. **Tests** (in order)
   - `core/tests/conftest.py` - Fixtures
   - `core/tests/test_utils.py`
   - `core/tests/test_models.py`
   - `core/tests/test_storage_sqlite.py`
   - `core/tests/test_service.py`
   - `core/tests/test_integration.py`

   f. **Documentation**
   - `core/README.md`

3. **CLI Package** (`cli/`)
   - See CLI implementation section below

## Critical Rules

### DO
- Use `async def` for ALL storage and service methods
- Use `UUID` for all IDs (generate with `uuid4()`)
- Use `datetime` with UTC timezone for timestamps
- Use `date` (not datetime) for completion dates
- Implement `set_completion` as an idempotent upsert
- Raise `DmoNotFoundError` before any operation on a DMO
- Return `Sequence[T]` (not `list[T]`) from list methods in the interface
- Strip whitespace from names in Pydantic validators
- Order activities by `order` field, then `created_at`

### DON'T
- Don't track per-activity completion (activities are reference only)
- Don't infer completion status from activities
- Don't use `Optional` for required fields
- Don't return `None` from `get_dmo()` or `get_activity()` - raise exceptions
- Don't forget `await` on async calls
- Don't mutate returned Pydantic models

## Key Design Patterns

### Strategy Pattern (Storage)
```python
class StorageBackend(ABC):
    @abstractmethod
    async def create_dmo(self, data: DMOCreate) -> DMORead: ...

class SqliteBackend(StorageBackend):
    async def create_dmo(self, data: DMOCreate) -> DMORead:
        # Implementation
```

### Upsert for Completions
```python
async def set_completion(self, dmo_id, date, completed, note=None):
    # Check if exists -> UPDATE
    # Else -> INSERT
    # This is idempotent
```

### Three-Model Pattern (Create/Update/Read)
```python
class DMOCreate(BaseModel):  # Input for creation
    name: str
    
class DMOUpdate(BaseModel):  # Partial updates (all optional)
    name: Optional[str] = None
    
class DMORead(BaseModel):    # Output with all fields
    id: UUID
    name: str
    created_at: datetime
```

## Streak Calculation Logic

```python
# Current streak: count backwards from last date until a miss
# Longest streak: max consecutive completed days in range
# Missing record = not completed (breaks streak)
```

## Verification Commands

**IMPORTANT**: All commands must be run from the workspace root using `uv run`.

After implementation, run these in order:

```bash
# Sync workspace dependencies
uv sync

# Type checking (must pass with zero errors)
uv run mypy core/src core/tests --strict

# Linting (must pass)
uv run ruff check core/src core/tests

# Tests with coverage (target: >80%)
uv run pytest core/tests --cov=dmo_core --cov-report=term-missing -v

# Quick smoke test (from workspace root)
uv run python -c "
import asyncio
from dmo_core import DmoService, DMOCreate
from dmo_core.storage import SqliteBackend

async def test():
    backend = SqliteBackend(':memory:')
    await backend.init()
    service = DmoService(backend)
    dmo = await service.create_dmo(DMOCreate(name='Test'))
    print(f'Created: {dmo.name} ({dmo.id})')
    await backend.close()

asyncio.run(test())
"

# Test CLI (if implemented)
uv run dmo --help
```

## Common Pitfalls

### Workspace-Specific
1. **Running commands from wrong directory**: Always run `uv run` from workspace root
2. **Forgetting `uv sync`**: Run after modifying any `pyproject.toml` file
3. **Path confusion**: Use `core/src`, `core/tests`, not `src`, `tests`
4. **Import errors in CLI**: Ensure `[tool.uv.sources]` points to workspace member

### Code-Specific
5. **Forgetting `await`**: Every storage/service call is async
6. **SQLite `order` column**: Must quote as `"order"` (reserved word)
7. **Foreign key enforcement**: Must run `PRAGMA foreign_keys = ON`
8. **Date vs datetime**: Completions use `date`, timestamps use `datetime`
9. **pytest-asyncio config**: Need `asyncio_mode = "auto"` in pyproject.toml
10. **Pydantic v2 syntax**: Use `model_config = ConfigDict(...)` not `class Config`

## File Checklist

When complete, you should have exactly these files:

```
dmo_app/                              # Workspace root
├── pyproject.toml                    # Workspace config (members: core, cli, api)
├── uv.lock                           # Unified lock file
├── CLAUDE.md                         # This file
├── README.md                         # Project overview
├── .venv/                            # Shared virtual environment
│
├── core/                             # dmo-core package
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── dmo_core/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── errors.py
│   │       ├── utils.py
│   │       ├── service.py
│   │       └── storage/
│   │           ├── __init__.py
│   │           ├── base.py
│   │           ├── sqlite.py
│   │           └── memory.py
│   └── tests/
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_storage_sqlite.py
│       ├── test_service.py
│       ├── test_utils.py
│       └── test_integration.py
│
├── cli/                              # dmo-cli package
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/
│   │   └── dmo_cli/
│   │       ├── __init__.py
│   │       └── main.py               # Typer CLI app
│   └── tests/
│       └── test_cli.py
│
├── api/                              # dmo-api package (future)
│   └── ...
│
└── web/                              # Web interface (future)
    └── ...
```

## Success Criteria

### Core Package (`core/`)
The core implementation is complete when:
- [ ] All core files from the checklist exist
- [ ] `uv run mypy core/src core/tests --strict` reports 0 errors
- [ ] `uv run ruff check core/src core/tests` reports 0 errors
- [ ] `uv run pytest core/tests` shows all 56 tests passing
- [ ] Test coverage exceeds 80% (currently at 85%)
- [ ] The smoke test above runs successfully

### CLI Package (`cli/`)
The CLI implementation is complete when:
- [ ] CLI files from the checklist exist
- [ ] `uv run dmo --help` shows help text
- [ ] All CLI commands work correctly
- [ ] CLI tests pass

## CLI Package Implementation

The CLI package (`cli/`) depends on the core package and provides a command-line interface using Typer and Rich.

### CLI Package Structure
```
cli/
├── pyproject.toml          # Dependencies: dmo-core, typer, rich
├── README.md
├── src/
│   └── dmo_cli/
│       ├── __init__.py
│       └── main.py         # Typer app with all commands
└── tests/
    └── test_cli.py
```

### CLI Commands to Implement

The CLI should provide these commands (see `dmo --help`):
- `dmo create` - Create a new DMO with optional activities
- `dmo list` - List all active DMOs
- `dmo show <dmo_id>` - Show DMO details
- `dmo delete <dmo_id>` - Delete a DMO (with confirmation)
- `dmo complete <dmo_id>` - Mark as complete/incomplete
- `dmo today` - Show today's status for all DMOs
- `dmo report` - Generate monthly reports
- `dmo init` - Initialize database
- `dmo reset` - Reset database (with confirmation)

### CLI Configuration

**pyproject.toml** must include:
```toml
[project.scripts]
dmo = "dmo_cli.main:app"

[tool.uv.sources]
dmo-core = { workspace = true }
```

### Database Location

The CLI should use `~/.dmo/dmo.db` as the default database path.

### Running CLI Commands

From workspace root:
```bash
uv run dmo --help
uv run dmo create "Morning Routine" -a "Meditate" -a "Exercise"
uv run dmo list
uv run dmo today
```

## When Stuck

1. Re-read the relevant section in `dmo-core-specification.md`
2. The spec contains complete, copy-paste-ready code for every file
3. If a test fails, check the exact assertion and trace back to the implementation
4. Type errors usually mean a mismatch between models—check Create vs Read vs Update
5. For CLI issues, check that workspace dependencies are synced with `uv sync`

