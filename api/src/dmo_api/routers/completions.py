"""
Completion endpoints for the FastAPI application.

Provides operations for tracking DMO completion status.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, status

from dmo_api.dependencies import ServiceDep
from dmo_core.models import DMOCompletionCreate, DMOCompletionRead

router = APIRouter(prefix="/completions", tags=["Completions"])


@router.post("", response_model=DMOCompletionRead, status_code=status.HTTP_201_CREATED)
async def set_completion(
    service: ServiceDep,
    completion_data: DMOCompletionCreate,
) -> DMOCompletionRead:
    """
    Set the completion status for a DMO on a specific date.

    This operation is idempotent - calling it multiple times with the same
    parameters will produce the same result.

    Args:
        completion_data: Completion data (dmo_id, date, completed, note)

    Returns:
        The completion record

    Raises:
        404: If DMO not found
    """
    return await service.set_dmo_completion(
        dmo_id=completion_data.dmo_id,
        completion_date=completion_data.date,
        completed=completion_data.completed,
        note=completion_data.note,
    )


@router.get("/{dmo_id}/{date}", response_model=DMOCompletionRead | None)
async def get_completion(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    completion_date: Annotated[date, Path(alias="date", description="Completion date (YYYY-MM-DD)")],
) -> DMOCompletionRead | None:
    """
    Get the completion record for a DMO on a specific date.

    Args:
        dmo_id: The DMO's ID
        completion_date: The date to check

    Returns:
        The completion record if it exists, None otherwise

    Raises:
        404: If DMO not found
    """
    # First verify the DMO exists
    await service.get_dmo(dmo_id)
    return await service.get_completion(dmo_id, completion_date)


@router.post("/{dmo_id}/mark-complete", response_model=DMOCompletionRead)
async def mark_complete(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    completion_date: Annotated[
        date, Body(embed=True, description="Date to mark complete (YYYY-MM-DD)")
    ],
    note: Annotated[str | None, Body(embed=True, description="Optional note")] = None,
) -> DMOCompletionRead:
    """
    Convenience endpoint to mark a DMO as complete.

    Args:
        dmo_id: The DMO's ID
        completion_date: The date to mark complete
        note: Optional note about the completion

    Returns:
        The completion record

    Raises:
        404: If DMO not found
    """
    return await service.mark_complete(dmo_id, completion_date, note)


@router.post("/{dmo_id}/mark-incomplete", response_model=DMOCompletionRead)
async def mark_incomplete(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    completion_date: Annotated[
        date, Body(embed=True, description="Date to mark incomplete (YYYY-MM-DD)")
    ],
    note: Annotated[str | None, Body(embed=True, description="Optional note")] = None,
) -> DMOCompletionRead:
    """
    Convenience endpoint to mark a DMO as incomplete.

    Args:
        dmo_id: The DMO's ID
        completion_date: The date to mark incomplete
        note: Optional note

    Returns:
        The completion record

    Raises:
        404: If DMO not found
    """
    return await service.mark_incomplete(dmo_id, completion_date, note)


@router.get("/{dmo_id}/list", response_model=list[DMOCompletionRead])
async def list_completions(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    start_date: Annotated[date, Query(description="Start date (inclusive, YYYY-MM-DD)")],
    end_date: Annotated[date, Query(description="End date (inclusive, YYYY-MM-DD)")],
) -> list[DMOCompletionRead]:
    """
    List all completion records for a DMO within a date range.

    Args:
        dmo_id: The DMO's ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        List of completion records

    Raises:
        404: If DMO not found
    """
    # First verify the DMO exists
    await service.get_dmo(dmo_id)
    completions = await service._storage.list_completions(dmo_id, start_date, end_date)
    return list(completions)
