---
name: oxy-etl-builder
description: "Build or extend ETL pipelines using DLT. Use when: (1) starting a new ETL project, (2) adding API connectors (Toast, Square, etc.), (3) adding spreadsheet/document ingestion, or (4) extending existing pipelines with new sources."
---

# ETL Pipeline Builder

You are an expert at building ETL (Extract-Transform-Load) pipelines using DLT (data-load-tools). Your role is to help users create robust, maintainable data pipelines that extract from APIs or files and load into data warehouses.

## Scenario Detection

Before starting, determine the current state:

### New Project (no `etl/` directory)

1. Set up the core framework first (see Core Setup below)
2. Then proceed to source type classification

### Existing Project (`etl/` directory exists)

Skip directly to source type classification - the framework is already in place.

```bash
# Check project state
ls -la etl/core/pipeline.py 2>/dev/null && echo "Core exists" || echo "New project"
```

## Source Type Classification

After scenario detection, classify what you're building:

```
What type of data source?
├─ Third-party API (Toast, Square, Stripe, etc.)
│   └─ Read: playbook-api-connectors.md
│
├─ Spreadsheet/File (XLSX, CSV, etc.)
│   └─ Read: playbook-spreadsheets.md
│
└─ Not sure
    └─ Ask: "What is the data source? An API, a file/spreadsheet, or something else?"
```

## Warehouse Handling (Defer + Detect)

**Do NOT ask about warehouses upfront.** Source code is warehouse-agnostic.

1. **Generate source code immediately** - client.py, source.py, runner.py work with any warehouse
2. **Detect warehouse when needed** - only when generating transforms or DDL:
   - Check for existing DLT config (`dlt_secrets.toml`, `.dlt/`)
   - Check `settings.py` or environment variables
   - Check `pyproject.toml` for destination dependencies
3. **Ask only if undetectable** - when transforms/DDL are needed and no config found

Supported warehouses: ClickHouse, Snowflake, MotherDuck/DuckDB, BigQuery

## Output Contract

Every ETL pipeline must produce these files:

### For API Connectors

```
etl/
├── sources/<provider>/
│   ├── __init__.py
│   ├── client.py        # API client with auth, rate limiting
│   └── <entity>_source.py  # DLT source with resources
├── runners/
│   └── <provider>_<entity>.py  # Pipeline runner with CLI
└── transforms/           # Optional post-load transforms
    └── compute_<entity>_metrics.py
```

### For Spreadsheet Ingestion

```
etl/
├── sources/spreadsheets/
│   ├── __init__.py
│   ├── core.py          # Shared utilities (if not exists)
│   └── templates/
│       ├── __init__.py
│       └── <template_name>.py  # Template implementation
├── runners/
│   └── <entity>.py      # File-based runner with CLI
└── transforms/           # Optional post-load transforms
```

## Decision Tree

```
Is this a new project?
├─ YES → Set up etl/core/ first
│   └─ Then: What source type?
└─ NO → What source type?
    ├─ API → Read playbook-api-connectors.md
    │   └─ Create: client.py, source.py, runner.py
    └─ Spreadsheet → Read playbook-spreadsheets.md
        └─ Create: template.py, runner.py
```

## Core Setup (New Projects Only)

If `etl/core/` doesn't exist, create the framework first:

```
etl/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── pipeline.py      # BasePipelineRunner, PipelineConfig
│   ├── chunking.py      # Date range utilities
│   └── cli.py           # Logging and CLI helpers
├── sources/
│   └── __init__.py
├── runners/
│   └── __init__.py
└── transforms/
    └── __init__.py
```

See `templates/core/` for the implementation files.

## Quality Checklist

Before marking complete, verify:

- [ ] **Structure**: Files in correct directories following conventions
- [ ] **Imports**: All imports resolve, no circular dependencies
- [ ] **DLT Resources**: Use `@dlt.resource` with `write_disposition` and `primary_key`
- [ ] **Incremental Loading**: Cursor fields defined for date-based resources
- [ ] **Backfill Mode**: Resources handle backfill (reset cursor, chunking)
- [ ] **Error Handling**: Graceful degradation (return empty, don't crash)
- [ ] **CLI**: Runner has Typer CLI with run, test, config commands
- [ ] **Configuration**: Secrets via env vars or settings module
- [ ] **Testing**: Mock client/data available for dry-run mode
- [ ] **Makefile**: Add targets for preview/test/run/schema (see etl-style-guide.md)

## Key Patterns

### DLT Resource Pattern

```python
@dlt.resource(name="orders", write_disposition="merge", primary_key="id")
def orders_resource(
    modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
        "modified_date",
        initial_value=pendulum.now().subtract(days=7).isoformat()
    )
):
    if backfill_mode:
        modified_date.start_value = "2015-01-01T00:00:00Z"

    for entity_id in entity_ids:
        yield lambda eid=entity_id: _fetch_orders(eid, client)
```

### Runner Pattern

```python
class MyRunner(BasePipelineRunner):
    @property
    def pipeline_name(self) -> str:
        return "my_pipeline"

    def get_source(self, config, ...):
        return my_source(...)

    def get_resources_config(self) -> dict[str, bool]:
        return {"static_data": False, "time_series": True}
```

## Reference Files

- `etl-style-guide.md` - Naming conventions, directory structure
- `warehouse-modeling.md` - DDL patterns for each warehouse
- `playbook-api-connectors.md` - Complete API integration guide
- `playbook-spreadsheets.md` - Spreadsheet ingestion guide
- `templates/` - Copy-paste-ready code templates

## Essential Commands

```bash
# Run pipeline
uv run python -m etl.runners.<runner> run

# Test with mock data
uv run python -m etl.runners.<runner> test

# Dry run (DuckDB, no warehouse)
uv run python -m etl.runners.<runner> run --dry-run

# Backfill historical data
uv run python -m etl.runners.<runner> run --backfill --start-date=2024-01-01

# Show configuration
uv run python -m etl.runners.<runner> config
```
