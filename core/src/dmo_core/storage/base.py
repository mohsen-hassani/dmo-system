"""
Abstract storage backend interface.

This module defines the StorageBackend protocol that all storage
implementations must follow. Uses the Strategy pattern to allow
swapping storage backends without changing business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date

from dmo_core.models import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    DMOCompletionRead,
    DMOCreate,
    DMORead,
    DMOUpdate,
)


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    All methods are async to support both sync (via anyio) and async backends.
    Implementations must handle their own connection management and transactions.
    """

    # =========================================================================
    # Lifecycle
    # =========================================================================

    @abstractmethod
    async def init(self) -> None:
        """
        Initialize the storage backend.

        This should create tables/schema if they don't exist.
        Safe to call multiple times (idempotent).
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """
        Close the storage backend and release resources.

        After calling close(), the backend should not be used.
        """
        ...

    # =========================================================================
    # DMO Operations
    # =========================================================================

    @abstractmethod
    async def create_dmo(self, data: DMOCreate) -> DMORead:
        """
        Create a new DMO.

        Args:
            data: DMO creation data

        Returns:
            The created DMO with generated ID and timestamps

        Raises:
            DuplicateNameError: If a DMO with this name already exists
        """
        ...

    @abstractmethod
    async def get_dmo(self, dmo_id: int) -> DMORead:
        """
        Retrieve a DMO by ID.

        Args:
            dmo_id: The DMO's unique identifier

        Returns:
            The DMO data

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def list_dmos(self, *, include_inactive: bool = False) -> Sequence[DMORead]:
        """
        List all DMOs.

        Args:
            include_inactive: If True, include DMOs where active=False

        Returns:
            Sequence of DMOs, ordered by name ascending
        """
        ...

    @abstractmethod
    async def update_dmo(self, dmo_id: int, data: DMOUpdate) -> DMORead:
        """
        Update an existing DMO.

        Only fields that are not None in data will be updated.

        Args:
            dmo_id: The DMO's unique identifier
            data: Fields to update (None values are ignored)

        Returns:
            The updated DMO

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
            DuplicateNameError: If updating name to one that already exists
        """
        ...

    @abstractmethod
    async def delete_dmo(self, dmo_id: int) -> None:
        """
        Delete a DMO and all associated data.

        This performs a HARD delete of:
        - The DMO itself
        - All Activities belonging to this DMO
        - All DMOCompletion records for this DMO

        Args:
            dmo_id: The DMO's unique identifier

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    # =========================================================================
    # Activity Operations
    # =========================================================================

    @abstractmethod
    async def create_activity(self, data: ActivityCreate) -> ActivityRead:
        """
        Create a new Activity within a DMO.

        Args:
            data: Activity creation data (must include valid dmo_id)

        Returns:
            The created Activity with generated ID and timestamps

        Raises:
            DmoNotFoundError: If the referenced DMO does not exist
        """
        ...

    @abstractmethod
    async def get_activity(self, activity_id: int) -> ActivityRead:
        """
        Retrieve an Activity by ID.

        Args:
            activity_id: The Activity's unique identifier

        Returns:
            The Activity data

        Raises:
            ActivityNotFoundError: If no Activity exists with this ID
        """
        ...

    @abstractmethod
    async def list_activities(self, dmo_id: int) -> Sequence[ActivityRead]:
        """
        List all Activities for a DMO.

        Args:
            dmo_id: The DMO's unique identifier

        Returns:
            Sequence of Activities, ordered by 'order' field ascending

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def update_activity(
        self, activity_id: int, data: ActivityUpdate
    ) -> ActivityRead:
        """
        Update an existing Activity.

        Only fields that are not None in data will be updated.

        Args:
            activity_id: The Activity's unique identifier
            data: Fields to update (None values are ignored)

        Returns:
            The updated Activity

        Raises:
            ActivityNotFoundError: If no Activity exists with this ID
        """
        ...

    @abstractmethod
    async def delete_activity(self, activity_id: int) -> None:
        """
        Delete an Activity.

        Args:
            activity_id: The Activity's unique identifier

        Raises:
            ActivityNotFoundError: If no Activity exists with this ID
        """
        ...

    # =========================================================================
    # DMOCompletion Operations
    # =========================================================================

    @abstractmethod
    async def set_completion(
        self,
        dmo_id: int,
        completion_date: date,
        completed: bool,
        note: str | None = None,
    ) -> DMOCompletionRead:
        """
        Set the completion status for a DMO on a specific date.

        This is an UPSERT operation:
        - If no record exists for (dmo_id, date): creates one
        - If a record exists: updates it

        This operation is idempotent.

        Args:
            dmo_id: The DMO's unique identifier
            completion_date: The date (user's local date)
            completed: Whether the DMO was completed
            note: Optional note about the completion

        Returns:
            The created or updated completion record

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def get_completion(
        self, dmo_id: int, completion_date: date
    ) -> DMOCompletionRead | None:
        """
        Get the completion record for a DMO on a specific date.

        Args:
            dmo_id: The DMO's unique identifier
            completion_date: The date to query

        Returns:
            The completion record, or None if no record exists

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
        """
        ...

    @abstractmethod
    async def list_completions(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> Sequence[DMOCompletionRead]:
        """
        List all completion records for a DMO within a date range.

        Args:
            dmo_id: The DMO's unique identifier
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            Sequence of completion records, ordered by date ascending

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
            ValueError: If start > end
        """
        ...

    @abstractmethod
    async def count_completed_days(
        self,
        dmo_id: int,
        start: date,
        end: date,
    ) -> int:
        """
        Count the number of completed days for a DMO in a date range.

        This is an optimization to avoid fetching all records when only
        the count is needed.

        Args:
            dmo_id: The DMO's unique identifier
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            Number of days where completed=True

        Raises:
            DmoNotFoundError: If no DMO exists with this ID
            ValueError: If start > end
        """
        ...
