# Example Prompts for Oxy App Builder

This document shows example prompts and the resulting apps that Claude would generate.

## Example 1: Simple Sales Dashboard

### Prompt
> "Create a sales dashboard that shows total revenue, number of orders, and a monthly trend line chart. Use the orders table from clickhouse."

### Clarifying Questions Claude Might Ask
- What date range should the dashboard cover?
- Should we break down by any dimensions (region, product category)?
- What's the primary key/date column in your orders table?

### Resulting Plan
```
App: sales_dashboard
Purpose: Display sales KPIs and monthly revenue trends

Data Sources:
- clickhouse.orders

Tasks:
1. kpis: Get total revenue and order count -> columns: total_revenue, order_count
2. monthly_trend: Monthly aggregation -> columns: month, revenue

Displays:
1. markdown: Title and intro
2. table: KPIs
3. line_chart: Monthly revenue trend
```

### Generated App
```yaml
name: sales_dashboard

description: |
  Sales overview dashboard showing KPIs and monthly trends.

tasks:
  - name: kpis
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        ROUND(SUM(amount), 2) as total_revenue,
        COUNT(*) as order_count,
        ROUND(AVG(amount), 2) as avg_order_value
      FROM orders

  - name: monthly_trend
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        toStartOfMonth(order_date) as month,
        ROUND(SUM(amount), 2) as revenue
      FROM orders
      GROUP BY month
      ORDER BY month

display:
  - type: markdown
    content: |
      # Sales Dashboard

      Overview of sales performance.

  - type: table
    title: "Key Metrics"
    data: kpis

  - type: line_chart
    title: "Monthly Revenue Trend"
    data: monthly_trend
    x: month
    y: revenue
    x_axis_label: "Month"
    y_axis_label: "Revenue ($)"
```

---

## Example 2: Multi-Dimensional Analysis

### Prompt
> "Build a customer segmentation app that shows revenue by customer segment as a pie chart, with a detailed breakdown table. Also show segment trends over time."

### Resulting Plan
```
App: customer_segmentation
Purpose: Analyze revenue distribution across customer segments

Data Sources:
- clickhouse.customers (joined with orders)

Tasks:
1. segment_summary: Revenue by segment -> columns: segment, revenue, customer_count
2. segment_trends: Monthly trends by segment -> columns: month, segment, revenue

Displays:
1. markdown: Introduction
2. pie_chart: Revenue distribution
3. table: Segment details
4. line_chart: Trends with series by segment
```

### Generated App
```yaml
name: customer_segmentation

description: |
  Customer segmentation analysis showing revenue distribution
  and trends across different customer segments.

tasks:
  - name: segment_summary
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        c.segment,
        ROUND(SUM(o.amount), 2) as revenue,
        COUNT(DISTINCT c.customer_id) as customer_count,
        ROUND(SUM(o.amount) / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer
      FROM customers c
      JOIN orders o ON c.customer_id = o.customer_id
      GROUP BY c.segment
      ORDER BY revenue DESC

  - name: segment_trends
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        toStartOfMonth(o.order_date) as month,
        c.segment,
        ROUND(SUM(o.amount), 2) as revenue
      FROM customers c
      JOIN orders o ON c.customer_id = o.customer_id
      GROUP BY month, c.segment
      ORDER BY month, c.segment

display:
  - type: markdown
    content: |
      # Customer Segmentation Analysis

      Revenue breakdown and trends by customer segment.

  - type: pie_chart
    title: "Revenue Distribution by Segment"
    data: segment_summary
    name: segment
    value: revenue

  - type: table
    title: "Segment Summary"
    data: segment_summary

  - type: markdown
    content: |
      ---
      ## Segment Trends Over Time

  - type: line_chart
    title: "Monthly Revenue by Segment"
    data: segment_trends
    x: month
    y: revenue
    series: segment
    x_axis_label: "Month"
    y_axis_label: "Revenue ($)"
```

---

## Example 3: Workflow-Based Report

### Prompt
> "Create a franchise operations report that pulls data from the existing labor and sales workflows, showing staffing metrics and sales performance."

### Resulting Plan
```
App: franchise_report
Purpose: Consolidated franchise operations dashboard

Data Sources:
- workflows/labor_metrics.workflow.yml
- workflows/sales_analysis.workflow.yml

Tasks:
1. labor: Invoke labor workflow -> outputs: location_summary, overtime_analysis
2. sales: Invoke sales workflow -> outputs: sales_by_location

Displays:
1. markdown: Report header
2. table: Labor metrics from labor.location_summary
3. bar_chart: Overtime by location
4. table: Sales from sales.sales_by_location
```

### Generated App
```yaml
name: franchise_report

description: |
  Franchise operations report combining labor and sales metrics
  from existing workflow analyses.

tasks:
  - name: labor
    type: workflow
    src: workflows/labor_metrics.workflow.yml
    variables:
      min_hours: 50

  - name: sales
    type: workflow
    src: workflows/sales_analysis.workflow.yml
    variables:
      period: "2024-Q4"

display:
  - type: markdown
    content: |
      # Franchise Operations Report

      Q4 2024 operational metrics across all locations.

      ---
      ## Labor Metrics

  - type: table
    title: "Location Labor Summary"
    data: labor.location_summary

  - type: bar_chart
    title: "Overtime % by Location"
    data: labor.overtime_analysis
    x: location_name
    y: overtime_percentage

  - type: markdown
    content: |
      ---
      ## Sales Performance

  - type: bar_chart
    title: "Sales by Location"
    data: sales.sales_by_location
    x: location_name
    y: total_sales

  - type: table
    title: "Sales Details"
    data: sales.sales_by_location
```

---

## Example 4: Edit Existing App

### Prompt
> "Edit my existing sales_report.app.yml to add a bar chart showing revenue by product category."

### Claude's Approach
1. Read the existing file
2. Summarize what it currently does
3. Propose minimal additions
4. Get approval before changes

### Proposed Changes
```
Current app: sales_report (shows monthly trends and overall KPIs)

Proposed addition:
1. Add new task: revenue_by_category
   - SQL: GROUP BY product_category
2. Add new display: bar_chart after monthly trend
   - Shows category comparison

Files to modify: sales_report.app.yml
Changes: Add 1 task, add 1 display block
```

### Diff Preview
```yaml
# ADD after existing tasks:
  - name: revenue_by_category
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT
        product_category,
        ROUND(SUM(amount), 2) as revenue
      FROM orders
      GROUP BY product_category
      ORDER BY revenue DESC

# ADD to display section:
  - type: bar_chart
    title: "Revenue by Product Category"
    data: revenue_by_category
    x: product_category
    y: revenue
```
