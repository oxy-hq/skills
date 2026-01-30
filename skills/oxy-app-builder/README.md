# Oxy App Builder Skill

A Claude Agent Skill for building Oxy data apps (`*.app.yml`) - interactive dashboards that combine data tasks with visualizations.

## What is this?

This skill provides Claude with specialized knowledge for creating and editing Oxy app files. Oxy apps define:

1. **Tasks** - Data operations (SQL queries, workflows, semantic queries, AI agents)
2. **Displays** - Visualizations (tables, charts, markdown content)

The core mental model: **Task -> Output -> Display**

## Skill Structure

```
oxy-app-builder/
├── SKILL.md              # Main skill instructions
├── README.md             # This file
├── QUICK-REFERENCE.md    # Schema cheat sheet
└── templates/
    └── (example templates)
```

## When Claude Uses This Skill

Claude automatically activates this skill when you:

- Ask to create a data dashboard or app
- Want to build reports or analytics interfaces
- Need to visualize data with charts and tables
- Ask to edit an existing `*.app.yml` file
- Mention "Oxy app" or "app.yml"

## What You Can Build

### Simple SQL Dashboard
```yaml
name: sales_overview

tasks:
  - name: sales_summary
    type: execute_sql
    database: clickhouse
    sql_query: |
      SELECT region, SUM(amount) as total
      FROM orders GROUP BY region

display:
  - type: bar_chart
    title: "Sales by Region"
    data: sales_summary
    x: region
    y: total
```

### Multi-Source Analytics
- SQL queries from any database
- Workflow orchestration
- Semantic layer queries
- AI-powered insights

### Supported Displays
- **Tables** - Tabular data views
- **Line Charts** - Trends over time
- **Bar Charts** - Category comparisons
- **Pie Charts** - Distribution views
- **Markdown** - Rich text with templating

## Usage Examples

Ask Claude:

- "Create a sales dashboard showing monthly revenue trends"
- "Build an app that shows customer segmentation with pie charts"
- "Edit my existing app to add a new table display"
- "Create a multi-source dashboard combining SQL and semantic queries"
- "Build an executive dashboard with KPIs and trend analysis"

## Plan-First Workflow

When you ask to create an app, Claude will:

1. **Ask clarifying questions** (if needed)
2. **Present a plan** including:
   - App purpose
   - Data sources
   - Tasks with expected outputs
   - Display layout
3. **Wait for your approval**
4. **Write the YAML file**
5. **Validate the result**

## Quick Commands

```bash
# Run an app
oxy run my_dashboard.app.yml

# Validate an app
oxy validate my_dashboard.app.yml

# List existing apps
find . -name "*.app.yml"
```

## Key Concepts

### Task Types
| Type | Use Case |
|------|----------|
| `execute_sql` | Direct database queries |
| `workflow` | Multi-step pipelines |
| `semantic_query` | Business-friendly semantic layer queries |
| `agent` | AI-powered analysis |

### Display Types
| Type | Best For |
|------|----------|
| `table` | Detailed data views |
| `line_chart` | Trends over time |
| `bar_chart` | Comparing categories |
| `pie_chart` | Showing proportions |
| `markdown` | Headers, text, AI-generated content |

## Documentation

- [Oxy Documentation](https://docs.oxy.tech/)
- [Apps Guide](https://docs.oxy.tech/learn-about-oxy/apps)

## Version

Created: 2025-01-29
Compatible with: Oxy apps (`*.app.yml`)
