# Oxy Semantic Layer Quick Reference

## Commands

```bash
# 1. Generate database schemas
oxy sync

# 2. Validate all YAML configs
oxy validate

# 3. Build/compile full semantic layer
oxy build

# 4. Start semantic engine
oxy semantic-engine --dev-mode
```

## File Locations

- Views: `semantics/views/*.view.yml`
- Topics: `semantics/topics/*.topic.yml`
- Database schemas: `.databases/`
- Configuration: `config.yml`

## View File Checklist

```yaml
✓ name: string
✓ description: string
✓ datasource: string (from config.yml)
✓ table: "schema.table"
✓ entities: [...]
  ✓ Primary entity (required)
  ✓ Foreign entities (optional)
✓ dimensions: [...]
  ✓ Entity key dimensions
  ✓ Regular attributes
  ✓ Calculated fields
✓ measures: [...]
  ✓ Basic aggregations
  ✓ Filtered measures
  ✓ Custom calculations
```

## Entity Rules

1. **One primary entity per view** (required)
2. **Entity keys reference dimension names**, not columns
3. **Use same entity names across views** to enable joins
4. **Foreign entities** create relationships to other views

## Dimension Types

| Type | Example | Common Use |
|------|---------|------------|
| `string` | "active" | Categories, IDs, text |
| `number` | 42, 3.14 | Counts, amounts, metrics |
| `date` | "2024-01-01" | Dates without time |
| `datetime` | "2024-01-01 10:30:00" | Timestamps |
| `boolean` | true, false | Flags, indicators |

## Measure Types

| Type | Description | Requires expr |
|------|-------------|---------------|
| `count` | Count rows | No |
| `count_distinct` | Count unique values | Yes |
| `sum` | Sum values | Yes |
| `average` | Average values | Yes |
| `median` | Median value | Yes |
| `min` | Minimum value | Yes |
| `max` | Maximum value | Yes |
| `custom` | Custom SQL expression | Yes |

## Common Patterns

### Date Parts

```yaml
- name: year
  type: number
  expr: "EXTRACT(YEAR FROM date_column)"
```

### Categorical Ranges

```yaml
- name: price_tier
  type: string
  expr: "CASE WHEN price < 100 THEN 'Low' WHEN price < 500 THEN 'Medium' ELSE 'High' END"
```

### Filtered Measures

```yaml
- name: active_count
  type: count
  filters:
    - expr: "{{status}} = 'active'"

- name: high_value_revenue
  type: sum
  expr: amount
  filters:
    - expr: "{{amount}} >= 1000"
```

### Correlations

```yaml
- name: temp_sales_correlation
  type: custom
  expr: "CORR(temperature, sales)"
```

## Topic Default Filters

```yaml
default_filters:
  # Single value
  - field: table.column
    eq:
      value: "active"

  # Array values
  - field: table.status
    not_in:
      values: ["cancelled", "test"]

  # Date range
  - field: table.date
    in_date_range:
      from: "90 days ago"
      to: "now"
```

## Validation Workflow

1. Create/edit view files
2. Create/edit topic files
3. Run `oxy validate` to validate all YAML configs
4. Run `oxy build` to build/compile the full semantic layer
5. Fix any errors
6. Test with `oxy semantic-engine --dev-mode`
7. Query using natural language

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Entity key not found" | Key references column not dimension | Change entity key to dimension name |
| "View not found" | File not in right location | Move to `semantics/views/` |
| "Invalid SQL" | Bad expr syntax | Check column names and SQL syntax |
| "Cannot join" | Entity names don't match | Use identical entity names |
| `TYPE_MISMATCH` at filter | Date dim declared `type: number`/`string` over a non-Date column | Sample one row, switch to `type: date`/`datetime`, wrap `expr` with the cast for your warehouse |

## Date Column Casts

Sample the column first (`SELECT <col> FROM <table> LIMIT 1`) — stored format
varies. Then wrap `expr:` for the dimension:

| Warehouse  | Cast functions                                                                                |
| ---------- | --------------------------------------------------------------------------------------------- |
| ClickHouse | `toDate(<col>)`, `toDateTime(<col>)`, `parseDateTimeBestEffort(<col>)`, `toDate(toString(<col>))` |
| BigQuery   | `CAST(<col> AS DATE)`, `PARSE_DATE('<fmt>', <col>)`, `TIMESTAMP_SECONDS(<col>)`               |
| Snowflake  | `TO_DATE(<col>[, '<fmt>'])`, `TO_TIMESTAMP(<col>)`, `TRY_TO_DATE(<col>)`                       |
| Postgres   | `(<col>)::date`, `to_date(<col>, '<fmt>')`, `to_timestamp(<col>, '<fmt>')`                     |
| DuckDB     | `CAST(<col> AS DATE)`, `strptime(<col>, '<fmt>')`, `epoch_ms(<col>)`                           |

Already-typed `Date` / `DateTime` / `TIMESTAMP` columns need no cast —
`expr: <col>` is enough.

## Best Practices

1. **One topic per view** to avoid duplication
2. **Add synonyms** for natural language queries
3. **Include samples** for categorical dimensions — `samples` is always a
   list of strings, even for `boolean` and `number` dimensions. Use
   `samples: ["true", "false"]` and `samples: ["129.99", "89.50"]`, never
   bare literals (they fail YAML deserialization)
4. **Use descriptive names** (snake_case)
5. **Write business-friendly descriptions**
6. **Test incrementally** after each change
