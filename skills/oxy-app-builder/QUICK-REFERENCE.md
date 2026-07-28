# Oxy App Quick Reference

Schema cheat sheet and canonical snippets for `*.app.yml` files.

> **Two app models.** This reference covers the declarative `*.app.yml` app
> (tasks + displays, rendered by `oxy serve --enterprise`). The other model is a
> **custom-code (React/Vite) app** deployed with `oxy publish` and identified by
> an **`oxy-app.json`** manifest at the app root — see
> `SKILL.md` → "Deploying custom-code apps (oxy-app.json)". `oxy-app.json` is the
> deploy manifest, not an alternative to `*.app.yml`.

## Top-Level Structure

```yaml
name: app_name                # Optional: snake_case identifier
description: |                # Optional: multi-line description
  What this app does

tasks:                        # REQUIRED: min 1 task
  - name: task_name
    type: execute_sql
    # ... task config

display:                      # REQUIRED: min 1 display
  - type: table
    data: task_name
```

## Task Types

### execute_sql

```yaml
- name: task_name
  type: execute_sql
  database: clickhouse        # clickhouse | postgres | bigquery | local
  mode: client                # Optional: client (default) | server. See "Task mode" below.
  sql_query: |                # Inline SQL — may contain {{ controls.x }} Jinja
    SELECT * FROM table
```

Or with file reference:
```yaml
- name: task_name
  type: execute_sql
  database: clickhouse
  sql_file: path/to/query.sql
```

### workflow

```yaml
- name: task_name
  type: workflow
  src: workflows/my_workflow.workflow.yml
  variables:                  # Optional: pass variables
    param1: value1
    param2: value2
```

Output reference: `workflow_task.inner_task_name`

### semantic_query

```yaml
- name: task_name
  type: semantic_query
  topic: topic_name
  dimensions:
    - view_name.dimension
  measures:
    - view_name.measure
  filters:                    # Optional
    - field: view_name.field
      op: eq                  # eq | neq | gt | gte | lt | lte | in
      value: "value"
  orders:                     # Optional
    - field: view_name.field
      direction: asc          # asc | desc
```

### agent

```yaml
- name: task_name
  type: agent
  agent_ref: path/to/agent.agent.yml
  inputs:                     # Optional: previous task names
    - task1
    - task2
  prompt: |
    Analyze the data and provide insights.
```

Output reference in markdown: `{{task_name}}`

## Display Types

### markdown

```yaml
- type: markdown
  content: |
    # Title

    Some **markdown** content.

    AI output: {{agent_task}}
```

With title:
```yaml
- type: markdown
  title: "Section Title"
  content: "{{agent_task}}"
```

### table

```yaml
- type: table
  title: "Table Title"        # Optional
  data: task_name             # REQUIRED: task reference
```

### line_chart

```yaml
- type: line_chart
  title: "Chart Title"        # Optional
  data: task_name             # REQUIRED
  x: column_name              # REQUIRED: x-axis column
  y: column_name              # REQUIRED: y-axis column
  x_axis_label: "Label"       # Optional
  y_axis_label: "Label"       # Optional
  series: column_name         # Optional: group into multiple lines
```

### bar_chart

```yaml
- type: bar_chart
  title: "Chart Title"        # Optional
  data: task_name             # REQUIRED
  x: column_name              # REQUIRED: x-axis (categories)
  y: column_name              # REQUIRED: y-axis (values)
  series: column_name         # Optional: grouped/stacked bars
```

### pie_chart

```yaml
- type: pie_chart
  title: "Chart Title"        # Optional
  data: task_name             # REQUIRED
  name: column_name           # REQUIRED: category/label column
  value: column_name          # REQUIRED: numeric value column
```

### row

```yaml
- type: row
  columns: 2                  # Optional: equal-width column count (>= 1)
  children:                   # REQUIRED: list of display blocks
    - type: bar_chart
      data: task_a
      x: cat
      y: val
    - type: pie_chart
      data: task_b
      name: cat
      value: val
```

