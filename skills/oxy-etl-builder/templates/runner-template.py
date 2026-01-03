"""
Pipeline Runner Template
========================

Template for building ETL pipeline runners with:
- Full CLI interface (run, test, config, schema commands)
- Support for multiple run modes
- Backfill with chunking
- Metrics computation

Replace <Provider> and <Entity> with your actual names.
"""

from datetime import datetime

import typer
from rich.console import Console

# Import core framework (adjust paths)
# from etl.core.pipeline import BasePipelineRunner, PipelineConfig
# from etl.core.cli import setup_logging, parse_date

# Import source (adjust path)
# from etl.sources.provider.orders_source import provider_orders_source, ENTITY_IDS


# =============================================================================
# Placeholder imports - replace with actual imports
# =============================================================================

from dataclasses import dataclass, field
from typing import Any
from abc import ABC, abstractmethod


@dataclass
class PipelineConfig:
    """Pipeline configuration (copy from core/pipeline.py)."""
    dry_run: bool = False
    mock_api: bool = False
    real_api: bool = False
    days: int = 7
    start_date: datetime | None = None
    end_date: datetime | None = None
    backfill: bool = False
    chunk_days: int = 30
    log_level: str = "WARNING"
    skip_metrics: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class BasePipelineRunner(ABC):
    """Base runner (copy from core/pipeline.py)."""
    @property
    @abstractmethod
    def pipeline_name(self) -> str: pass
    @property
    @abstractmethod
    def dataset_name(self) -> str: pass
    @property
    @abstractmethod
    def pipeline_emoji(self) -> str: pass
    @property
    @abstractmethod
    def pipeline_description(self) -> str: pass
    @abstractmethod
    def get_source(self, config, resource_name=None, start_date=None, end_date=None): pass
    @abstractmethod
    def get_resources_config(self) -> dict[str, bool]: pass
    def compute_metrics(self) -> None: pass
    def run(self, config: PipelineConfig) -> None:
        print(f"Running {self.pipeline_description}...")


def setup_logging(level: str) -> None:
    """Setup logging (copy from core/cli.py)."""
    import logging
    logging.basicConfig(level=level.upper())


def parse_date(date_str: str | None) -> datetime | None:
    """Parse date (copy from core/cli.py)."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d")


# Placeholder for source function
def provider_orders_source(**kwargs):
    """Placeholder - replace with actual source import."""
    raise NotImplementedError("Import your source function")


ENTITY_IDS = ["entity_001", "entity_002"]  # Replace with actual


# =============================================================================
# Runner Implementation
# =============================================================================

class ProviderOrdersRunner(BasePipelineRunner):
    """
    Runner for Provider orders pipeline.

    Handles:
    - Pipeline creation and execution
    - Resource configuration for backfill
    - Post-load metrics computation
    """

    @property
    def pipeline_name(self) -> str:
        """DLT pipeline identifier."""
        return "provider_orders_pipeline"

    @property
    def dataset_name(self) -> str:
        """Destination dataset name."""
        return "analytics"

    @property
    def pipeline_emoji(self) -> str:
        """Emoji for console output."""
        return "📦"

    @property
    def pipeline_description(self) -> str:
        """Human-readable description."""
        return "Provider Orders"

    def get_source(
        self,
        config: PipelineConfig,
        resource_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Create DLT source for extraction.

        Args:
            config: Pipeline configuration
            resource_name: Optional specific resource to load
            start_date: Start date for date-filtered resources
            end_date: End date for date-filtered resources

        Returns:
            DLT source object
        """
        source = provider_orders_source(
            use_mock=config.dry_run and not config.mock_api and not config.real_api,
            backfill_mode=config.backfill,
            days_back=config.days,
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
        )

        if resource_name:
            return source.with_resources(resource_name)

        return source

    def get_resources_config(self) -> dict[str, bool]:
        """
        Configure resources for backfill mode.

        Returns:
            Dict mapping resource name to whether it needs date filtering.
            - False: Static data, load once at start of backfill
            - True: Time-series data, load in date chunks
        """
        return {
            "entities": False,      # Static, load once
            "orders": True,         # Time-series, date filtered
            "order_items": True,    # Time-series, date filtered
        }

    def compute_metrics(self) -> None:
        """
        Compute derived metrics after data load.

        Override this to add post-load transformations.
        """
        # Example:
        # from etl.transforms.compute_order_metrics import compute_order_metrics
        # compute_order_metrics()
        pass

    def get_schema_info(self) -> dict[str, dict]:
        """Return schema documentation for CLI."""
        return {
            "entities": {
                "description": "Entity (location/store) metadata",
                "primary_key": "id",
            },
            "orders": {
                "description": "Order transactions",
                "primary_key": "id",
            },
            "order_items": {
                "description": "Order line items (flattened)",
                "primary_key": ["order_id", "item_id"],
            },
        }

    def get_sample_queries(self) -> list[str]:
        """Return sample queries for CLI."""
        return [
            "SELECT COUNT(*) FROM analytics.orders",
            "SELECT entity_id, COUNT(*) as orders FROM analytics.orders GROUP BY entity_id",
        ]


