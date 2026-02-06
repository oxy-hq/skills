# Oxy Workflow Builder Quick Reference

## The Hierarchy (REMEMBER THIS!)

1. **Semantic Queries** - Use if data is in semantic layer ✅ PREFERRED
2. **SQL/Workflows** - Use if deterministic logic needed 🔄 FALLBACK
3. **AI Agents** - Use only if AI reasoning required 🤖 LAST RESORT

## Commands

```bash
# Check semantic layer first (always!)
find semantics/views -name "*.view.yml"
find semantics/topics -name "*.topic.yml"
oxy semantic-engine --dev-mode

# SQL queries
oxy run query.sql                    # Execute SQL
oxy run query.sql --dry-run          # Test without executing
oxy run query.sql -v key=value       # With variables

# Workflows
oxy run workflow.workflow.yml        # Execute workflow

# Agents
oxy run agent.agent.yml "question"   # Run with prompt

# Validation
oxy validate --file=<path>           # Validate individual YAML file
oxy validate                         # Validate all YAML configs (agents, workflows, apps)
oxy build                            # Validate semantic layer

# Discovery
find . -name "*.sql" -not -path "*/.*"
find . -name "*.workflow.yml"
find . -name "*.agent.yml"
```

## Decision Matrix

| Need | Use | File Type |
|------|-----|-----------|
| Business reporting | Semantic queries | None (natural language) |
| Data in semantic layer | Semantic queries | None |
| Parameterized query | SQL file | `*.sql` |
| Multi-step pipeline | Workflow | `*.workflow.yml` |
| ETL operations | Workflow | `*.workflow.yml` |
| AI reasoning needed | Agent | `*.agent.yml` |
| Exploratory analysis | Agent | `*.agent.yml` |

## File Templates Quick View

### SQL File
```sql
-- query_name.sql
-- Description: What this query does
-- Variables:
--   - var1: Description
--   - var2: Description

SELECT column1, column2
FROM {{ databases.db_name.schema }}.table
WHERE date >= '{{ start_date }}'
  AND date <= '{{ end_date }}'
ORDER BY column1;
```

### Workflow File
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/oxy-hq/oxy/refs/heads/main/json-schemas/workflow.json

name: workflow_name
description: "What this workflow does"

tasks:
  - name: step_1
    description: "Extract data"
    type: execute_sql
    database: my_database
    sql_query: |
      SELECT * FROM source_table
      WHERE condition = true

  - name: step_2
    description: "Transform data"
    type: execute_sql
    database: my_database
    sql_query: |
      SELECT
        column1,
        SUM(column2) as total
      FROM {{ step_1 }}
      GROUP BY column1
```

### Agent File
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/oxy-hq/oxy/refs/heads/main/json-schemas/agent.json

name: agent_name
description: "What this agent analyzes"

model: "claude-3-5-sonnet-20241022"

system_instructions: |
  You are a [domain] expert. Your role:
  - Analyze data
  - Identify patterns
  - Provide insights

tools:
  - type: database
    database: clickhouse
    description: "Database access"
```

## Common Patterns

### Date Filtering (SQL)
```sql
WHERE created_at >= '{{ start_date }}'
  AND created_at < '{{ end_date }}'
```

### Dynamic Schema Reference (SQL)
```sql
FROM {{ databases.clickhouse.restaurant_analytics }}.orders
```

### Conditional Logic (SQL)
```sql
{% if include_cancelled %}
WHERE status IN ('completed', 'cancelled')
{% else %}
WHERE status = 'completed'
{% endif %}
```

### ETL Pipeline (Workflow)
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/oxy-hq/oxy/refs/heads/main/json-schemas/workflow.json

tasks:
  - name: extract
    type: execute_sql
    database: my_database
    sql_query: SELECT * FROM source WHERE date = '{{ date }}'
  - name: transform
    type: execute_sql
    database: my_database
    sql_query: SELECT clean_column FROM {{ extract }}
  - name: load
    type: execute_sql
    database: my_database
    sql_query: INSERT INTO dest SELECT * FROM {{ transform }}
```

### Task Reference (Workflow)
```yaml
sql_query: SELECT * FROM {{ previous_task_name }}
```

## Validation Workflow

1. Write file
2. Run `oxy validate --file=<path>` to validate the individual file
3. For SQL: `oxy run file.sql --dry-run`
4. Fix any errors
5. Run for real
6. Verify results

## Best Practices Checklist

### SQL Files
- ✅ Header comments with description
- ✅ Document required variables
- ✅ Use Jinja2 for parameters
- ✅ Test with --dry-run first
- ✅ Descriptive file names

### Workflows
- ✅ Description for workflow and each task
- ✅ Named tasks clearly
- ✅ Test each task's SQL separately
- ✅ Reference previous tasks correctly with `{{ task_name }}`
- ✅ One pipeline per file

### Agents
- ✅ Clear system prompt
- ✅ Only necessary tools
- ✅ Focused purpose
- ✅ Test with real questions
- ✅ Document expected use cases

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Variable not defined" | Missing -v parameter | Add `-v var=value` |
| "Table not found" | Wrong table reference | Check `.databases/` schemas |
| "Task not found" | Wrong task name in reference | Fix `{{ task_name }}` reference |
| "Agent requires prompt" | No question provided | Add question to command |
| "SQL syntax error" | Invalid SQL | Test with --dry-run |

## When to Use What

### Use Semantic Queries When:
- ✅ Data is in semantic layer views
- ✅ Business users need to query
- ✅ Standard reporting needed
- ✅ Cross-view joins required

### Use SQL When:
- ✅ Data not in semantic layer yet
- ✅ Custom calculations needed
- ✅ One-off parameterized query
- ✅ Direct database access required

### Use Workflows When:
- ✅ Multi-step data pipeline
- ✅ ETL operations
- ✅ Orchestrating multiple queries
- ✅ Results depend on previous tasks

### Use Agents When:
- ✅ AI reasoning required
- ✅ Exploratory analysis
- ✅ Natural language interaction
- ✅ Dynamic query generation
- ✅ Pattern recognition needed

## Remember: Always Start Here!

```bash
# 1. Check semantic layer FIRST
find semantics/views -name "*.view.yml"

# 2. If views exist, use semantic queries!
oxy semantic-engine --dev-mode

# 3. Only use SQL/workflows/agents if semantic layer insufficient
```

## File Organization

```
project/
├── semantics/
│   ├── views/          # Semantic layer views
│   └── topics/         # Semantic layer topics
├── queries/            # SQL files
│   ├── reports/
│   └── analysis/
├── workflows/          # Workflow files
│   ├── etl/
│   └── pipelines/
└── agents/             # Agent files
    ├── exploratory/
    └── insights/
```

## Naming Conventions

- Use `snake_case`
- Be descriptive: `monthly_revenue_report.sql`
- Avoid generic: `query1.sql`, `agent.agent.yml`
- Include purpose in name
- Group by domain/function
