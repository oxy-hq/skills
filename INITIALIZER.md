# Oxy Repository Initialization Guide

This repository (`oxy-template`) is a template for creating Oxy analytics projects with CSV data. It currently contains sample sleep data as a reference implementation. Use this guide to bootstrap a new analytics project with your own CSV file.

## Starting Context

You are starting with **this repository** (oxy-template) which already has:
- `config.yml` configured for DuckDB with a local dataset
- Directory structure: `db/`, `semantics/views/`, `semantics/topics/`
- `CLAUDE.md` with instructions for Claude Code
- Sample sleep data and semantic layer as reference

## Your New Data

The new CSV file is located at: `db/[YOUR_CSV_FILENAME].csv`

## Bootstrap Steps

### Step 1: Update Configuration

1. **Verify config.yml dataset path matches your CSV location**:
   ```yaml
   databases:
     - name: local
       dataset: db/     # Must match where CSV files are located
       type: duckdb
   ```

2. **If needed, update the dataset path** to point to the directory containing your CSV

### Step 2: Generate Database Schema

Run Oxy sync to auto-generate schema files:
```bash
oxy sync
```

This creates `db/[YOUR_CSV_FILENAME].schema.yml` with:
- Table and column metadata
- Dimensions (categorical/temporal fields)
- Measures (numeric metrics)

### Step 3: Create Semantic Layer

**CRITICAL**: Use the `oxy-semantic-layer` skill (DO NOT create files manually):

```bash
# Invoke the skill
Use the oxy-semantic-layer skill with your CSV filename and domain description
```

The skill will create:
- **View file** (`semantics/views/[VIEW_NAME].view.yml`) with proper structure
- **Topic files** (`semantics/topics/[TOPIC_NAME].topic.yml`) for business domains

**Why use the skill?**
- Ensures correct YAML structure and field names
- Properly escapes column names with spaces: `expr: '"Column Name"'`
- Uses correct data types (`datetime` not `timestamp`)
- Creates proper samples (strings not booleans: `["true", "false"]`)
- Defines entities and relationships correctly
- Avoids common pitfalls that cause build errors

**What the skill creates:**

1. **View File Structure**:
   ```yaml
   name: view_name
   description: "Business-friendly description"
   datasource: local
   table: filename.csv

   entities:
     - name: entity_name
       type: primary
       description: "..."
       key: dimension_name  # Must reference a dimension

   dimensions:
     - name: dimension_name
       type: string|number|date|datetime|boolean
       description: "..."
       expr: '"Column Name"'  # Single quotes for YAML, double for SQL
       samples: ["value1", "value2"]  # Always strings
       synonyms: ["alias1", "alias2"]

   measures:
     - name: measure_name
       type: sum|average|count|count_distinct|min|max|custom
       description: "..."
       expr: '"Column Name"'
       synonyms: ["alias"]
       filters:  # Optional
         - expr: '{{dimension_name}} = ''value'''
   ```

2. **Topic File Structure**:
   ```yaml
   name: topic_name
   description: "Business domain description"
   base_view: view_name
   views:
     - view_name

   default_filters:  # Optional
     - field: "dimension_name"
       op: "eq|not_in|gt|lt"
       value: "value" or ["val1", "val2"]
   ```

### Step 4: Validate Semantic Layer

```bash
oxy build
```

This validates the semantic layer and compiles to Cube.js format.

**Common errors and fixes:**
- `missing field 'expr'`: Add `expr` field to all dimensions/measures
- `unknown variant 'timestamp'`: Use `datetime` instead
- `invalid type: boolean true`: Use `samples: ["true", "false"]`
- `Entity key 'X' not found`: Entity key must reference a dimension name
- `IO Error: No files found`: Check config.yml dataset path matches CSV location
- `Parser Error: syntax error at "column"`: Escape column names: `expr: '"Column Name"'`

### Step 5: Create Agent File (Optional)

Create `[DOMAIN]-analyst.agent.yml`:
```yaml
name: domain_analyst
description: "Agent for analyzing [domain] data"
model: openai-4.1

system_instructions: |
  You are an expert [domain] analyst...

tools:
  - type: semantic_query
    topics:
      - topic_name

consistency_tests:
  - query: "Sample question about the data"
    expect_contains: ["expected", "keywords"]
```

### Step 6: Create Workflow File (Optional)