# =============================================================================
# CLI Interface
# =============================================================================

app = typer.Typer(
    name="provider-orders",
    help="Provider Orders ETL Pipeline",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d",
        help="Use DuckDB instead of production warehouse"
    ),
    mock_api: bool = typer.Option(
        False, "--mock-api",
        help="Use mock API responses (for testing)"
    ),
    real_api: bool = typer.Option(
        False, "--real-api",
        help="Use real API with dry-run destination"
    ),
    days: int = typer.Option(
        7, "--days",
        help="Days of data to fetch"
    ),
    backfill: bool = typer.Option(
        False, "--backfill", "-b",
        help="Enable chunked backfill mode"
    ),
    start_date: str = typer.Option(
        None, "--start-date",
        help="Start date (YYYY-MM-DD) for backfill"
    ),
    end_date: str = typer.Option(
        None, "--end-date",
        help="End date (YYYY-MM-DD) for backfill"
    ),
    chunk_days: int = typer.Option(
        30, "--chunk-days",
        help="Days per chunk in backfill mode"
    ),
    skip_metrics: bool = typer.Option(
        False, "--skip-metrics",
        help="Skip metrics computation"
    ),
    log_level: str = typer.Option(
        "WARNING", "--log-level", "-l",
        help="Log level (DEBUG, INFO, WARNING, ERROR)"
    ),
):
    """
    Run the ETL pipeline.

    Examples:

        # Default: last 7 days to production
        python -m etl.runners.provider_orders run

        # Dry run with DuckDB
        python -m etl.runners.provider_orders run --dry-run

        # Backfill last 90 days
        python -m etl.runners.provider_orders run --backfill --days 90

        # Backfill specific date range
        python -m etl.runners.provider_orders run --backfill \\
            --start-date 2024-01-01 --end-date 2024-03-01
    """
    setup_logging(log_level)

    config = PipelineConfig(
        dry_run=dry_run,
        mock_api=mock_api,
        real_api=real_api,
        days=days,
        backfill=backfill,
        start_date=parse_date(start_date),
        end_date=parse_date(end_date),
        chunk_days=chunk_days,
        skip_metrics=skip_metrics,
        log_level=log_level,
    )

    runner = ProviderOrdersRunner()
    runner.run(config)


@app.command()
def test():
    """
    Run with mock data for quick testing.

    Uses mock API responses and DuckDB destination.
    """
    console.print("[blue]Running test with mock data...[/blue]")

    config = PipelineConfig(
        dry_run=True,
        mock_api=True,
        days=7,
    )

    runner = ProviderOrdersRunner()
    runner.run(config)


@app.command()
def config():
    """Show current configuration."""
    console.print("[bold]Current Configuration[/bold]\n")

    console.print(f"  Entity IDs: {ENTITY_IDS}")
    console.print(f"  Pipeline: {ProviderOrdersRunner().pipeline_name}")
    console.print(f"  Dataset: {ProviderOrdersRunner().dataset_name}")

    console.print("\n[bold]Resources:[/bold]")
    for resource, needs_date in ProviderOrdersRunner().get_resources_config().items():
        date_info = "(date-filtered)" if needs_date else "(static)"
        console.print(f"  {resource} {date_info}")


@app.command()
def schema():
    """Show data schema information."""
    runner = ProviderOrdersRunner()
    schema_info = runner.get_schema_info()

    console.print("[bold]Schema Information[/bold]\n")

    for table, info in schema_info.items():
        console.print(f"[cyan]{table}[/cyan]")
        console.print(f"  Description: {info.get('description', 'N/A')}")
        console.print(f"  Primary Key: {info.get('primary_key', 'N/A')}")
        console.print()

    console.print("[bold]Sample Queries:[/bold]")
    for query in runner.get_sample_queries():
        console.print(f"  {query}")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    app()
