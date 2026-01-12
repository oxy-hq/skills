"""
CLI Utilities
=============

Helper functions for ETL pipeline CLIs including:
- Logging configuration with Rich console output
- Date parsing and validation
- Common CLI patterns

Usage:
    from etl.core.cli import setup_logging, parse_date

    setup_logging("INFO")
    date = parse_date("2024-01-15")
"""

import logging
import sys
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    level: str = "WARNING",
    console: Console | None = None,
) -> None:
    """
    Configure logging with Rich handler for beautiful console output.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Optional Rich console instance (creates new if not provided)
    """
    # Normalize level
    level = level.upper()

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console or Console(),
                rich_tracebacks=True,
                show_path=False,
            )
        ],
        force=True,  # Override existing config
    )

    # Quiet noisy libraries
    for noisy_logger in [
        "httpx",
        "httpcore",
        "urllib3",
        "dlt",
        "dlt.normalize",
        "dlt.extract",
        "dlt.load",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def parse_date(date_str: str | None) -> datetime | None:
    """
    Parse a date string in YYYY-MM-DD format.

    Args:
        date_str: Date string or None

    Returns:
        datetime object or None

    Raises:
        ValueError: If date string is invalid format
    """
    if date_str is None:
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
        )


def validate_date_range(
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    """
    Validate a date range and raise errors for invalid combinations.

    Args:
        start_date: Start of range (optional)
        end_date: End of range (optional)

    Returns:
        Validated (start_date, end_date) tuple

    Raises:
        ValueError: If range is invalid
    """
    if start_date and end_date and start_date > end_date:
        raise ValueError(
            f"Start date ({start_date.date()}) must be before "
            f"end date ({end_date.date()})"
        )

    if end_date and not start_date:
        raise ValueError("If end_date is specified, start_date must also be specified")

    return start_date, end_date


def confirm_action(
    message: str,
    console: Console | None = None,
    default: bool = False,
) -> bool:
    """
    Ask user to confirm an action.

    Args:
        message: Confirmation message
        console: Rich console for output
        default: Default answer if user presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    console = console or Console()

    suffix = " [Y/n] " if default else " [y/N] "
    console.print(f"[yellow]{message}{suffix}[/yellow]", end="")

    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        console.print()
        return False

    if not response:
        return default

    return response in ("y", "yes")


def print_table(
    data: list[dict],
    columns: list[str] | None = None,
    title: str | None = None,
    console: Console | None = None,
    max_rows: int = 20,
) -> None:
    """
    Print data as a formatted table.

    Args:
        data: List of dictionaries to display
        columns: Column names to show (default: all keys from first row)
        title: Optional table title
        console: Rich console for output
        max_rows: Maximum rows to display
    """
    from rich.table import Table

    console = console or Console()

    if not data:
        console.print("[dim]No data to display[/dim]")
        return

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    # Create table
    table = Table(title=title)
    for col in columns:
        table.add_column(col)

    # Add rows
    for row in data[:max_rows]:
        table.add_row(*[str(row.get(col, "")) for col in columns])

    console.print(table)

    if len(data) > max_rows:
        console.print(f"[dim]... and {len(data) - max_rows} more rows[/dim]")


def exit_with_error(
    message: str,
    console: Console | None = None,
    code: int = 1,
) -> None:
    """
    Print error message and exit.

    Args:
        message: Error message
        console: Rich console for output
        code: Exit code (default: 1)
    """
    console = console or Console()
    console.print(f"[red]Error: {message}[/red]")
    sys.exit(code)