## Interactive Controls

Interactive widgets that re-run dependent tasks when changed. Values reach task
SQL via Jinja: `{{ controls.<name> }}`.

### Declaring controls — two forms

**Inline in `display:` (recommended)** — note the `control_type:` key:

```yaml
display:
  - type: control             # display discriminant
    name: region              # -> {{ controls.region }}
    control_type: select      # WIDGET KIND: control_type, NOT type
    label: Region
    options: [All, North, South]
    default: "All"
```

**Top-level `controls:` array** — here the widget kind uses plain `type:`:

```yaml
controls:
  - name: region
    type: select              # plain `type:` in the top-level array
    label: Region
    options: [All, North, South]
    default: "All"
```

Use one form per app; do not declare the same control in both.

### Control fields

| Field          | Required | Notes                                                            |
| -------------- | -------- | ---------------------------------------------------------------- |
| `name`         | yes      | snake_case; referenced as `{{ controls.<name> }}`               |
| `control_type` | yes      | `select` \| `date` \| `toggle` (top-level array uses `type:`)    |
| `label`        | no       | UI label; defaults to `name`                                     |
| `default`      | no       | Initial value; quote strings; toggle uses `true`/`false`         |
| `options`      | no       | `select` only — static choice list                              |
| `source`       | no       | `select` only — task name; its first column fills the dropdown   |

### Control types

| Kind     | Widget      | Value                | SQL usage                                          |
| -------- | ----------- | -------------------- | -------------------------------------------------- |
| `select` | Dropdown    | string               | `col = {{ controls.x \| sqlquote }}`               |
| `date`   | Date picker | string `YYYY-MM-DD`  | `d >= {{ controls.start \| sqlquote }}`            |
| `toggle` | On/off      | boolean              | `{% if controls.flag %}AND ...{% endif %}`         |

### SQL templating rules

- Always pipe strings/dates through `| sqlquote` — it adds the quotes and escapes.
- Never wrap a `sqlquote` value in your own quotes (`'{{ ... | sqlquote }}'` is broken).
- Optional filter: `({{ controls.x | sqlquote }} = 'All' OR col = {{ controls.x | sqlquote }})`.
- Client-mode tasks support ONLY: `{{ x }}`, `{{ x | sqlquote }}`,
  `{{ x | default('v') }}`, `{% if x %}...{% endif %}`. No loops, comparisons, `else`.

### Task mode

| `mode`            | Re-runs on              | Use when                                              |
| ----------------- | ----------------------- | ----------------------------------------------------- |
| `client` (default)| Browser DuckDB WASM     | `execute_sql` + inline `sql_query` + local DuckDB     |
| `server`          | Server                  | External DB, `sql_file:`, workflow/semantic/agent     |

When in doubt use `mode: server` — non-local databases are forced to it anyway.

## SQL Dialect Reference

Use the right form for the configured database — the most common gotchas in
`execute_sql` task SQL:

| Dialect    | `DATE_TRUNC` form                                    | Stddev fn                      |
| ---------- | ---------------------------------------------------- | ------------------------------ |
| BigQuery   | `DATE_TRUNC(<col>, MONTH)` (column first, no quotes) | `STDDEV(<col>)`                |
| Snowflake  | `DATE_TRUNC('month', <col>)`                         | `STDDEV(<col>)`                |
| Postgres   | `DATE_TRUNC('month', <col>)`                         | `STDDEV(<col>)`                |
| DuckDB     | `DATE_TRUNC('month', <col>)`                         | `STDDEV(<col>)`                |
| ClickHouse | `toStartOfMonth(<col>)`                              | `stddevPop(<col>)` (lowercase) |

Other divergences:

| Concern             | Postgres / DuckDB         | Snowflake                 | BigQuery                          | ClickHouse / MySQL    |
| ------------------- | ------------------------- | ------------------------- | --------------------------------- | --------------------- |
| Identifier quoting  | `"col"`                   | `"col"`                   | `` `col` ``                       | `` `col` `` / unquoted |
| Cast to date        | `CAST(x AS DATE)`, `x::date` | `CAST(x AS DATE)`      | `CAST(x AS DATE)`                 | `toDate(x)`           |
| Date arithmetic     | `d + INTERVAL '1 day'`    | `DATEADD(day, 1, d)`      | `DATE_ADD(d, INTERVAL 1 DAY)`     | `d + INTERVAL 1 DAY`  |

## Profiling Template

Before committing a measure or entity to a chart, profile the underlying data
in one consolidated SELECT:

```sql
SELECT
  COUNT(*) AS rows,
  COUNT(DISTINCT <entity_expr>) AS entity_card,
  MIN(<time_expr>) AS min_date,
  MAX(<time_expr>) AS max_date,
  COUNT(DISTINCT DATE_TRUNC('month', <time_expr>)) AS month_count,
  MIN(<measure_expr>) AS min_val,
  MAX(<measure_expr>) AS max_val,
  STDDEV(<measure_expr>) AS measure_stddev
FROM <table>
```

Fitness thresholds for ranking / trend visualizations: `rows >= 100`,
`month_count >= 3`, `measure_stddev > 0`, `entity_card` between 5 and 500.

## Canonical Snippets

### 1. SQL -> Table

```yaml
name: customer_list

tasks:
  - name: customers
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        customer_id,
        name,
        email,
        created_at
      FROM customers
      ORDER BY created_at DESC
      LIMIT 100

display:
  - type: markdown
    content: |
      # Customer List
      Most recent 100 customers.

  - type: table
    title: "Customers"
    data: customers
```

### 2. SQL -> Line Chart

```yaml
name: revenue_trend

tasks:
  - name: monthly_revenue
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        toStartOfMonth(order_date) as month,
        ROUND(SUM(amount), 2) as revenue
      FROM orders
      WHERE order_date >= '2024-01-01'
      GROUP BY month
      ORDER BY month

display:
  - type: markdown
    content: |
      # Revenue Trend
      Monthly revenue for 2024.

  - type: line_chart
    title: "Monthly Revenue"
    data: monthly_revenue
    x: month
    y: revenue
    x_axis_label: "Month"
    y_axis_label: "Revenue ($)"
```

### 3. Workflow -> Markdown Summary

```yaml
name: operations_report

tasks:
  - name: ops
    type: workflow
    src: workflows/operations_analysis.workflow.yml
    variables:
      period: "2024-Q4"

display:
  - type: markdown
    content: |
      # Operations Report

      Q4 2024 operational metrics.

  - type: table
    title: "Location Metrics"
    data: ops.location_summary

  - type: bar_chart
    title: "Performance by Location"
    data: ops.location_summary
    x: location_name
    y: performance_score
```

### 4. Multi-Task App with Shared Context

```yaml
name: executive_dashboard

tasks:
  # Compute common date range
  - name: date_range
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        MIN(order_date) as start_date,
        MAX(order_date) as end_date,
        COUNT(*) as total_orders
      FROM orders

  # Summary KPIs
  - name: kpis
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        ROUND(SUM(amount), 2) as total_revenue,
        COUNT(DISTINCT customer_id) as unique_customers,
        ROUND(AVG(amount), 2) as avg_order_value
      FROM orders

  # Monthly breakdown
  - name: monthly
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        toStartOfMonth(order_date) as month,
        ROUND(SUM(amount), 2) as revenue,
        COUNT(*) as orders
      FROM orders
      GROUP BY month
      ORDER BY month

  # By region
  - name: regional
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        region,
        ROUND(SUM(amount), 2) as revenue,
        COUNT(*) as orders
      FROM orders
      GROUP BY region
      ORDER BY revenue DESC

display:
  - type: markdown
    content: |
      # Executive Dashboard

  - type: table
    title: "Analysis Period"
    data: date_range

  - type: table
    title: "Key Metrics"
    data: kpis

  - type: markdown
    content: |
      ---
      ## Revenue Analysis

  - type: line_chart
    title: "Monthly Revenue Trend"
    data: monthly
    x: month
    y: revenue
    x_axis_label: "Month"
    y_axis_label: "Revenue ($)"

  - type: bar_chart
    title: "Revenue by Region"
    data: regional
    x: region
    y: revenue

  - type: pie_chart
    title: "Regional Distribution"
    data: regional
    name: region
    value: revenue

  - type: table
    title: "Regional Details"
    data: regional
```

