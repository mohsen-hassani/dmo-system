"""
DMO endpoints for the FastAPI application.

Provides CRUD operations for Daily Methods of Operation.
"""

from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from dmo_api.dependencies import ServiceDep
from dmo_core.models import DMOCreate, DMORead, DMOUpdate

router = APIRouter(prefix="/dmos", tags=["DMOs"])


@router.get("", response_model=list[DMORead])
async def list_dmos(
    service: ServiceDep,
    include_inactive: Annotated[
        bool, Query(description="Include inactive DMOs in the list")
    ] = False,
) -> list[DMORead]:
    """
    List all DMOs.

    Args:
        include_inactive: If True, include inactive DMOs. Defaults to False (active only).

    Returns:
        List of DMO objects
    """
    dmos = await service.list_dmos(include_inactive=include_inactive)
    return list(dmos)


@router.post("", response_model=DMORead, status_code=status.HTTP_201_CREATED)
async def create_dmo(
    service: ServiceDep,
    dmo_data: DMOCreate,
) -> DMORead:
    """
    Create a new DMO.

    Args:
        dmo_data: DMO creation data (name, description, timezone)

    Returns:
        The created DMO object
    """
    return await service.create_dmo(dmo_data)


@router.get("/{dmo_id}", response_model=DMORead)
async def get_dmo(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
) -> DMORead:
    """
    Get a specific DMO by ID.

    Args:
        dmo_id: The DMO's ID

    Returns:
        The DMO object

    Raises:
        404: If DMO not found
    """
    return await service.get_dmo(dmo_id)


@router.patch("/{dmo_id}", response_model=DMORead)
async def update_dmo(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    dmo_data: DMOUpdate,
) -> DMORead:
    """
    Update a DMO.

    Args:
        dmo_id: The DMO's ID
        dmo_data: Fields to update (all optional)

    Returns:
        The updated DMO object

    Raises:
        404: If DMO not found
    """
    return await service.update_dmo(dmo_id, dmo_data)


@router.delete("/{dmo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dmo(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
) -> None:
    """
    Delete a DMO and all associated data.

    This permanently deletes the DMO, all its activities, and all completion records.

    Args:
        dmo_id: The DMO's ID

    Raises:
        404: If DMO not found
    """
    await service.delete_dmo(dmo_id)


@router.post("/{dmo_id}/deactivate", response_model=DMORead)
async def deactivate_dmo(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
) -> DMORead:
    """
    Deactivate a DMO (soft delete).

    Sets the DMO's active flag to False. The DMO will be hidden from default listings
    but can be reactivated later.

    Args:
        dmo_id: The DMO's ID

    Returns:
        The updated DMO object

    Raises:
        404: If DMO not found
    """
    return await service.deactivate_dmo(dmo_id)


@router.post("/{dmo_id}/activate", response_model=DMORead)
async def activate_dmo(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
) -> DMORead:
    """
    Activate a previously deactivated DMO.

    Sets the DMO's active flag to True.

    Args:
        dmo_id: The DMO's ID

    Returns:
        The updated DMO object

    Raises:
        404: If DMO not found
    """
    return await service.activate_dmo(dmo_id)
