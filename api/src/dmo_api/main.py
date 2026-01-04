"""
Main FastAPI application for DMO API.

This module sets up the FastAPI app with all routers and exception handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dmo_api.exceptions import (
    activity_not_found_handler,
    dmo_error_handler,
    dmo_not_found_handler,
    duplicate_name_handler,
    storage_error_handler,
    validation_error_handler,
)
from dmo_api.routers import activities, completions, dmos, reports
from dmo_core.errors import (
    ActivityNotFoundError,
    DmoError,
    DmoNotFoundError,
    DuplicateNameError,
    StorageError,
    ValidationError,
)

# Create FastAPI app
app = FastAPI(
    title="DMO API",
    description="REST API for Daily Methods of Operation (DMO) tracking system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(DmoNotFoundError, dmo_not_found_handler)
app.add_exception_handler(ActivityNotFoundError, activity_not_found_handler)
app.add_exception_handler(DuplicateNameError, duplicate_name_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(StorageError, storage_error_handler)
app.add_exception_handler(DmoError, dmo_error_handler)  # Catch-all for DmoError

# Include routers
app.include_router(dmos.router)
app.include_router(activities.router)
app.include_router(completions.router)
app.include_router(reports.router)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Welcome message with API information
    """
    return {
        "message": "DMO API - Daily Methods of Operation tracking system",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}
