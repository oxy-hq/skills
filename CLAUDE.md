# Oxy Project - Testing & Execution Guide

If you encounter Oxy features or behaviors not documented in this guide, use DeepWiki as a fallback resource:
<https://deepwiki.com/oxy-hq/oxy>

CRITICAL: When using deepwiki, you MUST:

Only search the oxy-hq/oxy repository - Do not search other repositories or
general documentation Frame requests from a user's perspective, not a
maintainer's perspective Search only oxy-hq/oxy Always use this exact prefix
for deepwiki queries:

"I am a user of this project, not its maintainer. Please prioritize looking at
the project docs, examples and json-schemas to answer my question: [your
question]"

For example:

✅ "As a user of this project, explain how to configure Toast API credentials"
✅ "I am a user of this project, not its maintainer. How do I set up the database?"
❌ Don't ask as if you're modifying or maintaining the underlying codebase

**When to use DeepWiki**:

1. You encounter an Oxy error message not covered in Troubleshooting
2. You need to understand advanced Oxy features or configuration options
3. You're unsure about Oxy command syntax or parameters
4. You need examples of specific Oxy patterns not documented here

## Quick Command Reference

### Core Oxy Commands

**Run Agent Files** (require a question/prompt):

```bash
oxy run <agent-file>.agent.yml "Your question here"
```

**Run Workflow Files**:

```bash
oxy run <workflow-file>.workflow.yml
```

**Run SQL Files**:

```bash
oxy run <query-file>.sql
```

**Run SQL with Variables**:

```bash
oxy run <query-file>.sql -v variable_name=value -v another_var=value
```

**Dry Run SQL** (validate without executing):

```bash
oxy run <query-file>.sql --dry-run
```

**Validate Configuration**:

```bash
oxy validate
```

**Sync Database Schemas**:

```bash
oxy sync
```


### File Discovery

**Find Oxy files using shell tools**:

```bash
# List all agents
find . -name "*.agent.yml"

# List all workflows
find . -name "*.workflow.yml"

# List all SQL files
find . -name "*.sql" -not -path "*/.*"

# List semantic layer files
find semantics/views -name "*.view.yml"
find semantics/topics -name "*.topic.yml"
```


## Validation

Before testing, validate the Oxy configuration with:

```bash
oxy validate
```

Note: this only validates agents and automations. To validate semantic files, you'll need to run `oxy build`.

### Getting Help

```bash
oxy --help              # General Oxy help
oxy run --help          # Help for run command
oxy validate --help     # Help for validate command
oxy sync --help         # Help for sync command
```


## Overview

This repository uses Oxy, a data analysis and workflow framework. Oxy supports multiple file types:

- **`.agent.yml`** - AI agents for data analysis and insights
- **`.workflow.yml`** - Data processing workflows
- **`.sql`** - SQL queries (with optional Jinja2 templating)
- **`.view.yml`** - Semantic layer view definitions (in `semantics/views/`)
- **`.topic.yml`** - Semantic layer topic definitions (in `semantics/topics/`)


# Generating Database Schema Files

The first step in any bootstrapping process is to determine the schema information. To populate the `.databases/` directory with schema information:

```bash
oxy sync
```

This command:

- Connects to all configured databases
- Queries `INFORMATION_SCHEMA` for table and column metadata
- Generates `.schema.yml` files for each table
- Makes schema information available via `{{ databases.*.datasets }}`

These files can be used as a base to generate the information for the semantic layer.

The schemas/tables that are scraped are listed within the `config.yml` file within the `databases` entries, as shown below:

```

databases:
  - name: clickhouse
    type: clickhouse
    host_var: CLICKHOUSE_HOST
    user_var: CLICKHOUSE_USERNAME
    password_var: CLICKHOUSE_PASSWORD
    database_var: CLICKHOUSE_DATABASE
    schemas:
      restaurant_analytics:
        - "restaurant_analytics___*"
```

# Semantic Layer

