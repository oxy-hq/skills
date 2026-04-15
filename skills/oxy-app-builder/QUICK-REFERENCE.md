# Oxy App Quick Reference

Schema cheat sheet and canonical snippets for `*.app.yml` files.

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
  sql_query: |                # Inline SQL
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

## Validation Checklist

Run validation first:
```bash
oxygen validate
```

Then verify:
- [ ] `oxygen validate` passes with no errors
- [ ] `name` is snake_case (if provided)
- [ ] All task `name` fields are unique
- [ ] All task `name` fields are snake_case
- [ ] Every display `data` references a valid task name
- [ ] Chart `x`/`y`/`series`/`name`/`value` match actual column names
- [ ] SQL is valid for target database
- [ ] YAML uses spaces (not tabs) for indentation
- [ ] Strings with special characters are quoted
