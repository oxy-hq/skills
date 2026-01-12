"""
Base Pipeline Runner
====================

Core infrastructure for ETL pipelines with support for:
- Multiple warehouse destinations (ClickHouse, Snowflake, MotherDuck, DuckDB)
- Chunked backfills with crash-safe incremental writes
- Rate limiting for API-heavy backfills
- Metrics computation after data load

Usage:
    Subclass BasePipelineRunner and implement required methods.
"""

import gc
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import dlt
from rich.console import Console

from .chunking import generate_date_chunks, generate_monthly_chunks


@dataclass
class PipelineConfig:
    """Configuration for a pipeline run."""

    # Run mode
    dry_run: bool = False      # Use DuckDB instead of production warehouse
    mock_api: bool = False     # Use mock API responses
    real_api: bool = False     # Use real API with dry-run destination

    # Date range
    days: int = 7              # Days of data to fetch (default mode)
    start_date: datetime | None = None   # Explicit start date
    end_date: datetime | None = None     # Explicit end date

    # Backfill settings
    backfill: bool = False     # Enable chunked backfill mode
    chunk_days: int = 30       # Days per chunk in backfill

    # Other options
    log_level: str = "WARNING"
    drop_pending: bool = False  # Drop pending packages from failed runs
    skip_metrics: bool = False  # Skip metrics computation

    # Pipeline-specific options (for extensibility)
    extra: dict[str, Any] = field(default_factory=dict)