Create `report-generator.workflow.yml`:
```yaml
name: report_generator
description: "Generate comprehensive [domain] report"

tasks:
  - name: analyze_metrics
    agent: domain_analyst
    prompt: "Analyze key metrics..."

  - name: format_report
    agent: domain_analyst
    prompt: "Format the analysis into a report"
    depends_on: [analyze_metrics]
```

### Step 7: Create SQL Query Files (Optional)

Create `[QUERY_NAME].sql`:
```sql
/* Business-relevant query description */
SELECT
    "Column Name",  -- DuckDB requires double quotes for columns with spaces
    AVG("Metric Column") as avg_metric
FROM "filename.csv"  -- Use double quotes for CSV files
WHERE "Filter Column" = 'value'
GROUP BY "Column Name"
ORDER BY avg_metric DESC;
```

**Important SQL Rules:**
- Use double quotes for column names with spaces: `"Column Name"`
- Use double quotes for CSV filenames: `"filename.csv"`
- Use single quotes for string values: `WHERE column = 'value'`

### Step 8: Create App File (Optional)

Create `[DOMAIN]_analytics.app.yml`:
```yaml
name: domain_analytics
description: "[Domain] analytics dashboard"

tasks:
  - name: metrics_overview
    execute_sql: |
      SELECT ... FROM "filename.csv"

  - name: trend_analysis
    execute_sql: |
      SELECT ... FROM "filename.csv"

display:
  - type: markdown
    content: |
      # [Domain] Analytics Dashboard

  - type: bar_chart
    data: metrics_overview
    x: dimension_column
    y: metric_column
    title: "Metrics by Dimension"
```

### Step 9: Clean Up Old Files

Remove all sleep-related sample files:
```bash
rm -f sleep_*.sql sleep_*.yml db/sleeps.* semantics/views/sleep_*.yml semantics/topics/sleep_*.yml
```

### Step 10: Test Everything

1. **Validate configuration**:
   ```bash
   oxy validate
   ```

2. **Test semantic layer**:
   ```bash
   oxy semantic-engine --dev-mode
   # Try natural language queries
   ```

3. **Test SQL queries**:
   ```bash
   oxy run [query].sql --dry-run  # Validate first
   oxy run [query].sql             # Execute
   ```

4. **Test agents** (if created):
   ```bash
   oxy run [agent].agent.yml "sample question"
   ```

5. **Test workflows** (if created):
   ```bash
   oxy run report-generator.workflow.yml
   ```

## Critical Format Rules

### View Files
- Use `expr:` (not `sql:`) for all dimensions and measures
- Column names with spaces: `expr: '"Column Name"'` (single quotes for YAML, double for SQL)
- Data types: `string`, `number`, `date`, `datetime`, `boolean` (NOT `timestamp`)
- Boolean samples: `samples: ["true", "false"]` (strings, not booleans)
- Entity keys must reference dimension `name` fields

### Schema Files (auto-generated by oxy sync)
- Use `sample:` (singular)
- Use `entities: []` (empty array)

### SQL Files
- Column names with spaces: `"Column Name"` (double quotes)
- CSV filenames: `"filename.csv"` (double quotes)
- String values: `'value'` (single quotes)

### Config.yml
- Dataset path must match CSV location: `dataset: db/` if CSV is in `db/` directory

## Key Lessons Learned

1. **Always use the oxy-semantic-layer skill** for creating semantic layer files
2. **Run `oxy sync` first** to auto-generate schema files
3. **Check dataset path** in config.yml matches CSV file location
4. **Escape column names properly** using single quotes for YAML and double quotes for SQL
5. **Use correct data types** (datetime not timestamp)
6. **Samples must be strings** even for booleans
7. **Test incrementally** - validate, build, then test queries
8. **Use `oxy build`** to validate semantic layer (not `oxy validate`)

## Reference Documentation

- Semantic Layer: https://docs.oxy.tech/learn-about-oxy/semantic-layer
- Views: https://docs.oxy.tech/learn-about-oxy/semantic-layer/views
- Topics: https://docs.oxy.tech/learn-about-oxy/semantic-layer/topics
- DeepWiki (fallback): https://deepwiki.com/oxy-hq/oxy

---

This guide captures all learnings from the sleep data implementation and provides a reliable bootstrap process for new CSV-based analytics projects.
