# ETL Style Guide

This guide defines naming conventions, directory structure, and coding patterns for ETL pipelines.

## Directory Structure

```
etl/
├── __init__.py
├── core/                    # Shared abstractions
│   ├── __init__.py
│   ├── pipeline.py         # BasePipelineRunner, PipelineConfig
│   ├── chunking.py         # Date range chunking utilities
│   └── cli.py              # Logging, date parsing helpers
│
├── sources/                 # Data extraction
│   ├── __init__.py
│   ├── <provider>/         # One directory per API provider
│   │   ├── __init__.py
│   │   ├── auth.py         # Optional: auth helpers
│   │   ├── client.py       # API client
│   │   ├── rate_limiter.py # Optional: rate limiting
│   │   └── <entity>_source.py  # DLT sources
│   │
│   └── spreadsheets/       # File-based sources
│       ├── __init__.py
│       ├── core.py         # Shared utilities
│       └── templates/      # Template implementations
│           ├── __init__.py
│           └── <template>.py
│
├── runners/                 # Pipeline orchestration
│   ├── __init__.py
│   └── <provider>_<entity>.py  # One runner per pipeline
│
└── transforms/              # Post-load computations
    ├── __init__.py
    └── compute_<entity>_metrics.py
```

## Naming Conventions

### Directories

| Type | Convention | Examples |
|------|------------|----------|
| Provider | lowercase, single word | `toast/`, `square/`, `stripe/` |
| Template | lowercase, snake_case | `templates/income_statement.py` |

### Files

| Type | Pattern | Examples |
|------|---------|----------|
| Source | `<entity>_source.py` | `labor_source.py`, `sales_source.py` |
| Runner | `<provider>_<entity>.py` | `toast_labor.py`, `income_statement.py` |
| Transform | `compute_<entity>_metrics.py` | `compute_labor_metrics.py` |
| Client | `client.py` | Always `client.py` in provider dir |

### Classes

| Type | Pattern | Examples |
|------|---------|----------|
| Runner | `<Provider><Entity>Runner` | `ToastLaborRunner`, `IncomeStatementRunner` |
| Client | `<Provider>Client` | `ToastClient`, `SquareClient` |
| Template | `<Name>Template` | `IncomeStatementTemplate` |

### DLT Names

| Type | Pattern | Examples |
|------|---------|----------|
| Pipeline | `<provider>_<entity>_pipeline` | `toast_labor_pipeline` |
| Dataset | `<domain>_analytics` | `restaurant_analytics` |
| Source | `<provider>_<entity>` | `toast_labor`, `income_statement` |
| Resource | lowercase, plural | `orders`, `employees`, `time_entries` |

## Configuration Patterns

### Environment Variables (Recommended for Secrets)

```python
import os

# API credentials
CLIENT_ID = os.getenv("TOAST_CLIENT_ID")
CLIENT_SECRET = os.getenv("TOAST_CLIENT_SECRET")

# Database connection
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
```

### Settings Module (Alternative)

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API
    toast_client_id: str
    toast_client_secret: str

    # Database
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123

    class Config:
        env_file = ".env"

settings = Settings()
```

Usage:
```python
from config.settings import settings

