"""
Activity endpoints for the FastAPI application.

Provides CRUD operations for Activities within DMOs.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Path, status

from dmo_api.dependencies import ServiceDep
from dmo_core.models import ActivityCreate, ActivityRead, ActivityUpdate

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get("/dmo/{dmo_id}", response_model=list[ActivityRead])
async def list_activities(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
) -> list[ActivityRead]:
    """
    List all activities for a DMO.

    Activities are returned ordered by their 'order' field, then by creation date.

    Args:
        dmo_id: The DMO's ID

    Returns:
        List of Activity objects

    Raises:
        404: If DMO not found
    """
    activities = await service.list_activities(dmo_id)
    return list(activities)


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_activity(
    service: ServiceDep,
    activity_data: ActivityCreate,
) -> ActivityRead:
    """
    Create a new activity within a DMO.

    Args:
        activity_data: Activity creation data (dmo_id, name, order)

    Returns:
        The created Activity object

    Raises:
        404: If DMO not found
    """
    return await service.create_activity(activity_data)


@router.get("/{activity_id}", response_model=ActivityRead)
async def get_activity(
    service: ServiceDep,
    activity_id: Annotated[int, Path(description="Activity ID", gt=0)],
) -> ActivityRead:
    """
    Get a specific activity by ID.

    Args:
        activity_id: The Activity's ID

    Returns:
        The Activity object

    Raises:
        404: If Activity not found
    """
    return await service.get_activity(activity_id)


@router.patch("/{activity_id}", response_model=ActivityRead)
async def update_activity(
    service: ServiceDep,
    activity_id: Annotated[int, Path(description="Activity ID", gt=0)],
    activity_data: ActivityUpdate,
) -> ActivityRead:
    """
    Update an activity.

    Args:
        activity_id: The Activity's ID
        activity_data: Fields to update (all optional)

    Returns:
        The updated Activity object

    Raises:
        404: If Activity not found
    """
    return await service.update_activity(activity_id, activity_data)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    service: ServiceDep,
    activity_id: Annotated[int, Path(description="Activity ID", gt=0)],
) -> None:
    """
    Delete an activity.

    Args:
        activity_id: The Activity's ID

    Raises:
        404: If Activity not found
    """
    await service.delete_activity(activity_id)


@router.post("/dmo/{dmo_id}/reorder", response_model=list[ActivityRead])
async def reorder_activities(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    activity_ids: Annotated[
        list[int],
        Body(description="Activity IDs in the desired order", min_length=1),
    ],
) -> list[ActivityRead]:
    """
    Reorder activities within a DMO.

    Sets the 'order' field based on the position in the activity_ids list.

    Args:
        dmo_id: The DMO's ID
        activity_ids: Activity IDs in the desired order

    Returns:
        Updated activities in their new order

    Raises:
        404: If DMO or any Activity not found
    """
    activities = await service.reorder_activities(dmo_id, activity_ids)
    return list(activities)
