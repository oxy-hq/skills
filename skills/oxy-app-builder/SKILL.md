---
name: oxy-app-builder
description: Build and edit Oxy data app YAML files (*.app.yml) that visualize data through tasks and displays. Use when users ask to create dashboards, data apps, reports, or interactive analytics interfaces. Helps define SQL/workflow/agent tasks and render outputs as tables, charts, and markdown.
---

# Oxy App Builder

You are an expert at building Oxy data apps - interactive dashboards that combine data tasks with visualizations. Your role is to help users create `*.app.yml` files that transform data into insights through tables, charts, and markdown content.

## What is an Oxy App?

An Oxy app is a YAML file that defines:
1. **Tasks** - Operations that produce data (SQL queries, workflows, semantic queries, agents)
2. **Displays** - Visualizations that render task outputs (tables, charts, markdown)

The mental model: **Task -> Output -> Display**

## App YAML Structure

```yaml
# Optional metadata
name: app_name                # snake_case identifier
description: |                # Multi-line description
  What this app does...

# Required: Array of tasks (min 1)
tasks:
  - name: task_name           # Unique, snake_case
    type: execute_sql         # Task type
    database: clickhouse      # Database to query
    sql_query: |              # Inline SQL
      SELECT * FROM table

# Required: Array of displays (min 1)
display:
  - type: table
    title: "Results"
    data: task_name           # Reference task by name
```

## Task Types

### 1. execute_sql - Direct SQL Execution
```yaml
- name: sales_by_region
  type: execute_sql
  database: clickhouse        # or: postgres, bigquery, local (DuckDB)
  sql_query: |
    SELECT region, SUM(amount) as total
    FROM sales
    GROUP BY region
```

Or reference a SQL file:
```yaml
- name: sales_report
  type: execute_sql
  database: clickhouse
  sql_file: queries/sales_report.sql
```

### 2. workflow - Invoke Sub-Workflow
```yaml
- name: data_prep
  type: workflow
  src: workflows/data_prep.workflow.yml
  variables:
    start_date: "2024-01-01"
    min_threshold: 100
```

Reference workflow task outputs: `workflow_name.inner_task_name`

### 3. semantic_query - Query Semantic Layer
```yaml
- name: revenue_by_month
  type: semantic_query
  topic: sales_mrr
  dimensions:
    - sales.month
  measures:
    - sales.total_revenue
    - sales.order_count
  filters:
    - field: sales.year
      op: eq
      value: 2024
  orders:
    - field: sales.month
      direction: asc
```

### 4. agent - AI-Powered Analysis
```yaml
- name: generate_insights
  type: agent
  agent_ref: analyst.agent.yml
  inputs:
    - sales_data
    - customer_data
  prompt: |
    Analyze the provided data and generate 3-5 key insights
    about sales trends and customer behavior.
```

Reference agent output in markdown: `{{generate_insights}}`

## Display Types

### markdown - Rich Text Content
```yaml
- type: markdown
  content: |
    # Dashboard Title

    Analysis period: **Q4 2024**

    ## Key Findings
    {{agent_task_name}}
```

With title:
```yaml
- type: markdown
  title: "Key Insights"
  content: "{{insights_task}}"
```

### table - Tabular Data
```yaml
- type: table
  title: "Sales Summary"
  data: sales_by_region        # Reference task name
```

### line_chart - Trend Lines
```yaml
- type: line_chart
  title: "Revenue Over Time"
  data: monthly_revenue
  x: month                     # Column for x-axis
  y: total_revenue             # Column for y-axis
  x_axis_label: "Month"
  y_axis_label: "Revenue ($)"
  series: region               # Optional: group into multiple lines
```

### bar_chart - Category Comparison
```yaml
- type: bar_chart
  title: "Sales by Region"
  data: regional_sales
  x: region
  y: total_sales
  series: product_category     # Optional: grouped/stacked bars
```

### pie_chart - Distribution
```yaml
- type: pie_chart
  title: "Market Share"
  data: market_data
  name: company                # Category column
  value: market_share          # Value column
```

### Chart column gotchas

**Time-dimension granularity suffix.** When a `semantic_query` task uses
`time_dimensions:` with `granularity:`, the output column gets an extra
`__<granularity>` suffix appended. Example:

```yaml
tasks:
  - name: trend
    type: semantic_query
    topic: orders
    time_dimensions:
      - dimension: orders.created_date
        granularity: month
    measures: [orders.total_revenue]

display:
  - type: line_chart
    data: trend
    x: orders__created_date__month   # NOT orders__created_date
    y: orders__total_revenue
```

Omitting the suffix produces a "column not found" Binder error in the
in-browser DuckDB chart engine and the chart silently fails to render.

**Never put a raw UUID/FK on a chart axis or table row label.** When the
primary entity's `key:` is an opaque ID (`guid`, `restaurant_id`,
`customer_id`, `order_id`, …), do NOT use that field as the chart `x:`,
`name:`, or as the only identifier in a table — the dashboard will render
uninformative UUIDs.

Two ways to surface a human-readable label instead:

1. **Preferred — `semantic_query` via foreign entity.** If a joined view
   exposes a name dimension (e.g. `restaurants.location_name`), make sure
   the FK side declares the joined view as a `type: foreign` entity (see
   the semantic-layer skill), include both views in the topic, and pull
   the name through:
   `dimensions: [restaurants.location_name]` instead of
   `dimensions: [orders.restaurant_id]`. Output column is then
   `restaurants__location_name`.

2. **Fallback — `execute_sql` with a JOIN.** When `semantic_query` can't
   reach the name (no foreign entity, no multi-view topic), use
   `execute_sql` with an explicit JOIN to the lookup table and `SELECT`
   the name column directly.

If neither path is available (no name field exists in any related view),
fall back to the FK but warn in the markdown header that rows are keyed
by ID — never silently render UUIDs as a chart axis.

## SQL dialect notes

When you author or profile SQL inside an `execute_sql` task — or when you query
the warehouse to check shape/distribution before picking fields — match the
dialect to the configured database. The most common gotchas:

| Dialect    | `DATE_TRUNC` form                                    | Stddev fn                      |
| ---------- | ---------------------------------------------------- | ------------------------------ |
| BigQuery   | `DATE_TRUNC(<col>, MONTH)` (column first, no quotes) | `STDDEV(<col>)`                |
| Snowflake  | `DATE_TRUNC('month', <col>)`                         | `STDDEV(<col>)`                |
| Postgres   | `DATE_TRUNC('month', <col>)`                         | `STDDEV(<col>)`                |
| DuckDB     | `DATE_TRUNC('month', <col>)`                         | `STDDEV(<col>)`                |
| ClickHouse | `toStartOfMonth(<col>)`                              | `stddevPop(<col>)` (lowercase) |

Other places `.app.yml` SQL diverges across dialects:

- **Identifier quoting** — `"col"` in Postgres/Snowflake; `` `col` `` in BigQuery/MySQL.
- **Casting** — `CAST(x AS DATE)` is portable; `x::date` is Postgres-only.
- **Date arithmetic** — `INTERVAL '1 day'` works in Postgres/DuckDB; BigQuery uses `DATE_ADD(d, INTERVAL 1 DAY)`.

## Profiling template

Before committing to a measure or entity for a chart or ranked table, profile
the underlying data so you don't ship a flat-line trend or a top-10 with one
row in it. One consolidated SELECT is enough:

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

Substitute `<entity_expr>`, `<time_expr>`, `<measure_expr>`, and `<table>` with
the view's actual `expr:` strings — never guess column names. Apply the
dialect substitutions above when the warehouse is BigQuery or ClickHouse.

A topic is fit for ranking and trend visualizations when:

- `rows >= 100`,
- `month_count >= 3` (enough time for a meaningful trend),
- `measure_stddev > 0` (not a flat measure that draws as a horizontal line at one value),
- `entity_card` is between 5 and 500 (top/bottom-N actually differ).

## Failure recovery

Profiling queries fail mid-build for routine reasons — dialect mismatch,
type-cast errors, an aggregation function the warehouse doesn't expose. The
recovery rule is:

1. **Simplify and retry once** — drop `STDDEV`, drop `month_count`, or
   replace `DATE_TRUNC` with the dialect equivalent. At most two attempts per
   topic in total.
