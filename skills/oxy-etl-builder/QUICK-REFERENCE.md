# ETL Builder Quick Reference

## Decision Matrix

| Need | Use |
|------|-----|
| Third-party API data | `playbook-api-connectors.md` |
| Spreadsheet/file data | `playbook-spreadsheets.md` |
| New project setup | `templates/core/` |
| Warehouse DDL | `warehouse-modeling.md` |

## File Naming

| Type | Pattern | Example |
|------|---------|---------|
| Client | `client.py` | `etl/sources/toast/client.py` |
| Source | `<entity>_source.py` | `labor_source.py` |
| Runner | `<provider>_<entity>.py` | `toast_labor.py` |
| Transform | `compute_<entity>.py` | `compute_labor_metrics.py` |

## DLT Decorators

```python
# Upsert (update or insert)
@dlt.resource(write_disposition="merge", primary_key="id")

# Append only
@dlt.resource(write_disposition="append")

# Full replace
@dlt.resource(write_disposition="replace")

# Parallel execution
@dlt.resource(parallelized=True)
```

## Incremental Loading

```python
# Define cursor
modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
    "modified_date",  # Field in data
    initial_value="2024-01-01T00:00:00Z"
)

# Reset for backfill
if backfill_mode:
    modified_date.start_value = "2015-01-01T00:00:00Z"
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Use DuckDB instead of production |
| `--mock-api` | Use mock API responses |
| `--backfill` | Enable chunked backfill |
| `--days N` | Days of data to fetch |
| `--start-date` | Explicit start (YYYY-MM-DD) |
| `--end-date` | Explicit end (YYYY-MM-DD) |
| `--chunk-days` | Days per backfill chunk |

## Resources Config

```python
def get_resources_config(self) -> dict[str, bool]:
    return {
        "entities": False,    # Static, load once
        "orders": True,       # Time-series, chunked
    }
```

## Warehouse Detection

| Environment Variable | Warehouse |
|---------------------|-----------|
| `CLICKHOUSE_HOST` | ClickHouse |
| `SNOWFLAKE_ACCOUNT` | Snowflake |
| `MOTHERDUCK_TOKEN` | MotherDuck |
| (none) | DuckDB (local) |

## ETL Metadata Fields

```python
{
    "_etl_source": "toast_api",
    "_etl_extracted_at": "2024-01-15T10:30:00Z",
    "_etl_pipeline_run_id": "abc123",
}
```

## Error Handling

```python
# API errors: return empty, don't crash
try:
    return response.json()
except Exception as e:
    logger.error(f"Failed: {e}")
    return []  # Graceful degradation
```

## Rate Limiting

```python
# Simple delay
time.sleep(0.1)

# Exponential backoff on 429
wait_time = 2 ** attempt
time.sleep(wait_time)
```

## Common Patterns

### Pagination (cursor)
```python
cursor = None
while True:
    data = fetch(cursor=cursor)
    yield from data["items"]
    cursor = data.get("next_cursor")
    if not cursor:
        break
```

### Flatten nested data
```python
for order in orders:
    for item in order.get("items", []):
        yield {"order_id": order["id"], **item}
```

### Template detection
```python
def detect(cls, workbook) -> float:
    # Return 0.0-1.0 confidence
    return 0.8 if matches else 0.0
```

## Templates

| File | Use For |
|------|---------|
| `pipeline-template.py` | BasePipelineRunner setup |
| `api-client-template.py` | API client with auth |
| `api-source-template.py` | DLT source for APIs |
| `runner-template.py` | Pipeline runner with CLI |
| `spreadsheet-template-template.py` | File parser |
| `spreadsheet-source-template.py` | DLT source for files |