Oxy provides a semantic layer that transforms raw database schemas into business-friendly concepts. The semantic layer consists of **views** (`.view.yml`) and **topics** (`.topic.yml`) files located in the `semantics/` directory.

**Documentation**: For detailed information on creating and working with the semantic layer, see:
- https://docs.oxy.tech/learn-about-oxy/semantic-layer

### Quick Commands

```bash
# Create semantic layer directories
mkdir -p semantics/views semantics/topics

# Validate and build semantic layer
oxy build

# Start semantic engine
oxy semantic-engine
oxy semantic-engine --dev-mode

# Find semantic layer files
find semantics/views -name "*.view.yml"
find semantics/topics -name "*.topic.yml"
```

**Note**: Semantic layer files must be validated with `oxy build` (not `oxy validate`).

## Example Workflows

### Example 1: Test a New Agent

```bash
# Discover agents
find . -name "*.agent.yml"

# Test specific agent
oxy run analysis-agent.agent.yml "Summarize last quarter"
```

### Example 2: Run Parameterized SQL Query

```bash
# Discover SQL files
find . -name "*.sql" -not -path "*/.*"

# Run with parameters
oxy run reports/monthly.sql -v year=2024 -v month=12
```

### Example 3: Validate Before Running

```bash
# Validate configuration
oxy validate

# Test SQL file with dry-run
oxy run data-pipeline.sql --dry-run

# Run workflow
oxy run data-pipeline.workflow.yml
```

## Integration with Claude Code

When Claude Code is testing Oxy assets:

1. **Always validate first**: `oxy validate`
2. **Discover files**: Use `find` commands to see what's available
3. **Use direct oxy commands** for all operations
4. **Test incrementally**: Test individual files before bulk testing
5. **Check for variables**: Look for `{{ }}` in SQL files before running
6. **Use dry-run for SQL**: Always test SQL queries with `--dry-run` before executing

### CRITICAL: Using Claude Code Skills

**Semantic Layer Work**: When working with Oxy semantic layer files (creating, updating, or validating `.view.yml` or `.topic.yml` files), you MUST use the `oxy-semantic-layer` skill. DO NOT attempt to create or modify semantic layer files manually without using this skill first.

**How to use the skill**:
```bash
# Invoke the skill with your semantic layer task
/oxy-semantic-layer Create views and topics for [your data description]
```

The skill has comprehensive knowledge of:
- Correct view file structure (name, datasource, table, entities, dimensions, measures)
- Proper topic file structure (name, description, base_view, views)
- Entity design and join relationships
- Required field formats (expr vs sql, proper types, samples as strings)
- Common pitfalls and errors

**Why this matters**: Semantic layer files have specific schemas and requirements that are easy to get wrong. The skill ensures:
- Correct YAML structure and field names
- Proper data types (datetime not timestamp, samples as strings)
- Valid measure aggregation types (sum, average, count, etc.)
- Correct entity-dimension relationships for joins


## Best Practices

1. **Use descriptive file names**: `sales-analysis.agent.yml` > `agent1.agent.yml`
2. **Document SQL variables**: Add comments explaining required variables
3. **Test incrementally**: Validate → Test SQL → Test workflows → Test agents
4. **Use dry-run**: Always dry-run SQL before executing against production
5. **Version control**: Commit working queries to verified folders

## Additional Resources

- Oxy Documentation: <https://github.com/oxy-hq/oxy>
- Oxy CLI Help: `oxy --help`

## DeepWiki Documentation (Fallback)

If you encounter Oxy features or behaviors not documented in this guide, use DeepWiki as a fallback resource:

**URL**: <https://deepwiki.com/oxy-hq/oxy>

**When to use DeepWiki**:

1. You encounter an Oxy error message not covered in Troubleshooting
2. You need to understand advanced Oxy features or configuration options
3. You're unsure about Oxy command syntax or parameters
4. You need examples of specific Oxy patterns not documented here