2. **Skip the topic on the second failure** — never loop on the same failing
   query. Move on to the next candidate; if none qualify, omit the affected
   block entirely rather than ship a misleading chart.

This rule applies anywhere in `.app.yml` authoring where you query the
warehouse before committing layout decisions.

## Workflow for Building Apps

### ALWAYS Follow This Process:

1. **Understand Requirements**
   - What insights does the user need?
   - What data sources are available?
   - What visualizations make sense?

2. **Create a Plan** (REQUIRED before writing YAML)
   ```
   App: [name]
   Purpose: [1-2 sentences]

   Data Sources:
   - [database/table or semantic layer topic]

   Tasks:
   1. task_name: [intent] -> [output shape: columns]
   2. task_name: [intent] -> [output shape]

   Displays:
   1. [type]: [what it shows] - data: task_name
   2. [type]: [what it shows] - data: task_name
   ```

3. **Get User Sign-Off on Plan**
   - Don't write YAML until plan is approved

4. **Write the App YAML**
   - Follow conventions from examples
   - Ensure task outputs match display requirements

5. **Pre-test referenced workflows and agents** (REQUIRED before opening the app)

   `oxy validate` only checks YAML structure — SQL errors won't surface until the app runs in
   the UI. Run any workflows and agents the app references BEFORE finalizing the app:

   ```bash
   # Test each workflow the app references
   OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy oxy run workflows/my_workflow.workflow.yml

   # Test each agent the app references
   OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy oxy run my_agent.agent.yml "summarize last week"
   ```

   If either fails with a SQL error, fix the workflow or agent first, then return to the app.

6. **Validate** (REQUIRED)
   - Run `oxy validate --file=<path>` on the app file
   - Fix any validation errors before proceeding
   - Verify task names match display data references

7. **Smoke-test the app end-to-end** (REQUIRED before declaring done)

   `oxy validate` only catches structural YAML errors. It does **not** catch
   malformed SQL — broken JOIN syntax, dialect-specific type mismatches,
   missing `ON` clauses, type coercion failures — which all fail at
   task-execution time. The most common failure mode is a brand-new
   `.app.yml` that loads as a blank dashboard with a runtime error,
   because the model wrote SQL that *parses* but doesn't *run* on the
   target warehouse.

   After every write or edit to a `.app.yml`, run every task end-to-end.
   Two practical paths:

   - **Open the app in the UI.** `oxy serve --enterprise` renders the app;
     a working app shows every block populated, a broken one shows an
     error banner naming the failing task.
   - **Run each task manually.** For `type: execute_sql` tasks, run the
     rendered `sql_query` against the same `database`. For
     `type: semantic_query` tasks, run the same topic / dimensions /
     measures through `oxy semantic-engine --dev-mode` (or the same
     warehouse-query path your environment exposes).

   Failure-recovery loop:

   1. If every task succeeds, stop — the file is done.
   2. If any task fails, read the error, diagnose, and apply **one**
      targeted corrective edit (most common fixes: re-state the JOIN
      with `ON`, replace a dialect-specific function with the matrix
      entry from `## SQL dialect notes`, or drop the offending measure /
      dimension and pick a different one from the view).
   3. Re-run the smoke test **once**. If it still fails, stop and report
      the error verbatim — do **not** loop. A second silent retry usually
      compounds the bad guess.

## Data Reference Patterns

### Direct task reference:
```yaml
data: task_name
```

### Workflow task reference (dot notation):
```yaml
data: workflow_task.inner_task_name
```

### Markdown templating:
```yaml
content: "Generated by AI: {{agent_task_name}}"
```

## Common Patterns

### Pattern 1: SQL -> Table + Chart
```yaml
name: sales_dashboard

tasks:
  - name: sales_by_region
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT region, SUM(amount) as total_sales
      FROM orders
      WHERE order_date >= '2024-01-01'
      GROUP BY region
      ORDER BY total_sales DESC

display:
  - type: markdown
    content: |
      # Sales Dashboard
      Regional sales performance for 2024.

  - type: bar_chart
    title: "Sales by Region"
    data: sales_by_region
    x: region
    y: total_sales

  - type: table
    title: "Regional Details"
    data: sales_by_region
```