client = ToastClient(
    client_id=settings.toast_client_id,
    client_secret=settings.toast_client_secret
)
```

### Choose Based On

- **Environment variables**: Simpler, works everywhere, good for containers
- **Settings module**: Better validation, IDE autocomplete, centralized config

## Error Handling

### API Errors: Return Empty, Don't Crash

```python
def get_orders(self, start_date, end_date):
    """Fetch orders, returning empty list on failure."""
    try:
        response = self._make_request(
            "GET", "/orders",
            params={"startDate": start_date, "endDate": end_date}
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch orders: {e}")
        return []  # Graceful degradation
```

### Rate Limiting: Exponential Backoff

```python
def _make_request(self, method, endpoint, **kwargs):
    for attempt in range(self.max_retries):
        response = self.session.request(method, url, **kwargs)

        if response.status_code == 429:
            wait_time = 2 ** attempt * self.base_delay
            logger.warning(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        return response

    raise Exception(f"Max retries exceeded for {endpoint}")
```

### Connection Cleanup

```python
def run(self):
    try:
        # Pipeline execution
        result = pipeline.run(source)
    finally:
        # Always cleanup
        if hasattr(self, 'client'):
            self.client.close()
```

## Testing Patterns

### Mock Client

```python
class MockToastClient:
    """Mock client for testing without real API calls."""

    def __init__(self, *args, **kwargs):
        self.calls = []

    def get_orders(self, start_date, end_date):
        self.calls.append(("get_orders", start_date, end_date))
        return self._load_fixture("orders.json")

    def _load_fixture(self, name):
        fixture_path = Path(__file__).parent / "fixtures" / name
        return json.loads(fixture_path.read_text())
```

### Dry Run Mode

```python
def create_pipeline(self, config):
    if config.dry_run:
        # Use local DuckDB for testing
        return dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination="duckdb",
            dataset_name=self.dataset_name,
        )
    else:
        # Use production warehouse
        return dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination="clickhouse",
            dataset_name=self.dataset_name,
        )
```

### Run Modes Matrix

| Mode | API | Destination | Use Case |
|------|-----|-------------|----------|
| `--dry-run` | Mock | DuckDB | Quick validation |
| `--mock-api` | Mock | Production | Test loading logic |
| `--real-api --dry-run` | Real | DuckDB | Test API without loading |
| (default) | Real | Production | Production run |

## Incremental Loading

### Cursor Field Selection

| Data Type | Cursor Field | Example |
|-----------|--------------|---------|
| Transactions | `modified_date`, `updated_at` | Orders, payments |
| Time series | `business_date`, `event_date` | Time entries, shifts |
| Append-only | `created_at` | Logs, events |

### Reset Cursor for Backfill

```python
@dlt.resource(name="orders", write_disposition="merge", primary_key="id")
def orders_resource(
    modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
        "modified_date",
        initial_value=pendulum.now().subtract(days=7).isoformat()
    )
):
    # CRITICAL: Reset cursor for backfill mode
    if backfill_mode:
        modified_date.start_value = "2015-01-01T00:00:00Z"

    yield from _fetch_all_orders(modified_date.start_value)
```

## Data Provenance

Every record should include ETL metadata:

```python
def _add_etl_metadata(record: dict, source_name: str, run_id: str) -> dict:
    """Add ETL provenance fields to a record."""
    return {
        **record,
        "_etl_source": source_name,
        "_etl_extracted_at": pendulum.now().isoformat(),
        "_etl_pipeline_run_id": run_id,
    }
```

These fields enable:
- Debugging data lineage
- Identifying stale data
- Replaying specific pipeline runs

## Import Organization

```python
# Standard library
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

# Third-party
import dlt
import pendulum
import requests
from rich.console import Console

# Local - core
from etl.core.pipeline import BasePipelineRunner, PipelineConfig
from etl.core.chunking import generate_date_chunks

# Local - sources
from etl.sources.toast.client import ToastClient
```

## CLI Pattern

```python
import typer
from rich.console import Console

app = typer.Typer(help="Toast Labor ETL Pipeline")
console = Console()

@app.command()
def run(
    dry_run: bool = typer.Option(False, "--dry-run", help="Use DuckDB instead of production"),
    days: int = typer.Option(7, "--days", help="Days of data to fetch"),
    backfill: bool = typer.Option(False, "--backfill", help="Enable backfill mode"),
    start_date: str = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
):
    """Run the ETL pipeline."""
    config = PipelineConfig(
        dry_run=dry_run,
        days=days,
        backfill=backfill,
        start_date=parse_date(start_date) if start_date else None,
    )
    runner = ToastLaborRunner()
    runner.run(config)

@app.command()
def test():
    """Run with mock data for testing."""
    config = PipelineConfig(dry_run=True, mock_api=True)
    runner = ToastLaborRunner()
    runner.run(config)

@app.command()
def config():
    """Show current configuration."""
    console.print("[bold]Current Configuration[/bold]")
    console.print(f"  Restaurant IDs: {RESTAURANT_IDS}")
    console.print(f"  Days: {DEFAULT_DAYS}")

if __name__ == "__main__":
    app()
```
