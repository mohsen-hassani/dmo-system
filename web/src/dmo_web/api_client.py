"""
API client for communicating with the DMO FastAPI backend.

Provides simple wrapper functions for all API endpoints.
"""

import os
from datetime import date
from typing import Any

import httpx

# API base URL (configurable via environment variable)
API_BASE_URL = os.getenv("DMO_API_URL", "http://localhost:8080")


class APIError(Exception):
    """Raised when an API call fails."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


def _make_request(
    method: str,
    endpoint: str,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Make an HTTP request to the API.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        endpoint: API endpoint path
        json: JSON body for POST/PATCH requests
        params: Query parameters

    Returns:
        Response data (dict or list)

    Raises:
        APIError: If the request fails
    """
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = httpx.request(
            method=method,
            url=url,
            json=json,
            params=params,
            timeout=10.0,
        )

        if response.status_code == 204:
            return None

        if response.status_code >= 400:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", response.text or "Unknown error")
            raise APIError(response.status_code, error_message)

        return response.json()

    except httpx.RequestError as e:
        raise APIError(0, f"Connection error: {e}")


# =============================================================================
# DMO Operations
# =============================================================================


def list_dmos(include_inactive: bool = False) -> list[dict[str, Any]]:
    """List all DMOs."""
    return _make_request("GET", "/dmos", params={"include_inactive": include_inactive})


def get_dmo(dmo_id: int) -> dict[str, Any]:
    """Get a specific DMO by ID."""
    return _make_request("GET", f"/dmos/{dmo_id}")


def create_dmo(name: str, description: str | None = None) -> dict[str, Any]:
    """Create a new DMO."""
    data = {"name": name}
    if description:
        data["description"] = description
    return _make_request("POST", "/dmos", json=data)


def update_dmo(
    dmo_id: int,
    name: str | None = None,
    description: str | None = None,
    active: bool | None = None,
) -> dict[str, Any]:
    """Update a DMO."""
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if active is not None:
        data["active"] = active
    return _make_request("PATCH", f"/dmos/{dmo_id}", json=data)


def delete_dmo(dmo_id: int) -> None:
    """Delete a DMO."""
    _make_request("DELETE", f"/dmos/{dmo_id}")


def deactivate_dmo(dmo_id: int) -> dict[str, Any]:
    """Deactivate a DMO."""
    return _make_request("POST", f"/dmos/{dmo_id}/deactivate")


def activate_dmo(dmo_id: int) -> dict[str, Any]:
    """Activate a DMO."""
    return _make_request("POST", f"/dmos/{dmo_id}/activate")


# =============================================================================
# Activity Operations
# =============================================================================


def list_activities(dmo_id: int) -> list[dict[str, Any]]:
    """List all activities for a DMO."""
    return _make_request("GET", f"/activities/dmo/{dmo_id}")


def create_activity(dmo_id: int, name: str, order: int = 0) -> dict[str, Any]:
    """Create a new activity."""
    data = {"dmo_id": dmo_id, "name": name, "order": order}
    return _make_request("POST", "/activities", json=data)


def update_activity(activity_id: int, name: str | None = None, order: int | None = None) -> dict[str, Any]:
    """Update an activity."""
    data = {}
    if name is not None:
        data["name"] = name
    if order is not None:
        data["order"] = order
    return _make_request("PATCH", f"/activities/{activity_id}", json=data)


def delete_activity(activity_id: int) -> None:
    """Delete an activity."""
    _make_request("DELETE", f"/activities/{activity_id}")


# =============================================================================
# Completion Operations
# =============================================================================


def set_completion(
    dmo_id: int, completion_date: date, completed: bool, note: str | None = None
) -> dict[str, Any]:
    """Set completion status for a DMO on a specific date."""
    data = {
        "dmo_id": dmo_id,
        "date": completion_date.isoformat(),
        "completed": completed,
    }
    if note:
        data["note"] = note
    return _make_request("POST", "/completions", json=data)


def mark_complete(dmo_id: int, completion_date: date, note: str | None = None) -> dict[str, Any]:
    """Mark a DMO as complete for a specific date."""
    data = {"completion_date": completion_date.isoformat()}
    if note:
        data["note"] = note
    return _make_request("POST", f"/completions/{dmo_id}/mark-complete", json=data)


def mark_incomplete(dmo_id: int, completion_date: date) -> dict[str, Any]:
    """Mark a DMO as incomplete for a specific date."""
    data = {"completion_date": completion_date.isoformat()}
    return _make_request("POST", f"/completions/{dmo_id}/mark-incomplete", json=data)


# =============================================================================
# Report Operations
# =============================================================================


def get_today_report() -> dict[str, Any]:
    """Get today's status for all active DMOs."""
    return _make_request("GET", "/reports/today")


def get_daily_report(report_date: date) -> dict[str, Any]:
    """Get a daily report for a specific date."""
    return _make_request("GET", f"/reports/daily/{report_date.isoformat()}")


def get_monthly_report(year: int | None = None, month: int | None = None, dmo_id: int | None = None) -> list[dict[str, Any]]:
    """Get monthly report."""
    if year and month:
        params = {}
        if dmo_id:
            params["dmo_id"] = dmo_id
        return _make_request("GET", f"/reports/monthly/{year}/{month}", params=params)
    else:
        return _make_request("GET", "/reports/monthly")


def get_dmo_summary(
    dmo_id: int, start_date: date, end_date: date
) -> dict[str, Any]:
    """Get a DMO summary for a date range."""
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    return _make_request("GET", f"/reports/summary/{dmo_id}", params=params)