### 5. Semantic Query + Agent Insights

```yaml
name: sales_insights

tasks:
  - name: revenue_by_segment
    type: semantic_query
    topic: sales_metrics
    dimensions:
      - segment.name
    measures:
      - sales.total_revenue
      - sales.order_count
    orders:
      - field: sales.total_revenue
        direction: desc

  - name: monthly_trend
    type: semantic_query
    topic: sales_metrics
    dimensions:
      - time.month
    measures:
      - sales.total_revenue
    orders:
      - field: time.month
        direction: asc

  - name: generate_callouts
    type: agent
    agent_ref: sales_analyst.agent.yml
    inputs:
      - revenue_by_segment
      - monthly_trend
    prompt: |
      Analyze the sales data and provide 3-5 key callouts:
      - Segment performance highlights
      - Month-over-month trends
      - Notable patterns
      Format as markdown bullet points.

display:
  - type: markdown
    content: |
      # Sales Insights Report

  - type: markdown
    title: "Key Callouts"
    content: "{{generate_callouts}}"

  - type: bar_chart
    title: "Revenue by Segment"
    data: revenue_by_segment
    x: segment__name
    y: sales__total_revenue

  - type: line_chart
    title: "Monthly Trend"
    data: monthly_trend
    x: time__month
    y: sales__total_revenue

  - type: table
    title: "Segment Details"
    data: revenue_by_segment
```

## Column Naming Conventions

### SQL Tasks
Column names match your SELECT aliases:
```sql
SELECT region as region_name, SUM(amount) as total_sales
```
Use: `x: region_name`, `y: total_sales`

### Semantic Queries
Columns use double underscore format: `view__field`
```yaml
dimensions:
  - sales.region
measures:
  - sales.revenue
```
Use: `x: sales__region`, `y: sales__revenue`

**Time dimensions with `granularity:` add the granularity as an extra
`__<granularity>` suffix on the output column.** A `time_dimensions` entry
of `dimension: orders.created_date, granularity: month` produces a column
named `orders__created_date__month` — the chart `x:` must reference it
with the suffix or the chart fails to render with a Binder error.

**Never put a raw UUID/FK column on a chart axis** (`restaurant_id`,
`customer_id`, `guid`, …). Pull a human-readable name through a foreign
entity (`x: restaurants__location_name`) or `execute_sql` JOIN instead.

## Validation Checklist

Run validation first:
```bash
oxy validate
```

Then verify:
- [ ] `oxy validate` passes with no errors
- [ ] `name` is snake_case (if provided)
- [ ] All task `name` fields are unique
- [ ] All task `name` fields are snake_case
- [ ] Every display `data` references a valid task name
- [ ] Chart `x`/`y`/`series`/`name`/`value` match actual column names
- [ ] SQL is valid for target database
- [ ] YAML uses spaces (not tabs) for indentation
- [ ] Strings with special characters are quoted
- [ ] Inline `- type: control` blocks use `control_type:` (not `type:`)
- [ ] Every `{{ controls.x }}` matches a declared control `name`
- [ ] Control strings/dates in SQL use `| sqlquote`, no extra quotes
- [ ] Tasks referencing controls on non-local databases set `mode: server`
