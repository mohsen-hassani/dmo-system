# DMO API

FastAPI REST API for the Daily Methods of Operation (DMO) tracking system.

## Overview

This package provides a REST API that exposes all DMO-Core functionality as HTTP endpoints. It's built with FastAPI and uses the same SQLite database as the CLI.

## Installation

From the workspace root:

```bash
# Install all workspace dependencies
uv sync

# Or install with dev dependencies
uv sync --extra dev
```

## Running the API

### Development Server

From the workspace root:

```bash
# Run with uvicorn (auto-reload enabled)
uv run uvicorn dmo_api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

### Production Server

```bash
uv run uvicorn dmo_api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Root & Health

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### DMOs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dmos` | List all DMOs (query: `include_inactive`) |
| `POST` | `/dmos` | Create a new DMO |
| `GET` | `/dmos/{dmo_id}` | Get a specific DMO |
| `PATCH` | `/dmos/{dmo_id}` | Update a DMO |
| `DELETE` | `/dmos/{dmo_id}` | Delete a DMO |
| `POST` | `/dmos/{dmo_id}/activate` | Activate a DMO |
| `POST` | `/dmos/{dmo_id}/deactivate` | Deactivate a DMO |

### Activities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/activities/dmo/{dmo_id}` | List activities for a DMO |
| `POST` | `/activities` | Create a new activity |
| `GET` | `/activities/{activity_id}` | Get a specific activity |
| `PATCH` | `/activities/{activity_id}` | Update an activity |
| `DELETE` | `/activities/{activity_id}` | Delete an activity |
| `POST` | `/activities/dmo/{dmo_id}/reorder` | Reorder activities |

### Completions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/completions` | Set completion status |
| `GET` | `/completions/{dmo_id}/{date}` | Get completion for a date |
| `POST` | `/completions/{dmo_id}/mark-complete` | Mark as complete |
| `POST` | `/completions/{dmo_id}/mark-incomplete` | Mark as incomplete |
| `GET` | `/completions/{dmo_id}/list` | List completions (query: `start_date`, `end_date`) |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/reports/today` | Today's report for all active DMOs |
| `GET` | `/reports/daily/{date}` | Daily report for a specific date |
| `GET` | `/reports/monthly` | This month's report for all active DMOs |
| `GET` | `/reports/monthly/{year}/{month}` | Monthly report (query: `dmo_id`) |
| `GET` | `/reports/summary/{dmo_id}` | Custom summary (query: `start_date`, `end_date`) |

## Usage Examples

### Create a DMO

```bash
curl -X POST "http://localhost:8000/dmos" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Routine",
    "description": "Daily morning habits",
    "timezone": "UTC"
  }'
```

Response:
```json
{
  "id": 1,
  "name": "Morning Routine",
  "description": "Daily morning habits",
  "active": true,
  "timezone": "UTC",
  "created_at": "2026-01-03T10:00:00Z",
  "updated_at": "2026-01-03T10:00:00Z"
}
```

### List DMOs

```bash
# Get all active DMOs
curl "http://localhost:8000/dmos"

# Include inactive DMOs
curl "http://localhost:8000/dmos?include_inactive=true"
```

### Get a Specific DMO

```bash
curl "http://localhost:8000/dmos/1"
```

### Update a DMO

```bash
curl -X PATCH "http://localhost:8000/dmos/1" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated morning routine"
  }'
```

### Delete a DMO

```bash
curl -X DELETE "http://localhost:8000/dmos/1"
```

### Create Activities

```bash
curl -X POST "http://localhost:8000/activities" \
  -H "Content-Type: application/json" \
  -d '{
    "dmo_id": 1,
    "name": "Meditation",
    "order": 0
  }'

curl -X POST "http://localhost:8000/activities" \
  -H "Content-Type: application/json" \
  -d '{
    "dmo_id": 1,
    "name": "Exercise",
    "order": 1
  }'
```

### List Activities

```bash
curl "http://localhost:8000/activities/dmo/1"
```

### Reorder Activities

```bash
curl -X POST "http://localhost:8000/activities/dmo/1/reorder" \
  -H "Content-Type: application/json" \
  -d '[2, 1]'  # Activity IDs in new order
```

### Mark DMO as Complete

```bash
# Using the set_completion endpoint
curl -X POST "http://localhost:8000/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "dmo_id": 1,
    "date": "2026-01-03",
    "completed": true,
    "note": "Great session!"
  }'

# Using the convenience endpoint
curl -X POST "http://localhost:8000/completions/1/mark-complete" \
  -H "Content-Type: application/json" \
  -d '{
    "completion_date": "2026-01-03",
    "note": "Great session!"
  }'
```

### Get Completion Status

```bash
curl "http://localhost:8000/completions/1/2026-01-03"
```

### List Completions for a Date Range

```bash
curl "http://localhost:8000/completions/1/list?start_date=2026-01-01&end_date=2026-01-31"
```

### Get Today's Report

```bash
curl "http://localhost:8000/reports/today"
```

Response:
```json
{
  "date": "2026-01-03",
  "dmos": [
    {
      "dmo": {
        "id": 1,
        "name": "Morning Routine",
        "description": "Daily morning habits",
        "active": true,
        "timezone": "UTC",
        "created_at": "2026-01-03T10:00:00Z",
        "updated_at": "2026-01-03T10:00:00Z"
      },
      "completed": true,
      "note": "Great session!",
      "activities": ["Meditation", "Exercise"]
    }
  ]
}
```

### Get Monthly Report

```bash
# This month for all active DMOs
curl "http://localhost:8000/reports/monthly"

# Specific month for all active DMOs
curl "http://localhost:8000/reports/monthly/2026/1"

# Specific month for a specific DMO
curl "http://localhost:8000/reports/monthly/2026/1?dmo_id=1"
```

### Get Custom Summary

```bash
curl "http://localhost:8000/reports/summary/1?start_date=2026-01-01&end_date=2026-01-31"
```

Response:
```json
{
  "dmo": {...},
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "total_days": 31,
  "completed_days": 25,
  "completion_rate": 0.806,
  "current_streak": 5,
  "longest_streak": 10
}
```

## Error Responses

The API returns standardized error responses:

```json
{
  "error": "DMO not found: 999",
  "detail": "No DMO exists with ID '999'"
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

## Testing

Run tests from the workspace root:

```bash
# Run all API tests
uv run pytest api/tests -v

# Run with coverage
uv run pytest api/tests --cov=dmo_api --cov-report=term-missing

# Run specific test file
uv run pytest api/tests/test_api.py -v
```

## Development

### Type Checking

```bash
uv run mypy api/src --strict
```

### Linting

```bash
uv run ruff check api/src api/tests
```

### Auto-formatting

```bash
uv run ruff format api/src api/tests
```

## Database

The API uses the same SQLite database as the CLI, located at `~/.dmo/dmo.db`.

To reset the database:

```bash
rm ~/.dmo/dmo.db
```

The database will be automatically recreated on the next API request.

## Architecture

```
api/
├── src/
│   └── dmo_api/
│       ├── __init__.py          # Package exports
│       ├── main.py              # FastAPI app setup
│       ├── dependencies.py      # Dependency injection
│       ├── exceptions.py        # Exception handlers
│       └── routers/
│           ├── __init__.py
│           ├── dmos.py          # DMO endpoints
│           ├── activities.py    # Activity endpoints
│           ├── completions.py   # Completion endpoints
│           └── reports.py       # Report endpoints
└── tests/
    └── test_api.py              # API tests
```

## License

Same as DMO-Core
