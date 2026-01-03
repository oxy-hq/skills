# Warehouse Modeling Guide

This guide covers data warehouse patterns for ETL destinations. DLT abstracts most details, but understanding warehouse-specific patterns helps with transforms and optimization.

## DLT Destination Abstraction

DLT handles schema creation and data loading automatically. Key settings:

### Write Dispositions

```python
@dlt.resource(write_disposition="merge")  # Upsert with primary_key
@dlt.resource(write_disposition="append")  # Insert only
@dlt.resource(write_disposition="replace") # Truncate and reload
```

| Disposition | Use Case | Requires |
|-------------|----------|----------|
| `merge` | Transaction data, upserts | `primary_key` |
| `append` | Event logs, immutable data | Nothing |
| `replace` | Dimension tables, full refresh | Nothing |

### Primary Keys

```python
@dlt.resource(primary_key="id")           # Single key
@dlt.resource(primary_key=["id", "date"]) # Composite key
```

## ETL Metadata Columns

Add these to every table for data lineage (warehouse-agnostic):

| Column | Type | Description |
|--------|------|-------------|
| `_etl_source` | String | Source identifier (e.g., "toast_api") |
| `_etl_extracted_at` | Timestamp | When data was extracted |
| `_etl_pipeline_run_id` | String | Unique run identifier |

```python
def add_etl_metadata(record: dict) -> dict:
    return {
        **record,
        "_etl_source": "toast_api",
        "_etl_extracted_at": pendulum.now().isoformat(),
        "_etl_pipeline_run_id": str(uuid.uuid4()),
    }
```

## Detecting Warehouse

Before generating warehouse-specific code, detect from existing config:

```python
def detect_warehouse():
    """Detect configured warehouse from project files."""

    # Check DLT secrets
    if Path(".dlt/secrets.toml").exists():
        secrets = toml.load(".dlt/secrets.toml")
        if "clickhouse" in secrets.get("destination", {}):
            return "clickhouse"
        if "snowflake" in secrets.get("destination", {}):
            return "snowflake"
        if "motherduck" in secrets.get("destination", {}):
            return "motherduck"

    # Check environment variables
    if os.getenv("CLICKHOUSE_HOST"):
        return "clickhouse"
    if os.getenv("SNOWFLAKE_ACCOUNT"):
        return "snowflake"
    if os.getenv("MOTHERDUCK_TOKEN"):
        return "motherduck"

    # Check pyproject.toml dependencies
    if Path("pyproject.toml").exists():
        pyproject = toml.load("pyproject.toml")
        deps = pyproject.get("project", {}).get("dependencies", [])
        if any("clickhouse" in d for d in deps):
            return "clickhouse"
        if any("snowflake" in d for d in deps):
            return "snowflake"

    return None  # Unknown, ask user
```

---

## ClickHouse

### Connection Setup

```python
# DLT configuration
dlt.pipeline(
    destination="clickhouse",
    credentials={
        "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
        "port": int(os.getenv("CLICKHOUSE_PORT", 8123)),
        "database": os.getenv("CLICKHOUSE_DATABASE", "default"),
        "username": os.getenv("CLICKHOUSE_USER", "default"),
        "password": os.getenv("CLICKHOUSE_PASSWORD", ""),
    }
)
```

### Table Engine Selection

| Engine | Use Case | Features |
|--------|----------|----------|
| `ReplacingMergeTree` | Upsert semantics | Deduplication on ORDER BY |
| `MergeTree` | Append-only logs | Fast writes |
| `SummingMergeTree` | Pre-aggregated metrics | Auto-sum on merge |

DLT uses `ReplacingMergeTree` by default for `write_disposition="merge"`.

### ORDER BY Selection

```sql
-- Transaction data: unique ID + date
ORDER BY (id, created_at)

-- Time series: date first for partitioning
ORDER BY (business_date, restaurant_id, id)

-- Dimension tables: natural key
ORDER BY (restaurant_id)
```

### PARTITION BY Patterns

```sql
-- Monthly partitions (most common)
PARTITION BY toYYYYMM(business_date)

-- Daily partitions (high volume)
PARTITION BY toDate(created_at)

-- No partitioning (small tables)
-- Omit PARTITION BY clause
```

### Deduplication

ClickHouse deduplicates asynchronously. For consistent reads:

```sql
-- Use FINAL for deduped results
SELECT * FROM orders FINAL WHERE business_date = '2024-01-15';

-- Or optimize manually (heavy operation)
OPTIMIZE TABLE orders FINAL;
```

### Transform Example (ClickHouse)

```python
def compute_daily_metrics(client, start_date=None, end_date=None):
    """Compute daily metrics in ClickHouse."""

    # Delete existing data for date range (idempotent)
    if start_date and end_date:
        client.execute(f"""
            ALTER TABLE restaurant_analytics.daily_metrics
            DELETE WHERE business_date BETWEEN '{start_date}' AND '{end_date}'
        """)

    # Insert aggregated data
    client.execute("""
        INSERT INTO restaurant_analytics.daily_metrics
        SELECT
            business_date,
            restaurant_id,
            COUNT(*) as order_count,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_order_value,
            now() as _etl_computed_at
        FROM restaurant_analytics.orders FINAL
        WHERE business_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY business_date, restaurant_id
    """)
```

