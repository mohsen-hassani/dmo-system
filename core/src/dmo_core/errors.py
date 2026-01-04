"""
Custom exceptions for the DMO-Core system.

Exception hierarchy:
    DmoError (base)
    ├── NotFoundError
    │   ├── DmoNotFoundError
    │   ├── ActivityNotFoundError
    │   └── CompletionNotFoundError
    ├── ValidationError
    │   └── DuplicateNameError
    └── StorageError
"""

from __future__ import annotations


class DmoError(Exception):
    """Base exception for all DMO-Core errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(DmoError):
    """Base class for "entity not found" errors."""

    pass


class DmoNotFoundError(NotFoundError):
    """Raised when a DMO with the specified ID does not exist."""

    def __init__(self, dmo_id: int) -> None:
        super().__init__(
            message=f"DMO not found: {dmo_id}",
            detail=f"No DMO exists with ID '{dmo_id}'"
        )
        self.dmo_id = dmo_id


class ActivityNotFoundError(NotFoundError):
    """Raised when an Activity with the specified ID does not exist."""

    def __init__(self, activity_id: int) -> None:
        super().__init__(
            message=f"Activity not found: {activity_id}",
            detail=f"No Activity exists with ID '{activity_id}'"
        )
        self.activity_id = activity_id


class CompletionNotFoundError(NotFoundError):
    """Raised when a DMOCompletion record is not found."""

    def __init__(self, dmo_id: int, date: str) -> None:
        super().__init__(
            message=f"Completion not found for DMO {dmo_id} on {date}",
            detail=f"No completion record exists for DMO '{dmo_id}' on date '{date}'"
        )
        self.dmo_id = dmo_id
        self.date = date


class ValidationError(DmoError):
    """Base class for validation-related errors."""

    pass


class DuplicateNameError(ValidationError):
    """Raised when attempting to create/update an entity with a duplicate name."""

    def __init__(self, entity_type: str, name: str) -> None:
        super().__init__(
            message=f"Duplicate {entity_type} name: '{name}'",
            detail=f"A {entity_type} with name '{name}' already exists"
        )
        self.entity_type = entity_type
        self.name = name


class StorageError(DmoError):
    """Raised when a storage operation fails unexpectedly."""

    def __init__(self, operation: str, detail: str | None = None) -> None:
        super().__init__(
            message=f"Storage operation failed: {operation}",
            detail=detail
        )
        self.operation = operation
