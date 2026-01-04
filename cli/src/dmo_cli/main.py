"""
Command-line interface for DMO-Core.

Provides commands to manage Daily Methods of Operation tracking:
- Create DMOs with activities
- List DMOs
- Mark days as complete/incomplete
- Generate monthly reports
"""

import asyncio
from collections.abc import Coroutine
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any, TypeVar

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dmo_core import (
    ActivityCreate,
    DMOCreate,
    DmoService,
)
from dmo_core.storage.sqlite import SqliteBackend

T = TypeVar("T")

# Initialize Typer app and Rich console
app = typer.Typer(
    name="dmo",
    help="Daily Methods of Operation (DMO) tracking system",
    add_completion=False,
)
console = Console()

# Default database location
DEFAULT_DB_DIR = Path.home() / ".dmo"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "dmo.db"


def get_db_path() -> Path:
    """Get the database path, creating directory if needed."""
    db_dir = DEFAULT_DB_DIR
    db_dir.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH


async def get_service() -> DmoService:
    """Initialize and return a DmoService with SQLite backend."""
    db_path = get_db_path()
    backend = SqliteBackend(str(db_path))
    await backend.init()
    return DmoService(backend)


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Helper to run async coroutines in sync context."""
    return asyncio.run(coro)


def _calculate_display_range(max_days: int = 10) -> tuple[date, date]:
    """
    Calculate the date range for completion summary display.

    Shows up to max_days from the start of current month to today.
    - If we're early in the month (day <= max_days), show from day 1 to today
    - Otherwise, show the last max_days

    Args:
        max_days: Maximum number of days to display

    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Calculate days elapsed in current month
    days_elapsed = (today - month_start).days + 1  # +1 to include today

    if days_elapsed <= max_days:
        # Show all days from month start
        return month_start, today
    else:
        # Show only the last max_days
        start_date = date(today.year, today.month, today.day - max_days + 1)
        return start_date, today


async def _render_completion_summary(
    service: DmoService,
    dmo_id: int,
    *,
    max_days: int = 10
) -> Text:
    """
    Render a visual completion summary for the last N days of current month.

    Shows colored boxes representing completion status:
    - Green (■) = completed
    - Red (■) = not completed
    - Gray/dim (■) = no data/missing record

    Args:
        service: The DmoService instance
        dmo_id: ID of the DMO
        max_days: Maximum number of days to display (default: 10)

    Returns:
        Rich Text object with two lines:
        Line 1: Colored boxes
        Line 2: Day numbers

    Example output:
        ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
        2 3 4 5 6 7 8 9 10 11
    """
    from dmo_core.utils import date_range

    # Calculate date range
    start_date, end_date = _calculate_display_range(max_days)

    # Fetch completion data
    completions = await service._storage.list_completions(dmo_id, start_date, end_date)

    # Create lookup map: date -> DMOCompletionRead
    completion_map = {c.date: c for c in completions}

    # Generate list of dates
    dates = date_range(start_date, end_date)

    # Build visual representation
    result = Text()

    # Line 1: Colored boxes
    for i, d in enumerate(dates):
        if i > 0:
            result.append(" ")  # Space between boxes

        completion = completion_map.get(d)

        if completion is None:
            # No data - gray/dim
            result.append("■", style="dim")
        elif completion.completed:
            # Completed - green
            result.append("■", style="green")
        else:
            # Not completed - red
            result.append("■", style="red")

    result.append("\n")

    # Line 2: Day numbers (aligned with boxes)
    for i, d in enumerate(dates):
        if i > 0:
            result.append(" ")

        # Format day number
        day_str = f"{d.day}"
        result.append(day_str, style="dim")

    return result