---

## Snowflake

### Connection Setup

```python
# DLT configuration
dlt.pipeline(
    destination="snowflake",
    credentials={
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    }
)
```

### Clustering Keys

Snowflake auto-manages storage but benefits from clustering hints:

```sql
-- Add clustering for frequently filtered columns
ALTER TABLE orders CLUSTER BY (business_date, restaurant_id);
```

### Time Travel

Snowflake keeps history for recovery:

```sql
-- Query historical data (within retention period)
SELECT * FROM orders AT(TIMESTAMP => '2024-01-15 10:00:00'::TIMESTAMP);

-- Restore from history
CREATE TABLE orders_restored CLONE orders AT(TIMESTAMP => '...');
```

### Transform Example (Snowflake)

```python
def compute_daily_metrics(connection, start_date, end_date):
    """Compute daily metrics in Snowflake."""

    cursor = connection.cursor()

    # MERGE for upsert semantics
    cursor.execute(f"""
        MERGE INTO daily_metrics AS target
        USING (
            SELECT
                business_date,
                restaurant_id,
                COUNT(*) as order_count,
                SUM(amount) as total_revenue,
                AVG(amount) as avg_order_value,
                CURRENT_TIMESTAMP() as _etl_computed_at
            FROM orders
            WHERE business_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY business_date, restaurant_id
        ) AS source
        ON target.business_date = source.business_date
           AND target.restaurant_id = source.restaurant_id
        WHEN MATCHED THEN UPDATE SET
            order_count = source.order_count,
            total_revenue = source.total_revenue,
            avg_order_value = source.avg_order_value,
            _etl_computed_at = source._etl_computed_at
        WHEN NOT MATCHED THEN INSERT (
            business_date, restaurant_id, order_count,
            total_revenue, avg_order_value, _etl_computed_at
        ) VALUES (
            source.business_date, source.restaurant_id, source.order_count,
            source.total_revenue, source.avg_order_value, source._etl_computed_at
        )
    """)
```

---

## MotherDuck / DuckDB

### Connection Setup

```python
# Local DuckDB (development)
dlt.pipeline(
    destination="duckdb",
    credentials="./data/analytics.duckdb"
)

# MotherDuck (production)
dlt.pipeline(
    destination="motherduck",
    credentials={
        "database": "my_database",
        "token": os.getenv("MOTHERDUCK_TOKEN"),
    }
)
```

### Key Characteristics

- **No explicit partitioning**: DuckDB handles this internally
- **Columnar storage**: Excellent for analytics queries
- **Zero config**: Great for development and testing
- **MotherDuck**: Serverless cloud hosting for DuckDB

### Transform Example (DuckDB)

```python
def compute_daily_metrics(conn, start_date, end_date):
    """Compute daily metrics in DuckDB."""

    # DuckDB supports INSERT OR REPLACE
    conn.execute(f"""
        INSERT OR REPLACE INTO daily_metrics
        SELECT
            business_date,
            restaurant_id,
            COUNT(*) as order_count,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_order_value,
            NOW() as _etl_computed_at
        FROM orders
        WHERE business_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY business_date, restaurant_id
    """)
```

---

## Choosing a Warehouse

| Factor | ClickHouse | Snowflake | MotherDuck |
|--------|------------|-----------|------------|
| **Volume** | High (billions) | High | Medium (millions) |
| **Real-time** | Excellent | Good | Good |
| **Cost** | Self-hosted or Cloud | Pay-per-query | Serverless, low |
| **Setup** | Moderate | Easy | Very easy |
| **SQL Dialect** | ClickHouse SQL | ANSI SQL | DuckDB/PostgreSQL |
| **Best For** | Real-time analytics | Enterprise, complex ETL | Startups, prototypes |

### Decision Guide

```
What's your scale?
├─ Billions of rows, real-time queries → ClickHouse
├─ Enterprise needs, complex transforms → Snowflake
└─ Smaller scale, simplicity preferred → MotherDuck

What's your budget?
├─ Self-hosted preferred → ClickHouse
├─ Pay-per-query OK → Snowflake
└─ Cost-sensitive → MotherDuck
```

## Cross-Warehouse SQL Differences

| Operation | ClickHouse | Snowflake | DuckDB |
|-----------|------------|-----------|--------|
| Current time | `now()` | `CURRENT_TIMESTAMP()` | `NOW()` |
| Date extract | `toYYYYMM(date)` | `DATE_TRUNC('month', date)` | `DATE_TRUNC('month', date)` |
| Upsert | ReplacingMergeTree | MERGE | INSERT OR REPLACE |
| String concat | `concat(a, b)` | `a \|\| b` | `a \|\| b` |

Keep transforms in separate files per warehouse when SQL differs significantly.
