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
│   │   ├── <entity>_source.py  # DLT sources
│   │   └── scripts/        # Optional: browser/ad-hoc scripts
│   │       ├── README.md   # Usage documentation
│   │       └── <name>_scraper.js  # Browser console scripts
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

## Makefile Integration

After creating a new pipeline, **always add Makefile targets** for common operations. This provides a consistent interface for running pipelines.

### Required Targets

For each pipeline, add these targets to the project's `Makefile`:

```makefile
# Testing & Pipeline - <Provider/Entity>
preview-<name>: ## Preview data without loading
	uv run python -m etl.runners.<runner> preview --file <default_file>

test-<name>: ## Test pipeline with DuckDB (dry-run)
	uv run python -m etl.runners.<runner> test --file <default_file>

run-<name>: ## Run pipeline to load data into warehouse
	uv run python -m etl.runners.<runner> run --file <default_file>

schema-<name>: ## Show data schema
	uv run python -m etl.runners.<runner> schema
```

### Naming Convention

| Pipeline Type | Target Prefix | Examples |
|--------------|---------------|----------|
| API connector | `<provider>-<entity>` | `toast-labor`, `toast-sales` |
| File/CSV | `<source>` | `olo`, `income-statement` |

### Example: File-Based Pipeline

```makefile
# Testing & Pipeline - OLO Weekly Orders
preview-olo: ## Preview OLO CSV data without loading
	uv run python -m etl.runners.olo_weekly_orders preview --file data/olo_weekly_online_orders_by_provider.csv

test-olo: ## Test OLO pipeline with DuckDB (dry-run)
	uv run python -m etl.runners.olo_weekly_orders test --file data/olo_weekly_online_orders_by_provider.csv

run-olo: ## Run OLO pipeline to load data into ClickHouse
	uv run python -m etl.runners.olo_weekly_orders run --file data/olo_weekly_online_orders_by_provider.csv

schema-olo: ## Show OLO weekly orders data schema
	uv run python -m etl.runners.olo_weekly_orders schema
```

### Example: API-Based Pipeline

```makefile
# Testing & Pipeline - Toast Labor
test-toast-labor: ## Run Toast labor pipeline with mock data
	uv run python -m etl.runners.toast_labor test

run-toast-labor: ## Run Toast labor pipeline with real data
	uv run python -m etl.runners.toast_labor run

local-toast-labor: ## Test with real API + local DuckDB
	uv run python -m etl.runners.toast_labor run --dry-run --real-api

config-toast-labor: ## Show pipeline configuration
	uv run python -m etl.runners.toast_labor config

schema-toast-labor: ## Show data schema
	uv run python -m etl.runners.toast_labor schema
```

### Checklist

When adding a new pipeline, ensure:

- [ ] All common operations have Makefile targets
- [ ] Targets follow naming convention (`<source>-<entity>` or `<source>`)
- [ ] Each target has a `## description` comment for `make help`
- [ ] Default file paths are set for file-based pipelines
- [ ] Add to `.PHONY` if needed

## Browser Scripts (Ad-hoc Data Extraction)

When a data source doesn't provide an API but exposes data in web UIs (charts, tables, dashboards), use browser console scripts to extract it.

### Location

```
etl/sources/<provider>/scripts/
├── README.md              # Usage documentation
├── <chart>_scraper.js     # Highcharts, Chart.js extractors
└── <table>_extractor.js   # HTML table extractors
```

### Naming

| Type | Pattern | Examples |
|------|---------|----------|
| Chart scraper | `<chart_type>_scraper.js` | `highcharts_scraper.js` |
| Table extractor | `<page>_extractor.js` | `orders_table_extractor.js` |
| General | `<purpose>.js` | `export_helper.js` |

### Script Structure

```javascript
/**
 * <Provider> <Page> - <Chart/Table> Scraper
 * ==========================================
 *
 * <Description of what this extracts>
 *
 * Usage:
 *   1. Navigate to <specific page URL or path>
 *   2. Ensure <element> is fully rendered
 *   3. Open DevTools Console (F12)
 *   4. Paste this script and press Enter
 *   5. CSV copied to clipboard
 *   6. Save to data/<filename>.csv
 *
 * Expected output format:
 *   <column1>,<column2>,<column3>
 *   <example row>
 *
 * Then run:
 *   <make target or pipeline command>
 */

// Extraction logic...

// Always end with helpful console output
copy(csv);
console.log(`Copied ${rows.length} rows to clipboard as CSV.`);
console.log("Next: save to data/<name>.csv and run: make run-<target>");
```

### Workflow

```
Browser UI → Browser Script → CSV → data/ → DLT Source → Warehouse
             (scripts/)              dir    (<entity>_source.py)
```

### Best Practices

1. **Match output to DLT source input**: Column names should match what `<entity>_source.py` expects
2. **Include validation**: Check elements exist before extracting, throw clear errors
3. **Log row counts**: Help user verify extraction worked
4. **Document target page**: Pages change; note the URL/path and UI elements targeted
5. **Keep scripts self-contained**: No external dependencies, paste-and-run

### When to Use Browser Scripts

| Scenario | Approach |
|----------|----------|
| API available | Use API client (`client.py`) |
| Bulk export available | Use file-based source (`<entity>_source.py`) |
| Only web UI with charts/tables | Browser script → CSV → file source |
| One-time extraction | Browser script is fine |
| Recurring extraction | Consider if browser automation (Playwright) is worth it |

### README Template

Each `scripts/` directory should have a README.md:

```markdown
# <Provider> Browser Scripts

Ad-hoc scripts for extracting data from <Provider> web interfaces.

## Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `<name>.js` | <description> | CSV (clipboard) |

## Usage

1. Navigate to <page>
2. Open DevTools Console
3. Paste script, press Enter
4. Save clipboard to `data/<name>.csv`
5. Run: `make run-<target>`
```
