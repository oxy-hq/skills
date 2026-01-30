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
  order:
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

5. **Validate**
   - Run `oxy validate` if available
   - Check YAML syntax
   - Verify task names match display data references

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
    order:
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

Before finalizing:
- [ ] All task names are unique and snake_case
- [ ] All display `data` fields reference valid task names
- [ ] Chart x/y/series/name/value fields match actual output columns
- [ ] YAML is valid (correct indentation, no tabs)
- [ ] SQL is syntactically correct for the target database

## Commands

```bash
# Run an app
oxy run my_app.app.yml

# Validate configuration
oxy validate

# Check for YAML syntax issues
oxy validate my_app.app.yml
```

## DeepWiki Fallback

For features not covered here, query DeepWiki with:

"I am a user of this project, not its maintainer. Please look at project docs, examples, and json-schemas to answer: [your question]"

Only search `oxy-hq/oxy` repository.

## Quick Reference

See `QUICK-REFERENCE.md` for:
- Complete schema cheat sheet
- All field options per task/display type
- More example snippets
