# ETL Pipeline Builder

Build and extend ETL pipelines using DLT (data-load-tools) for loading data into warehouses.

## When Claude Activates This Skill

Claude automatically uses this skill when you ask to:

- Create a new ETL pipeline
- Add an API connector (Toast, Square, Stripe, etc.)
- Build spreadsheet/file ingestion (XLSX, CSV)
- Extend existing `etl/` pipelines with new sources
- Set up data extraction from third-party services

## What This Skill Does

### For New Projects

1. Sets up the core framework (`etl/core/`)
2. Creates the standard directory structure
3. Generates source, runner, and transform files

### For Existing Projects

1. Detects existing `etl/` structure
2. Adds new connectors following established patterns
3. Maintains consistency with existing code

## Directory Structure

```
etl/
├── core/                    # Shared abstractions
│   ├── pipeline.py         # BasePipelineRunner, PipelineConfig
│   ├── chunking.py         # Date range utilities
│   └── cli.py              # CLI helpers
│
├── sources/                 # Data extraction
│   ├── <provider>/         # API providers (toast/, square/)
│   │   ├── client.py       # API client
│   │   └── <entity>_source.py
│   └── spreadsheets/       # File-based sources
│       ├── core.py
│       └── templates/
│
├── runners/                 # Pipeline orchestration
│   └── <name>.py           # One per pipeline
│
└── transforms/              # Post-load computations
    └── compute_*.py
```

## Supported Warehouses

- **ClickHouse** - High-volume analytics
- **Snowflake** - Enterprise data warehouse
- **MotherDuck** - Serverless DuckDB
- **DuckDB** - Local development

The skill generates warehouse-agnostic source code and detects your warehouse configuration automatically.

## Quick Commands

```bash
# Run pipeline
uv run python -m etl.runners.<name> run

# Test with mock data
uv run python -m etl.runners.<name> test

# Dry run (DuckDB)
uv run python -m etl.runners.<name> run --dry-run

# Backfill historical data
uv run python -m etl.runners.<name> run --backfill --days 90

# Show configuration
uv run python -m etl.runners.<name> config
```

## Reference Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Entry point and routing logic |
| `etl-style-guide.md` | Naming conventions, patterns |
| `warehouse-modeling.md` | DDL patterns per warehouse |
| `playbook-api-connectors.md` | API integration guide |
| `playbook-spreadsheets.md` | Spreadsheet ingestion guide |
| `templates/` | Copy-paste-ready code |

## Example Usage

### Add Toast API Connector

```
"Add a Toast labor data connector that syncs employee time entries"
```

Claude will:
1. Create `etl/sources/toast/client.py` with auth and rate limiting
2. Create `etl/sources/toast/labor_source.py` with DLT resources
3. Create `etl/runners/toast_labor.py` with CLI
4. Provide sample queries and next steps

### Add Spreadsheet Ingestion

```
"Create an income statement ingestion pipeline for Excel files"
```

Claude will:
1. Create `etl/sources/spreadsheets/templates/income_statement.py`
2. Create `etl/runners/income_statement.py` with file input CLI
3. Add detection and preview commands

## Key Concepts

### DLT Resources

```python
@dlt.resource(name="orders", write_disposition="merge", primary_key="id")
def orders_resource(...):
    yield from fetch_orders(...)
```

### Incremental Loading

```python
modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
    "modified_date",
    initial_value=pendulum.now().subtract(days=7).isoformat()
)
```

### Backfill Chunking

Large date ranges are processed in chunks (default 30 days) for:
- API rate limit compliance
- Crash-safe incremental writes
- Memory efficiency
