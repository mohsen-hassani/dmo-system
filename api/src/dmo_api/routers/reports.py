"""
Report endpoints for the FastAPI application.

Provides daily and monthly reports for DMO tracking.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query

from dmo_api.dependencies import ServiceDep
from dmo_core.models import DailyReport, DMOSummary, MonthlyReport

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/today", response_model=DailyReport)
async def get_today_report(
    service: ServiceDep,
) -> DailyReport:
    """
    Get today's status for all active DMOs.

    Returns a report showing:
    - All active DMOs
    - Completion status for today
    - Activities for each DMO
    - Any notes

    Returns:
        Daily report for today
    """
    return await service.get_daily_report(date.today())


@router.get("/daily/{date}", response_model=DailyReport)
async def get_daily_report(
    service: ServiceDep,
    report_date: Annotated[date, Path(alias="date", description="Report date (YYYY-MM-DD)")],
) -> DailyReport:
    """
    Get a daily report for a specific date.

    Returns a report showing all active DMOs and their completion status
    for the specified date.

    Args:
        report_date: The date to generate the report for

    Returns:
        Daily report for the specified date
    """
    return await service.get_daily_report(report_date)


@router.get("/monthly", response_model=list[MonthlyReport])
async def get_this_month_report(
    service: ServiceDep,
) -> list[MonthlyReport]:
    """
    Get monthly report for the current month on all active DMOs.

    Returns reports for all active DMOs showing:
    - Completion status for each day
    - Total days and completed days
    - Completion rate
    - Current and longest streaks
    - Missed days

    Returns:
        List of monthly reports (one per active DMO)
    """
    today = date.today()
    return await service.get_monthly_report(today.year, today.month)


@router.get("/monthly/{year}/{month}", response_model=list[MonthlyReport])
async def get_monthly_report(
    service: ServiceDep,
    year: Annotated[int, Path(description="Year (e.g., 2026)", ge=2000, le=3000)],
    month: Annotated[int, Path(description="Month (1-12)", ge=1, le=12)],
    dmo_id: Annotated[
        int | None, Query(description="Specific DMO ID (defaults to all active DMOs)")
    ] = None,
) -> list[MonthlyReport]:
    """
    Get monthly report for a specific month.

    If dmo_id is provided, returns a report for that DMO only.
    Otherwise, returns reports for all active DMOs.

    Args:
        year: The year (e.g., 2026)
        month: The month (1-12)
        dmo_id: Optional specific DMO ID

    Returns:
        List of monthly reports

    Raises:
        404: If specified DMO not found
    """
    return await service.get_monthly_report(year, month, dmo_id)


@router.get("/summary/{dmo_id}", response_model=DMOSummary)
async def get_dmo_summary(
    service: ServiceDep,
    dmo_id: Annotated[int, Path(description="DMO ID", gt=0)],
    start_date: Annotated[date, Query(description="Start date (inclusive, YYYY-MM-DD)")],
    end_date: Annotated[date, Query(description="End date (inclusive, YYYY-MM-DD)")],
) -> DMOSummary:
    """
    Get a custom summary for a DMO over a date range.

    Returns statistics including:
    - Total days in range
    - Completed days
    - Completion rate
    - Current streak
    - Longest streak

    Args:
        dmo_id: The DMO's ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        DMO summary for the date range

    Raises:
        404: If DMO not found
    """
    return await service.get_dmo_summary(dmo_id, start_date, end_date)
