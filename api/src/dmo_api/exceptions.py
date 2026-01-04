"""
Exception handlers for FastAPI application.

Maps DMO-Core exceptions to appropriate HTTP responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from dmo_core.errors import (
    ActivityNotFoundError,
    DmoError,
    DmoNotFoundError,
    DuplicateNameError,
    NotFoundError,
    StorageError,
    ValidationError,
)


async def dmo_error_handler(request: Request, exc: DmoError) -> JSONResponse:
    """
    Generic handler for all DmoError exceptions.

    Maps specific error types to appropriate HTTP status codes.
    """
    # Map error types to HTTP status codes
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, StorageError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
        },
    )


async def dmo_not_found_handler(
    request: Request, exc: DmoNotFoundError
) -> JSONResponse:
    """Handler for DmoNotFoundError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "dmo_id": exc.dmo_id,
        },
    )


async def activity_not_found_handler(
    request: Request, exc: ActivityNotFoundError
) -> JSONResponse:
    """Handler for ActivityNotFoundError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "activity_id": exc.activity_id,
        },
    )


async def duplicate_name_handler(
    request: Request, exc: DuplicateNameError
) -> JSONResponse:
    """Handler for DuplicateNameError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "entity_type": exc.entity_type,
            "name": exc.name,
        },
    )


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handler for ValidationError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.message,
            "detail": exc.detail,
        },
    )


async def storage_error_handler(
    request: Request, exc: StorageError
) -> JSONResponse:
    """Handler for StorageError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "operation": exc.operation,
        },
    )