### Pattern 2: Multi-Task Dashboard with Trends
```yaml
name: executive_dashboard

tasks:
  - name: kpi_summary
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        SUM(revenue) as total_revenue,
        COUNT(DISTINCT customer_id) as customers,
        AVG(order_value) as avg_order
      FROM orders

  - name: monthly_trends
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        DATE_TRUNC('month', order_date) as month,
        SUM(revenue) as revenue
      FROM orders
      GROUP BY 1
      ORDER BY 1

display:
  - type: markdown
    content: |
      # Executive Dashboard

  - type: table
    title: "Key Metrics"
    data: kpi_summary

  - type: line_chart
    title: "Revenue Trend"
    data: monthly_trends
    x: month
    y: revenue
    x_axis_label: "Month"
    y_axis_label: "Revenue ($)"
```

### Pattern 3: Workflow Orchestration
```yaml
name: franchise_report

tasks:
  - name: sales
    type: workflow
    src: workflows/sales_analysis.workflow.yml
    variables:
      period: "2024-Q4"

  - name: labor
    type: workflow
    src: workflows/labor_metrics.workflow.yml
    variables:
      min_hours: 50

display:
  - type: table
    title: "Sales by Location"
    data: sales.location_summary      # Dot notation!

  - type: bar_chart
    title: "Labor Cost %"
    data: labor.cost_analysis
    x: location
    y: labor_cost_pct
```

### Pattern 4: Semantic Query + Agent Insights
```yaml
name: sales_report

tasks:
  - name: revenue_data
    type: semantic_query
    topic: sales_mrr
    dimensions:
      - sales.month
    measures:
      - sales.total_mrr
    orders:
      - field: sales.month
        direction: asc

  - name: insights
    type: agent
    agent_ref: analyst.agent.yml
    inputs:
      - revenue_data
    prompt: |
      Analyze the revenue data and provide 3 key insights.

display:
  - type: line_chart
    title: "Revenue Over Time"
    data: revenue_data
    x: sales__month
    y: sales__total_mrr

  - type: markdown
    title: "AI Insights"
    content: "{{insights}}"
```

## Best Practices

### Task Design
- **Unique names**: Each task must have a unique `name` (snake_case)
- **Clear output shapes**: Know what columns your SQL/query returns
- **Match displays**: Ensure output columns match chart x/y/series fields

### SQL Guidelines
- Use CTEs for complex queries
- Include ORDER BY for predictable results
- Add comments for complex logic: `# ==== SECTION ====`
- Round numeric outputs: `ROUND(value, 2)`

### Display Organization
- Start with markdown header/intro
- Group related visualizations
- Use markdown dividers: `---`
- End with data quality notes if relevant

### Chart Column Mapping
| Chart Type | Required Fields | Column Mapping |
|------------|-----------------|----------------|
| line_chart | x, y, data | x=dimension, y=measure |
| bar_chart | x, y, data | x=category, y=value |
| pie_chart | name, value, data | name=label, value=amount |

## Editing Existing Apps

When editing an existing `*.app.yml`:

1. **Read the current file first**
2. **Summarize what it does**
3. **Propose minimal changes**
4. **Preserve existing style**

Only propose broader refactoring if the user explicitly requests it.

## Validation Checklist

Before finalizing, ALWAYS run:
```bash
oxy validate
```

Then verify:
- [ ] Validation passes with no errors
- [ ] All task names are unique and snake_case
- [ ] All display `data` fields reference valid task names
- [ ] Chart x/y/series/name/value fields match actual output columns
- [ ] SQL is syntactically correct for the target database

## Commands

```bash
# Validate all YAML configs (agents, workflows, apps)
oxy validate

# Validate a single file
oxy validate --file=my_app.app.yml
```

Note: Apps are rendered through the Oxy web UI (`oxy start --enterprise`), not via `oxy run`. The `oxy run` command only supports `.workflow.yml`, `.agent.yml`, and `.sql` files.

## DeepWiki Fallback

For features not covered here, query DeepWiki with:

"I am a user of this project, not its maintainer. Please look at project docs, examples, and json-schemas to answer: [your question]"

Only search `oxy-hq/oxy` repository.

## Quick Reference

See `QUICK-REFERENCE.md` for:
- Complete schema cheat sheet
- All field options per task/display type
- More example snippets