class BasePipelineRunner(ABC):
    """
    Base class for ETL pipeline runners.

    Subclasses must implement:
    - pipeline_name: Name for the DLT pipeline
    - dataset_name: Destination dataset name
    - pipeline_emoji: Emoji for console output
    - pipeline_description: Human-readable description
    - get_source(): Returns the DLT source for extraction
    - get_resources_config(): Returns resource configuration for backfill

    Optional overrides:
    - compute_metrics(): Post-load metrics computation
    - get_schema_info(): Schema documentation for CLI output
    - get_sample_queries(): Sample queries for CLI output
    """

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.logger = logging.getLogger(self.__class__.__name__)

    # --- Required Properties ---

    @property
    @abstractmethod
    def pipeline_name(self) -> str:
        """DLT pipeline name (e.g., 'toast_labor_pipeline')."""
        pass

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Dataset name in destination (e.g., 'restaurant_analytics')."""
        pass

    @property
    @abstractmethod
    def pipeline_emoji(self) -> str:
        """Emoji for console output (e.g., '👷' for labor, '🛒' for sales)."""
        pass

    @property
    @abstractmethod
    def pipeline_description(self) -> str:
        """Human-readable pipeline description."""
        pass

    # --- Required Methods ---

    @abstractmethod
    def get_source(
        self,
        config: PipelineConfig,
        resource_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Any:
        """
        Create and return the DLT source for this pipeline.

        Args:
            config: Pipeline configuration
            resource_name: If provided, only return this specific resource
            start_date: Start date for date-filtered resources
            end_date: End date for date-filtered resources

        Returns:
            DLT source object
        """
        pass

    @abstractmethod
    def get_resources_config(self) -> dict[str, bool]:
        """
        Return resource configuration for backfill mode.

        Returns:
            Dict mapping resource name to whether it's date-filtered.
            Example: {"restaurants": False, "employees": False, "time_entries": True}

            - False: Static data, loaded once at start
            - True: Time-series data, loaded in date chunks
        """
        pass

    # --- Optional Overrides ---

    def compute_metrics(self) -> None:
        """
        Compute metrics after pipeline completes.
        Override in subclass to enable metrics computation.
        """
        pass

    def get_schema_info(self) -> dict[str, dict[str, Any]]:
        """
        Return schema documentation for CLI output.
        Override in subclass for custom schema docs.
        """
        return {}

    def get_sample_queries(self) -> list[str]:
        """
        Return sample queries for CLI output.
        Override in subclass for custom sample queries.
        """
        return []

    # --- Pipeline Creation ---

    def create_pipeline(self, config: PipelineConfig) -> dlt.Pipeline:
        """Create DLT pipeline with appropriate destination."""

        # Dry-run mode: use local DuckDB
        if config.dry_run:
            return dlt.pipeline(
                pipeline_name=self.pipeline_name,
                destination="duckdb",
                dataset_name=self.dataset_name,
            )

        # Production: detect and configure warehouse
        return self._create_production_pipeline()

    def _create_production_pipeline(self) -> dlt.Pipeline:
        """
        Create production pipeline with configured warehouse.

        Override this method to customize warehouse configuration.
        Default implementation uses environment variables.
        """

        # Option 1: ClickHouse (default if CLICKHOUSE_HOST is set)
        if os.getenv("CLICKHOUSE_HOST"):
            return self._create_clickhouse_pipeline()

        # Option 2: Snowflake
        if os.getenv("SNOWFLAKE_ACCOUNT"):
            return self._create_snowflake_pipeline()

        # Option 3: MotherDuck
        if os.getenv("MOTHERDUCK_TOKEN"):
            return self._create_motherduck_pipeline()

        # Fallback to DuckDB if no warehouse configured
        self.console.print(
            "[yellow]No warehouse configured, using local DuckDB[/yellow]"
        )
        return dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination="duckdb",
            dataset_name=self.dataset_name,
        )

    def _create_clickhouse_pipeline(self) -> dlt.Pipeline:
        """Create ClickHouse pipeline from environment variables."""
        credentials = {
            "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
            "port": int(os.getenv("CLICKHOUSE_PORT", "9000")),
            "http_port": int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
            "database": os.getenv("CLICKHOUSE_DATABASE", "default"),
            "username": os.getenv("CLICKHOUSE_USER", "default"),
            "password": os.getenv("CLICKHOUSE_PASSWORD", ""),
            "secure": os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true",
        }

        destination = dlt.destinations.clickhouse(
            credentials=credentials,
            loader_file_format="parquet"
        )

        return dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=destination,
            dataset_name=self.dataset_name,
        )

    def _create_snowflake_pipeline(self) -> dlt.Pipeline:
        """Create Snowflake pipeline from environment variables."""
        credentials = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        }

        return dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination="snowflake",
            credentials=credentials,
            dataset_name=self.dataset_name,
        )

    def _create_motherduck_pipeline(self) -> dlt.Pipeline:
        """Create MotherDuck pipeline from environment variables."""
        return dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination="motherduck",
            credentials={
                "database": os.getenv("MOTHERDUCK_DATABASE", "my_db"),
                "token": os.getenv("MOTHERDUCK_TOKEN"),
            },
            dataset_name=self.dataset_name,
        )

    # --- Main Execution ---

    def run(self, config: PipelineConfig) -> None:
        """
        Execute the pipeline with the given configuration.

        This handles:
        - Pipeline creation (ClickHouse vs DuckDB)
        - Backfill chunking and incremental writes
        - Metrics computation
        - Cleanup
        """
        self.console.print(
            f"[bold blue]{self.pipeline_emoji} Starting {self.pipeline_description}[/bold blue]"
        )

        # Configure backfill mode (single-threaded for rate limiting)
        if config.backfill:
            os.environ["EXTRACT__WORKERS"] = "1"
            os.environ["EXTRACT__MAX_PARALLEL_ITEMS"] = "1"

        pipeline = self.create_pipeline(config)

        # Drop pending packages if requested
        if config.drop_pending:
            self._drop_pending_packages(pipeline)

        # Print run mode
        self._print_run_mode(config)

        # Run pipeline
        if config.backfill:
            load_info = self._run_backfill(pipeline, config)
        else:
            load_info = self._run_parallel(pipeline, config)

        self.console.print("[green]Pipeline completed successfully![/green]")

        # Compute metrics (only in production mode)
        if not config.dry_run and not config.skip_metrics:
            self._run_metrics()

        # Print results
        self._print_results(pipeline, load_info, config)

        # Cleanup
        self._cleanup(pipeline)

    # --- Internal Methods ---

    def _drop_pending_packages(self, pipeline: dlt.Pipeline) -> None:
        """Drop any pending/failed load packages."""
        self.console.print(
            "[yellow]Dropping pending load packages from previous failed runs...[/yellow]"
        )
        try:
            pipeline.drop_pending_packages()
            self.console.print("[green]Pending packages dropped[/green]")
        except Exception as e:
            self.console.print(f"[yellow]Could not drop pending packages: {e}[/yellow]")

    def _print_run_mode(self, config: PipelineConfig) -> None:
        """Print the current run mode to console."""
        if config.mock_api:
            self.console.print(
                "[blue]Running with mocked API responses[/blue]"
            )
        elif config.dry_run and config.real_api:
            self.console.print(
                f"[cyan]Running with real API + DuckDB for last {config.days} days[/cyan]"
            )
        elif config.dry_run:
            self.console.print(
                "[yellow]Running in dry-run mode (DuckDB + mock data)[/yellow]"
            )
        elif config.backfill:
            self._print_backfill_info(config)
        else:
            self.console.print(
                f"[green]Analyzing data for last {config.days} days[/green]"
            )

    def _print_backfill_info(self, config: PipelineConfig) -> None:
        """Print backfill mode information."""
        if config.start_date and config.end_date:
            date_chunks = generate_date_chunks(
                config.start_date, config.end_date, chunk_size_days=config.chunk_days
            )
            num_chunks = len(date_chunks)
        else:
            num_chunks = len(
                generate_monthly_chunks(config.days, chunk_size_days=config.chunk_days)
            )

        resources_config = self.get_resources_config()
        date_resources = [r for r, is_date in resources_config.items() if is_date]

        self.console.print(
            f"[magenta]Running chunked backfill ({num_chunks} chunks)[/magenta]"
        )
        self.console.print(
            f"[magenta]   Date resources: {', '.join(date_resources)}[/magenta]"
        )

    def _run_parallel(self, pipeline: dlt.Pipeline, config: PipelineConfig) -> Any:
        """Run all resources in parallel (faster for small date ranges)."""
        source = self.get_source(config)
        return pipeline.run(source, loader_file_format="parquet")

    def _run_backfill(self, pipeline: dlt.Pipeline, config: PipelineConfig) -> Any:
        """Run chunked backfill with incremental writes."""
        resources_config = self.get_resources_config()
        non_date_resources = [r for r, is_date in resources_config.items() if not is_date]
        date_resources = [r for r, is_date in resources_config.items() if is_date]

        # Generate chunks
        if config.start_date and config.end_date:
            date_chunks = generate_date_chunks(
                config.start_date, config.end_date, chunk_size_days=config.chunk_days
            )
            use_date_mode = True
        else:
            days_chunks = generate_monthly_chunks(
                config.days, chunk_size_days=config.chunk_days
            )
            use_date_mode = False

        num_chunks = len(date_chunks if use_date_mode else days_chunks)
        all_load_infos = []

        # First, load non-date-based resources once
        if non_date_resources:
            self.console.print(
                f"\n[bold cyan]Loading reference data ({', '.join(non_date_resources)})...[/bold cyan]"
            )
            for resource_name in non_date_resources:
                self.console.print(f"   [cyan]{resource_name}...[/cyan]")
                source = self.get_source(config, resource_name=resource_name)
                load_info = pipeline.run(source, loader_file_format="parquet")
                all_load_infos.append(load_info)
                self.console.print(f"   [green]{resource_name} loaded[/green]")

        # Then load date-based resources in chunks
        if date_resources:
            self.console.print(
                f"\n[bold cyan]Loading date-based resources in {num_chunks} chunks...[/bold cyan]"
            )
            for chunk_idx in range(1, num_chunks + 1):
                if use_date_mode:
                    chunk_start_dt, chunk_end_dt = date_chunks[chunk_idx - 1]
                else:
                    start_days, end_days = days_chunks[chunk_idx - 1]
                    now = datetime.utcnow()
                    chunk_start_dt = now - timedelta(days=start_days)
                    chunk_end_dt = now - timedelta(days=end_days)

                self.console.print(
                    f"\n   [magenta]Chunk {chunk_idx}/{num_chunks}: "
                    f"{chunk_start_dt.date()} -> {chunk_end_dt.date()}[/magenta]"
                )

                for resource_name in date_resources:
                    self.console.print(f"      [cyan]{resource_name}...[/cyan]")
                    source = self.get_source(
                        config,
                        resource_name=resource_name,
                        start_date=chunk_start_dt,
                        end_date=chunk_end_dt,
                    )
                    load_info = pipeline.run(source, loader_file_format="parquet")
                    all_load_infos.append(load_info)

                self.console.print(f"   [green]Chunk {chunk_idx}/{num_chunks} saved[/green]")

        return all_load_infos[-1] if all_load_infos else None

    def _run_metrics(self) -> None:
        """Run metrics computation."""
        self.console.print("\n[cyan]Computing metrics...[/cyan]")
        try:
            self.compute_metrics()
        except Exception as e:
            self.console.print(f"[yellow]Failed to compute metrics: {e}[/yellow]")

    def _print_results(
        self, pipeline: dlt.Pipeline, load_info: Any, config: PipelineConfig
    ) -> None:
        """Print pipeline results to console."""
        if load_info:
            self.console.print(f"Loaded {len(load_info.load_packages)} packages")

        # Show schema
        self.console.print("\n[bold]Schema:[/bold]")
        try:
            for table_name in pipeline.default_schema.tables.keys():
                if not table_name.startswith("_dlt"):
                    self.console.print(f"  {table_name}")
        except Exception as e:
            self.console.print(f"  Schema available in destination (error: {e})")

    def _cleanup(self, pipeline: dlt.Pipeline) -> None:
        """Clean up resources after pipeline run."""
        self.console.print("[dim]Cleaning up connections...[/dim]")

        try:
            if hasattr(pipeline, "_destination_client"):
                pipeline._destination_client = None
            gc.collect()
            time.sleep(0.3)
        except Exception as e:
            self.logger.warning(f"Cleanup error (non-fatal): {e}")

        self.console.print("[green]Pipeline completed![/green]")
