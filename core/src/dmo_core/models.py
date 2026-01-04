"""
Domain models (DTOs) for the DMO-Core system.

This module defines three layers:
1. Create models (*Create) - for input validation when creating entities
2. Update models (*Update) - for partial updates with optional fields
3. Read models (*Read) - for output/response data with all fields populated
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# DMO Models
# =============================================================================


class DMOCreate(BaseModel):
    """Input model for creating a new DMO."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    timezone: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip()


class DMOUpdate(BaseModel):
    """Input model for updating an existing DMO. All fields optional."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    timezone: str | None = Field(default=None, max_length=50)
    active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip() if v else v


class DMORead(BaseModel):
    """Output model representing a complete DMO entity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    active: bool
    timezone: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Activity Models
# =============================================================================


class ActivityCreate(BaseModel):
    """Input model for creating a new Activity within a DMO."""

    model_config = ConfigDict(str_strip_whitespace=True)

    dmo_id: int
    name: str = Field(..., min_length=1, max_length=500)
    order: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip()


class ActivityUpdate(BaseModel):
    """Input model for updating an existing Activity. All fields optional."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=500)
    order: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip() if v else v


class ActivityRead(BaseModel):
    """Output model representing a complete Activity entity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dmo_id: int
    name: str
    order: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# DMOCompletion Models
# =============================================================================


class DMOCompletionCreate(BaseModel):
    """Input model for setting/updating DMO completion status."""

    dmo_id: int
    date: date
    completed: bool
    note: str | None = Field(default=None, max_length=2000)


class DMOCompletionRead(BaseModel):
    """Output model representing a DMO completion record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dmo_id: int
    date: date
    completed: bool
    note: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Report Models
# =============================================================================


class DMODailyStatus(BaseModel):
    """A single DMO's status for a specific day in a daily report."""

    dmo: DMORead
    completed: bool
    note: str | None
    activities: list[str]  # Activity names only, ordered


class DailyReport(BaseModel):
    """Complete report for a single day across all active DMOs."""

    date: date
    dmos: list[DMODailyStatus]


class DayCompletion(BaseModel):
    """Completion status for a single day in a monthly report."""

    date: date
    completed: bool
    note: str | None = None


class MonthSummary(BaseModel):
    """Aggregated statistics for a month."""

    total_days: int
    completed_days: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    current_streak: int = Field(..., ge=0)
    longest_streak: int = Field(..., ge=0)
    missed_days: list[date]


class MonthlyReport(BaseModel):
    """Complete monthly report for a single DMO."""

    dmo: DMORead
    year: int
    month: int = Field(..., ge=1, le=12)
    days: list[DayCompletion]
    summary: MonthSummary


class DMOSummary(BaseModel):
    """Summary statistics for a DMO over a date range."""

    dmo: DMORead
    start_date: date
    end_date: date
    total_days: int
    completed_days: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    current_streak: int = Field(..., ge=0)
    longest_streak: int = Field(..., ge=0)