@app.command("create")
def create_dmo(
    name: Annotated[str, typer.Argument(help="Name of the DMO")],
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Description of the DMO")
    ] = None,
    activities: Annotated[
        list[str] | None,
        typer.Option("--activity", "-a", help="Activity name (can be used multiple times)"),
    ] = None,
) -> None:
    """
    Create a new DMO with optional activities.

    Example:
        dmo create "Morning Routine" -a "Meditation" -a "Exercise" -a "Journaling"
    """
    async def _create() -> None:
        service = await get_service()

        # Create the DMO
        dmo = await service.create_dmo(DMOCreate(
            name=name,
            description=description,
        ))

        console.print(f"[green]✓[/green] Created DMO: [bold]{dmo.name}[/bold]")
        console.print(f"  ID: {dmo.id}")

        # Create activities if provided
        if activities:
            console.print(f"\n[cyan]Adding {len(activities)} activities...[/cyan]")
            for i, activity_name in enumerate(activities):
                activity = await service.create_activity(ActivityCreate(
                    dmo_id=dmo.id,
                    name=activity_name,
                    order=i,
                ))
                console.print(f"  [green]✓[/green] {activity.name}")

        # Close the backend
        await service._storage.close()

    run_async(_create())


@app.command("list")
def list_dmos(
    include_inactive: Annotated[
        bool, typer.Option("--all", "-a", help="Include inactive DMOs")
    ] = False,
) -> None:
    """
    List all DMOs.

    Example:
        dmo list
        dmo list --all
    """
    async def _list() -> None:
        service = await get_service()

        dmos = await service.list_dmos(include_inactive=include_inactive)

        if not dmos:
            console.print("[yellow]No DMOs found.[/yellow]")
            await service._storage.close()
            return

        # Create a table
        table = Table(title="Daily Methods of Operation")
        table.add_column("Name", style="cyan", no_wrap=False)
        table.add_column("ID", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Activities", justify="right")
        table.add_column("Description", style="dim", no_wrap=False)

        for dmo in dmos:
            # Get activities count
            activities = await service.list_activities(dmo.id)
            activity_count = len(activities)

            # Status
            status = "[green]Active[/green]" if dmo.active else "[red]Inactive[/red]"

            table.add_row(
                dmo.name,
                str(dmo.id),
                status,
                str(activity_count),
                dmo.description or "",
            )

        console.print(table)
        await service._storage.close()

    run_async(_list())


@app.command("show")
def show_dmo(
    dmo_id: Annotated[int, typer.Argument(help="DMO ID")],
) -> None:
    """
    Show details of a specific DMO including its activities.

    Example:
        dmo show <dmo-id>
    """
    async def _show() -> None:
        service = await get_service()

        try:
            dmo = await service.get_dmo(dmo_id)
            activities = await service.list_activities(dmo_id)

            # Create panel with DMO details
            details = Text()
            details.append("Name: ", style="bold cyan")
            details.append(f"{dmo.name}\n")
            details.append("ID: ", style="bold cyan")
            details.append(f"{dmo.id}\n")
            details.append("Status: ", style="bold cyan")
            details.append(f"{'Active' if dmo.active else 'Inactive'}\n",
                          style="green" if dmo.active else "red")
            if dmo.description:
                details.append("Description: ", style="bold cyan")
                details.append(f"{dmo.description}\n")
            details.append("Created: ", style="bold cyan")
            details.append(f"{dmo.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")

            console.print(Panel(details, title="[bold]DMO Details[/bold]", border_style="blue"))

            # Show activities
            if activities:
                console.print(f"\n[bold cyan]Activities ({len(activities)}):[/bold cyan]")
                for i, activity in enumerate(activities, 1):
                    console.print(f"  {i}. {activity.name}")
            else:
                console.print("\n[dim]No activities defined.[/dim]")

            # Show completion summary
            console.print("\n[bold cyan]Recent Completion History:[/bold cyan]")
            try:
                completion_visual = await _render_completion_summary(service, dmo_id)
                console.print(completion_visual)
            except Exception:
                # Gracefully handle errors to avoid breaking the command
                console.print("[dim]Unable to load completion history[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        await service._storage.close()

    run_async(_show())


@app.command("delete")
def delete_dmo(
    dmo_id: Annotated[int, typer.Argument(help="DMO ID to delete")],
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Delete a DMO and all its associated data.

    Example:
        dmo delete <dmo-id>
        dmo delete <dmo-id> --yes
    """
    async def _delete() -> None:
        service = await get_service()

        try:
            # Get DMO name for display
            dmo = await service.get_dmo(dmo_id)

            # Confirm deletion
            if not confirm:
                response = typer.confirm(
                    f"Are you sure you want to delete '{dmo.name}' (ID: {dmo_id})?\n"
                    "This will also delete all activities and completion records.",
                    default=False,
                )
                if not response:
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                    await service._storage.close()
                    return

            # Perform deletion
            await service.delete_dmo(dmo_id)

            console.print(f"[green]✓[/green] Deleted DMO: [bold]{dmo.name}[/bold]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        await service._storage.close()

    run_async(_delete())


@app.command("complete")
def mark_complete(
    dmo_id: Annotated[int, typer.Argument(help="DMO ID")],
    completed: Annotated[
        bool, typer.Option("--yes/--no", help="Mark as complete or incomplete")
    ] = True,
    date_str: Annotated[
        str | None, typer.Option("--date", "-d", help="Date (YYYY-MM-DD), defaults to today")
    ] = None,
    note: Annotated[str | None, typer.Option("--note", "-n", help="Optional note")] = None,
) -> None:
    """
    Mark a DMO as complete or incomplete for a specific date.

    Examples:
        dmo complete <dmo-id> --yes
        dmo complete <dmo-id> --no --date 2025-01-01
        dmo complete <dmo-id> --yes --note "Great session!"
    """
    async def _mark() -> None:
        service = await get_service()

        try:
            # Parse date
            if date_str:
                completion_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                completion_date = date.today()

            # Set completion
            await service.set_dmo_completion(
                dmo_id,
                completion_date,
                completed,
                note,
            )

            # Get DMO name for display
            dmo = await service.get_dmo(dmo_id)

            status = "[green]complete[/green]" if completed else "[red]incomplete[/red]"
            console.print(
                f"[green]✓[/green] Marked [bold]{dmo.name}[/bold] as {status} "
                f"for {completion_date}"
            )

            if note:
                console.print(f"  Note: {note}")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        await service._storage.close()

    run_async(_mark())


@app.command("report")
def monthly_report(
    year: Annotated[int, typer.Option("--year", "-y", help="Year (defaults to current year)")],
    month: Annotated[
        int, typer.Option("--month", "-m", help="Month (1-12, defaults to current month)")
    ],
    dmo_id: Annotated[
        int | None, typer.Option("--dmo", help="Specific DMO ID (defaults to all active DMOs)")
    ] = None,
) -> None:
    """
    Generate a monthly report for DMOs.

    Examples:
        dmo report --year 2025 --month 1
        dmo report --year 2025 --month 1 --dmo <dmo-id>
    """
    async def _report() -> None:
        service = await get_service()

        try:
            # Get monthly reports
            reports = await service.get_monthly_report(year, month, dmo_id)

            if not reports:
                console.print("[yellow]No reports found.[/yellow]")
                await service._storage.close()
                return

            # Display each report
            for report in reports:
                console.print()

                # Title panel
                title = f"{report.dmo.name} - {year}/{month:02d}"
                console.print(Panel(title, style="bold cyan"))

                # Summary statistics
                summary = report.summary
                stats = Table.grid(padding=(0, 2))
                stats.add_column(style="cyan")
                stats.add_column(style="bold")

                stats.add_row("Total Days:", str(summary.total_days))
                stats.add_row("Completed Days:", f"[green]{summary.completed_days}[/green]")
                stats.add_row("Completion Rate:", f"{summary.completion_rate * 100:.1f}%")
                stats.add_row("Current Streak:", f"[yellow]{summary.current_streak}[/yellow] days")
                stats.add_row("Longest Streak:", f"[yellow]{summary.longest_streak}[/yellow] days")

                console.print(stats)

                # Show completion history
                console.print("\n[bold cyan]Recent Completion History:[/bold cyan]")
                try:
                    completion_visual = await _render_completion_summary(service, report.dmo.id)
                    console.print(completion_visual)
                except Exception:
                    console.print("[dim]Unable to load completion history[/dim]")

                # Calendar view (simplified)
                if summary.missed_days:
                    console.print(f"\n[red]Missed Days ({len(summary.missed_days)}):[/red]")
                    missed_str = ", ".join(d.strftime("%d") for d in summary.missed_days[:10])
                    if len(summary.missed_days) > 10:
                        missed_str += f" ... and {len(summary.missed_days) - 10} more"
                    console.print(f"  {missed_str}")
                else:
                    console.print("\n[green]Perfect month! No missed days.[/green]")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        await service._storage.close()

    run_async(_report())


@app.command("today")
def today_report() -> None:
    """
    Show today's status for all active DMOs.

    Example:
        dmo today
    """
    async def _today() -> None:
        service = await get_service()

        try:
            report = await service.get_daily_report(date.today())

            if not report.dmos:
                console.print("[yellow]No active DMOs found.[/yellow]")
                await service._storage.close()
                return

            console.print(Panel(
                f"[bold]Daily Report for {report.date.strftime('%Y-%m-%d')}[/bold]",
                style="cyan"
            ))

            for dmo_status in report.dmos:
                status_icon = "[green]✓[/green]" if dmo_status.completed else "[red]✗[/red]"
                console.print(f"\n{status_icon} [bold]{dmo_status.dmo.name}[/bold]")

                if dmo_status.activities:
                    console.print("  [dim]Activities:[/dim]")
                    for activity in dmo_status.activities:
                        console.print(f"    • {activity}")

                if dmo_status.note:
                    console.print(f"  [dim]Note: {dmo_status.note}[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        await service._storage.close()

    run_async(_today())


@app.command("stats")
def show_stats() -> None:
    """
    Show completion statistics for all active DMOs in the current month.

    Displays each DMO with its name and recent completion history.

    Example:
        dmo stats
    """
    async def _stats() -> None:
        service = await get_service()

        try:
            # Get all active DMOs
            dmos = await service.list_dmos(include_inactive=False)

            if not dmos:
                console.print("[yellow]No active DMOs found.[/yellow]")
                await service._storage.close()
                return

            # Get current month info
            today = date.today()
            console.print(Panel(
                f"[bold]DMO Statistics for {today.strftime('%B %Y')}[/bold]",
                style="cyan"
            ))

            for dmo in dmos:
                console.print(f"\n[bold cyan]{dmo.name}[/bold cyan]")
                try:
                    completion_visual = await _render_completion_summary(service, dmo.id)
                    console.print(completion_visual)
                except Exception:
                    console.print("[dim]Unable to load completion history[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        await service._storage.close()

    run_async(_stats())


@app.command("init")
def initialize_db() -> None:
    """
    Initialize the DMO database.

    This is automatically done when needed, but can be run manually.
    """
    async def _init() -> None:
        db_path = get_db_path()
        backend = SqliteBackend(str(db_path))
        await backend.init()
        await backend.close()
        console.print(f"[green]✓[/green] Database initialized at: {db_path}")

    run_async(_init())


@app.command("reset")
def reset_database(
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Delete the database and start fresh.

    WARNING: This will delete ALL DMOs, activities, and completion records.

    Example:
        dmo reset
        dmo reset --yes
    """
    db_path = get_db_path()

    if not db_path.exists():
        console.print("[yellow]No database found. Nothing to reset.[/yellow]")
        return

    # Confirm deletion
    if not confirm:
        response = typer.confirm(
            "Are you sure you want to delete the entire database?\n"
            "This will permanently delete ALL DMOs, activities, and completion records.",
            default=False,
        )
        if not response:
            console.print("[yellow]Reset cancelled.[/yellow]")
            return

    # Delete the database file
    db_path.unlink()
    console.print(f"[green]✓[/green] Database deleted: {db_path}")
    console.print("[dim]Run 'dmo init' or any command to create a fresh database.[/dim]")


if __name__ == "__main__":
    app()
