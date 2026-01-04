"""
Tests for the DMO API endpoints.

Uses httpx TestClient to test FastAPI endpoints without running a server.
"""

from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dmo_api import exceptions, routers
from dmo_api.dependencies import get_service
from dmo_core import DmoService
from dmo_core.errors import (
    ActivityNotFoundError,
    DmoError,
    DmoNotFoundError,
    DuplicateNameError,
    StorageError,
    ValidationError,
)
from dmo_core.storage.memory import MemoryBackend


@pytest.fixture
async def memory_service() -> DmoService:
    """Create a DmoService with in-memory storage for testing."""
    backend = MemoryBackend()
    await backend.init()
    return DmoService(backend)


@pytest.fixture
def test_app(memory_service: DmoService) -> FastAPI:
    """Create a test FastAPI app with in-memory database."""
    app = FastAPI()

    # Override the get_service dependency
    async def override_get_service():
        yield memory_service

    app.dependency_overrides[get_service] = override_get_service

    # Register exception handlers
    app.add_exception_handler(DmoNotFoundError, exceptions.dmo_not_found_handler)
    app.add_exception_handler(ActivityNotFoundError, exceptions.activity_not_found_handler)
    app.add_exception_handler(DuplicateNameError, exceptions.duplicate_name_handler)
    app.add_exception_handler(ValidationError, exceptions.validation_error_handler)
    app.add_exception_handler(StorageError, exceptions.storage_error_handler)
    app.add_exception_handler(DmoError, exceptions.dmo_error_handler)

    # Include routers
    app.include_router(routers.dmos.router)
    app.include_router(routers.activities.router)
    app.include_router(routers.completions.router)
    app.include_router(routers.reports.router)

    # Add root endpoints
    @app.get("/")
    async def root():
        return {"message": "Test API"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client for the test app."""
    return TestClient(test_app)


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_and_get_dmo(client: TestClient) -> None:
    """Test creating and retrieving a DMO."""
    # Create a DMO
    create_response = client.post(
        "/dmos",
        json={
            "name": "Test DMO",
            "description": "A test DMO",
            "timezone": "UTC",
        },
    )
    assert create_response.status_code == 201
    dmo_data = create_response.json()
    assert dmo_data["name"] == "Test DMO"
    assert dmo_data["description"] == "A test DMO"
    assert dmo_data["active"] is True
    assert "id" in dmo_data

    dmo_id = dmo_data["id"]

    # Get the DMO
    get_response = client.get(f"/dmos/{dmo_id}")
    assert get_response.status_code == 200
    retrieved_dmo = get_response.json()
    assert retrieved_dmo["id"] == dmo_id
    assert retrieved_dmo["name"] == "Test DMO"


def test_list_dmos(client: TestClient) -> None:
    """Test listing DMOs."""
    response = client.get("/dmos")
    assert response.status_code == 200
    dmos = response.json()
    assert isinstance(dmos, list)


def test_update_dmo(client: TestClient) -> None:
    """Test updating a DMO."""
    # Create a DMO first
    create_response = client.post(
        "/dmos",
        json={"name": "Original Name"},
    )
    dmo_id = create_response.json()["id"]

    # Update it
    update_response = client.patch(
        f"/dmos/{dmo_id}",
        json={"name": "Updated Name", "description": "New description"},
    )
    assert update_response.status_code == 200
    updated_dmo = update_response.json()
    assert updated_dmo["name"] == "Updated Name"
    assert updated_dmo["description"] == "New description"


def test_deactivate_and_activate_dmo(client: TestClient) -> None:
    """Test deactivating and activating a DMO."""
    # Create a DMO
    create_response = client.post("/dmos", json={"name": "Test DMO"})
    dmo_id = create_response.json()["id"]

    # Deactivate it
    deactivate_response = client.post(f"/dmos/{dmo_id}/deactivate")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["active"] is False

    # Activate it
    activate_response = client.post(f"/dmos/{dmo_id}/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["active"] is True


def test_delete_dmo(client: TestClient) -> None:
    """Test deleting a DMO."""
    # Create a DMO
    create_response = client.post("/dmos", json={"name": "To Delete"})
    dmo_id = create_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/dmos/{dmo_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/dmos/{dmo_id}")
    assert get_response.status_code == 404


def test_create_and_list_activities(client: TestClient) -> None:
    """Test creating and listing activities."""
    # Create a DMO first
    dmo_response = client.post("/dmos", json={"name": "Test DMO"})
    dmo_id = dmo_response.json()["id"]

    # Create activities
    activity1_response = client.post(
        "/activities",
        json={"dmo_id": dmo_id, "name": "Activity 1", "order": 0},
    )
    assert activity1_response.status_code == 201

    activity2_response = client.post(
        "/activities",
        json={"dmo_id": dmo_id, "name": "Activity 2", "order": 1},
    )
    assert activity2_response.status_code == 201

    # List activities
    list_response = client.get(f"/activities/dmo/{dmo_id}")
    assert list_response.status_code == 200
    activities = list_response.json()
    assert len(activities) == 2
    assert activities[0]["name"] == "Activity 1"
    assert activities[1]["name"] == "Activity 2"


def test_update_and_delete_activity(client: TestClient) -> None:
    """Test updating and deleting an activity."""
    # Create DMO and activity
    dmo_response = client.post("/dmos", json={"name": "Test DMO"})
    dmo_id = dmo_response.json()["id"]

    activity_response = client.post(
        "/activities",
        json={"dmo_id": dmo_id, "name": "Original Activity"},
    )
    activity_id = activity_response.json()["id"]

    # Update activity
    update_response = client.patch(
        f"/activities/{activity_id}",
        json={"name": "Updated Activity"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Activity"

    # Delete activity
    delete_response = client.delete(f"/activities/{activity_id}")
    assert delete_response.status_code == 204


def test_set_and_get_completion(client: TestClient) -> None:
    """Test setting and getting completion status."""
    # Create a DMO
    dmo_response = client.post("/dmos", json={"name": "Test DMO"})
    dmo_id = dmo_response.json()["id"]

    today = date.today()

    # Set completion
    completion_response = client.post(
        "/completions",
        json={
            "dmo_id": dmo_id,
            "date": today.isoformat(),
            "completed": True,
            "note": "Great job!",
        },
    )
    assert completion_response.status_code == 201
    completion_data = completion_response.json()
    assert completion_data["completed"] is True
    assert completion_data["note"] == "Great job!"

    # Get completion
    get_response = client.get(f"/completions/{dmo_id}/{today.isoformat()}")
    assert get_response.status_code == 200
    retrieved_completion = get_response.json()
    assert retrieved_completion["completed"] is True


def test_mark_complete_and_incomplete(client: TestClient) -> None:
    """Test convenience endpoints for marking complete/incomplete."""
    # Create a DMO
    dmo_response = client.post("/dmos", json={"name": "Test DMO"})
    dmo_id = dmo_response.json()["id"]

    today = date.today()

    # Mark complete
    complete_response = client.post(
        f"/completions/{dmo_id}/mark-complete",
        json={"completion_date": today.isoformat(), "note": "Done!"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["completed"] is True

    # Mark incomplete
    incomplete_response = client.post(
        f"/completions/{dmo_id}/mark-incomplete",
        json={"completion_date": today.isoformat()},
    )
    assert incomplete_response.status_code == 200
    assert incomplete_response.json()["completed"] is False


def test_today_report(client: TestClient) -> None:
    """Test getting today's report."""
    response = client.get("/reports/today")
    assert response.status_code == 200
    report = response.json()
    assert "date" in report
    assert "dmos" in report
    assert isinstance(report["dmos"], list)


def test_monthly_report(client: TestClient) -> None:
    """Test getting monthly reports."""
    # Get this month's report
    response = client.get("/reports/monthly")
    assert response.status_code == 200
    reports = response.json()
    assert isinstance(reports, list)

    # Get specific month
    response = client.get("/reports/monthly/2026/1")
    assert response.status_code == 200


def test_dmo_summary(client: TestClient) -> None:
    """Test getting a DMO summary."""
    # Create a DMO
    dmo_response = client.post("/dmos", json={"name": "Test DMO"})
    dmo_id = dmo_response.json()["id"]

    # Get summary
    response = client.get(
        f"/reports/summary/{dmo_id}",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )
    assert response.status_code == 200
    summary = response.json()
    assert "total_days" in summary
    assert "completed_days" in summary
    assert "completion_rate" in summary
    assert "current_streak" in summary
    assert "longest_streak" in summary


def test_dmo_not_found(client: TestClient) -> None:
    """Test 404 error for non-existent DMO."""
    response = client.get("/dmos/99999")
    assert response.status_code == 404
    error = response.json()
    assert "error" in error
    assert "DMO not found" in error["error"]
