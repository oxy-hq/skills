---
name: oxy-semantic-layer
description: Build and maintain Oxy semantic layer files (views and topics) for analytics. Use when the user asks to create, update, or validate Oxy semantic layers, view files, topic files, or needs help understanding database schemas for semantic layer creation.
---

# Oxy Semantic Layer Builder

You are an expert at building Oxy semantic layer files. Your role is to analyze database schemas and create well-structured view and topic files that enable business users to query data using natural language.

## Core Workflow

When building semantic layers, follow this process:

1. **Analyze schemas**: Read `semantics.yml` (produced by `oxy sync`) to discover tables and columns. If `.databases/` exists, read that instead.
2. **Create views**: Build `semantics/views/*.view.yml` files with entities, dimensions, and measures
3. **Create topics**: Build `semantics/topics/*.topic.yml` files to organize views
4. **Validate**: Run `oxy build` to check syntax and compilation
5. **Test**: Use `oxy semantic-engine --dev-mode` to verify queries work

## Essential Commands

```bash
# Generate database schemas (run first)
oxy sync

# Validate semantic layer
oxy build

# Test semantic engine
oxy semantic-engine --dev-mode
```

## View File Structure

Views are the core of the semantic layer. Each view file (`semantics/views/*.view.yml`) defines:

```yaml
name: view_name
description: "Clear business explanation of what this view represents"
datasource: "database_name"  # Must match config.yml
table: "schema_name.table_name"

entities:
  - name: entity_name
    type: primary|foreign
    description: "What this entity represents"
    key: dimension_name  # MUST reference a dimension name, not a column

dimensions:
  - name: dimension_name
    type: string|number|date|datetime|boolean
    description: "Business-friendly explanation"
    expr: column_name_or_sql_expression
    samples: ["example1", "example2"]  # Optional but helpful
    synonyms: ["alias1", "alias2"]     # For natural language queries

measures:
  - name: measure_name
    type: sum|average|count|count_distinct|min|max|median|stddev|custom
    description: "What this metric represents"
    expr: column_name_or_sql_expression
    synonyms: ["alternative name"]
    filters: []  # Optional, for filtered measures
```

## Entity Design (Critical for Joins)

**Entities enable automatic joins between views**. When multiple views define entities with the same name, Oxy automatically creates join relationships.

### Entity Types

- **Primary entity**: The main subject of the view (one per view, required)
- **Foreign entity**: References to objects in other views (creates relationships)

### Key Rule

**Entity keys MUST reference dimension names, not database columns**:

```yaml
entities:
  - name: order
    type: primary
    key: order_id  # This references the dimension below

dimensions:
  - name: order_id  # The dimension name
    type: string
    expr: order_id  # This is the actual database column
```

### Example Multi-Entity View

```yaml
entities:
  - name: order
    type: primary
    description: "Individual customer order"
    key: order_id

  - name: customer
    type: foreign
    description: "Customer who placed the order"
    key: customer_id

  - name: restaurant
    type: foreign
    description: "Restaurant fulfilling the order"
    key: restaurant_id

dimensions:
  - name: order_id
    type: string
    description: "Unique order identifier"
    expr: order_id

  - name: customer_id
    type: string
    description: "Customer identifier"
    expr: customer_id

  - name: restaurant_id
    type: string
    description: "Restaurant identifier"
    expr: restaurant_id
```

## Dimension Patterns

### Time Dimensions

Extract date parts for temporal analysis:

```yaml
dimensions:
  - name: order_date
    type: date
    description: "Date when order was placed"
    expr: order_date

  - name: order_year
    type: number
    description: "Year of order"
    expr: "EXTRACT(YEAR FROM order_date)"
    synonyms: ["year"]

  - name: order_month
    type: number
    description: "Month of order (1-12)"
    expr: "EXTRACT(MONTH FROM order_date)"
    synonyms: ["month"]

  - name: order_quarter
    type: number
    description: "Quarter of order (1-4)"
    expr: "EXTRACT(QUARTER FROM order_date)"
```

### Categorical Ranges

Bin continuous values:

```yaml
dimensions:
  - name: price_range
    type: string
    description: "Price category"
    expr: |
      CASE
        WHEN price < 100 THEN 'Budget'
        WHEN price BETWEEN 100 AND 500 THEN 'Mid-Range'
        ELSE 'Premium'
      END
    samples: ["Budget", "Mid-Range", "Premium"]
    synonyms: ["price category", "price tier"]
```

### Boolean Flags

```yaml
dimensions:
  - name: is_holiday
    type: boolean
    description: "Whether date is a holiday"
    expr: is_holiday
    samples: [true, false]
    synonyms: ["holiday", "holiday flag"]
```

## Measure Patterns

**Note**: Measures can have filters applied directly in their definition using the `filters` property. Dimensions cannot have filters; filtering on dimensions is done at the topic level using `default_filters`.

### Basic Aggregations

```yaml
measures:
  - name: total_orders
    type: count
    description: "Total number of orders"
    synonyms: ["order count", "number of orders"]

  - name: total_revenue
    type: sum
    description: "Total revenue from all orders"
    expr: order_amount
    synonyms: ["total sales", "gross revenue", "sales"]

  - name: average_order_value
    type: average
    description: "Average order value"
    expr: order_amount
    synonyms: ["avg order value", "AOV"]
```

### Filtered Measures

Apply conditions to measures using filter expressions:

```yaml
measures:
  - name: holiday_revenue
    type: sum
    description: "Revenue during holiday periods only"
    expr: order_amount
    filters:
      - expr: "{{is_holiday}} = true"

  - name: completed_orders
    type: count
    description: "Number of completed orders"
    filters:
      - expr: "{{status}} = 'completed'"

  - name: high_value_orders
    type: count
    description: "Orders over $1000"
    filters:
      - expr: "{{order_amount}} >= 1000"
```

### Custom Calculations

```yaml
measures:
  - name: revenue_growth_rate
    type: custom
    description: "Year-over-year revenue growth percentage"
    expr: |
      (SUM(CASE WHEN year = 2024 THEN revenue END) -
       SUM(CASE WHEN year = 2023 THEN revenue END)) /
       NULLIF(SUM(CASE WHEN year = 2023 THEN revenue END), 0) * 100

  - name: temp_sales_correlation
    type: custom
    description: "Correlation between temperature and sales"
    expr: "CORR(temperature, sales)"
```

## Topic File Structure

Topics organize views by business domain. **Best practice: create one topic per view**.

```yaml
name: topic_name
description: "Business domain this topic covers"
base_view: primary_view_name
views:
  - view_name

# Optional: Apply filters to all queries
default_filters:
  - field: "status"
    not_in:
      values: ["cancelled", "test"]
  - field: "is_deleted"
    eq:
      value: false
```

### Filter Types

Filters use a nested structure with the operator as a key:

- **Scalar filters** (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`): Use `value` field
  ```yaml
  - field: "amount"
    gt:
      value: 0
  ```
- **Array filters** (`in`, `not_in`): Use `values` field (array)
  ```yaml
  - field: "status"
    not_in:
      values: ["cancelled", "test"]
  ```
- **Date range filters** (`in_date_range`, `not_in_date_range`): Use `from` and `to` fields
  ```yaml
  - field: "order_date"
    in_date_range:
      from: "2023-01-01"
      to: "2023-12-31"
  ```

## Building Process

### Step 1: Generate Schemas

```bash
oxy sync
```

This reads database connections from `config.yml` and writes schema/dimension data to
`semantics.yml` in the project root. Read this file to discover table names and columns.

> **Note**: Older oxy versions wrote to `.databases/` instead. If `.databases/` exists,
> read it. Otherwise read `semantics.yml`.

### Step 2: Analyze Schemas

Read the schema files to understand:
- Table structures and column types
- Primary/foreign key relationships
- Column naming patterns
- Business context from table/column names

### Step 3: Create View Files

For each table or logical data model:

1. **Define primary entity** (the main subject)
2. **Add foreign entities** (relationships to other tables)
3. **Create dimensions** (filterable/groupable attributes)
   - Direct column mappings
   - Calculated fields (date parts, ranges)
   - Add synonyms for natural language
4. **Create measures** (aggregatable metrics)
   - Basic aggregations (sum, count, average)
   - Filtered measures (segment-specific)
   - Custom calculations (ratios, correlations)
5. **Document thoroughly** (descriptions, samples, synonyms)

### Step 4: Create Topic Files

Create one topic per view to organize by business domain.

### Step 5: Validate

```bash
# oxy build requires a running PostgreSQL instance.
# If OXY_DATABASE_URL is not already set, start it first:
oxy start  # starts Docker-based PostgreSQL on localhost:15432
export OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy

# Then build and validate the semantic layer
oxy build
```

Always run `oxy build` after creating or editing view or topic files — **this is a mandatory
final step, do not consider the task complete until it passes.** It processes `.view.yml` and
`.topic.yml` files, compiles them, and reports errors.

**Do NOT use `oxy validate` on view or topic files.** `oxy validate` is for workflow, agent,
and app files only. Running it on view/topic files will not catch errors and may report
misleading results.

`oxy build` validates:
- Entity/dimension/measure references across views
- SQL expression syntax
- Topic-to-view relationships

### Step 6: Test

```bash
oxy semantic-engine --dev-mode
```

Test natural language queries to verify the semantic layer generates correct SQL.

## Quality Guidelines

### Naming Conventions

- Use `snake_case` for all names
- Be descriptive and business-friendly
- Avoid abbreviations unless universally understood
- Use consistent patterns (e.g., `total_*`, `avg_*`, `*_count`)

### Descriptions

- Write clear, business-friendly explanations
- Explain what the field represents, not how it's calculated
- Include units where relevant (e.g., "in USD", "in minutes")

### Synonyms

Add synonyms for:
- Common abbreviations (e.g., "AOV" for "average order value")
- Alternative phrasings (e.g., "revenue" vs "sales")
- Domain-specific terms (e.g., "check" vs "bill" in restaurants)

### Samples

Provide example values for:
- Categorical dimensions
- Boolean flags
- Any field where example values aid understanding

## Common Issues

### Entity Key Not Found

**Error**: "Entity key 'X' not found in dimensions"

**Cause**: Entity key references a column name instead of a dimension name

**Fix**: Ensure entity `key` references a dimension `name`:

```yaml
entities:
  - name: order
    key: order_id  # Must match dimension name below

dimensions:
  - name: order_id  # This is what entity key references
    expr: order_id  # This is the actual column
```

### View Not Found

**Error**: "View 'X' not found"

**Cause**: View file not in correct location or name mismatch

**Fix**:
- Ensure file is in `semantics/views/` directory
- Verify filename is `*.view.yml`
- Check that `name` field matches topic reference exactly

### SQL Generation Errors

**Error**: Generated SQL fails or is incorrect

**Cause**: Invalid SQL in `expr` fields

**Fix**:
- Verify column names exist in the table
- Check SQL syntax for your database dialect
- Ensure data types match (don't sum strings, don't average dates)
- Test expressions with `--dry-run`

### Joins Not Working

**Error**: Can't query across multiple views

**Cause**: Entity names don't match or keys are incorrect

**Fix**:
- Use identical entity names across related views
- Verify entity keys reference the correct dimensions
- Ensure dimensions exist with matching names

## DeepWiki Fallback

For Oxy features not covered here, query DeepWiki with:

"I am a user of this project, not its maintainer. Please prioritize looking at the project docs, examples and json-schemas to answer my question: [your question]"

Only search `oxy-hq/oxy` repository.

## Documentation Links

- Semantic Layer: https://docs.oxy.tech/learn-about-oxy/semantic-layer
- Views: https://docs.oxy.tech/learn-about-oxy/semantic-layer/views
- Entities: https://docs.oxy.tech/learn-about-oxy/semantic-layer/entities
- Dimensions: https://docs.oxy.tech/learn-about-oxy/semantic-layer/dimensions
- Measures: https://docs.oxy.tech/learn-about-oxy/semantic-layer/measures
- Topics: https://docs.oxy.tech/learn-about-oxy/semantic-layer/topics

## Examples

### Complete View Example

```yaml
name: restaurant_orders
description: "Restaurant order transactions with customer and item details"
datasource: "clickhouse"
table: "restaurant_analytics.orders"

entities:
  - name: order
    type: primary
    description: "Individual restaurant order"
    key: order_id

  - name: customer
    type: foreign
    description: "Customer who placed the order"
    key: customer_id

  - name: restaurant
    type: foreign
    description: "Restaurant fulfilling the order"
    key: restaurant_id

dimensions:
  - name: order_id
    type: string
    description: "Unique order identifier"
    expr: order_id

  - name: customer_id
    type: string
    description: "Customer identifier"
    expr: customer_id

  - name: restaurant_id
    type: string
    description: "Restaurant identifier"
    expr: restaurant_id

  - name: order_date
    type: datetime
    description: "Timestamp when order was placed"
    expr: order_timestamp

  - name: order_year
    type: number
    description: "Year order was placed"
    expr: "EXTRACT(YEAR FROM order_timestamp)"
    synonyms: ["year"]

  - name: order_status
    type: string
    description: "Current status of the order"
    expr: status
    samples: ["pending", "preparing", "ready", "completed", "cancelled"]
    synonyms: ["status", "order state"]

  - name: is_delivery
    type: boolean
    description: "Whether order is for delivery"
    expr: "order_type = 'delivery'"
    synonyms: ["delivery order", "delivery"]

measures:
  - name: total_orders
    type: count
    description: "Total number of orders"
    synonyms: ["order count", "number of orders"]

  - name: total_revenue
    type: sum
    description: "Total revenue from orders"
    expr: order_amount
    synonyms: ["total sales", "revenue", "sales"]

  - name: average_order_value
    type: average
    description: "Average order value in USD"
    expr: order_amount
    synonyms: ["AOV", "avg order value"]

  - name: delivery_revenue
    type: sum
    description: "Revenue from delivery orders only"
    expr: order_amount
    filters:
      - expr: "{{is_delivery}} = true"
```

### Complete Topic Example

```yaml
name: restaurant_orders
description: "Restaurant order analytics covering sales, customer behavior, and fulfillment"
base_view: restaurant_orders
views:
  - restaurant_orders

default_filters:
  - field: "order_status"
    not_in:
      values: ["cancelled", "test"]
```

## Important: Do NOT Add yaml-language-server Schema Comments

**NEVER add `# yaml-language-server: $schema=...` comments to view or topic files.**

- Oxy does not publish JSON schemas for view.yml or topic.yml files at predictable URLs
- Adding non-existent schema URLs causes IDE validation errors and confusion
- If you're unsure whether a schema URL exists, don't include it
- Only add schema comments if you have verified the URL returns a valid JSON schema
