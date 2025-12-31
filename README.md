# Oxy Skills for Claude Code

Official Claude Code plugin for building Oxy analytics projects. Provides intelligent skills, commands, and agents for working with semantic layers, workflows, and AI-powered data analysis.

## What's Included

### 🎯 Skills (Auto-activate)

**oxy-semantic-layer**
Builds semantic layer files (views and topics) for natural language analytics.

Auto-activates when you ask to:

- Create view or topic files
- Validate semantic layer configuration
- Work with database schemas

**oxy-workflow-builder**
Builds workflows, SQL queries, and agents following Oxy best practices.

Auto-activates when you ask to:

- Create data pipelines
- Write SQL queries
- Build analysis agents
- Design workflows

### ⚡ Commands (Quick actions)

- `/oxy:validate` - Validate all configuration files
- `/oxy:build` - Build semantic layer and embeddings
- `/oxy:sync` - Sync database metadata and schemas
- `/oxy:test` - Run evaluation tests on agents/workflows

### 🤖 Agents (Autonomous helpers)

**config-validator**
Proactively validates Oxy configuration files, catches errors before runtime, and suggests fixes.

## Installation

### From Marketplace

```bash
# Add the Oxy plugin marketplace
/plugin marketplace add oxy-hq/skills

# Install the plugin
/plugin install oxy-skills@oxy-hq
```

### From Local Directory

```bash
claude --plugin-dir /path/to/skills
```

## Prerequisites

- [Oxy CLI](https://oxy.tech) installed and in PATH
- An Oxy project with `config.yml`
- Database connections configured (for semantic layer features)
- API keys for LLM providers (OpenAI, Anthropic, etc.)

## Usage

### Building Semantic Layers

Skills auto-activate based on your requests:

```text
"Create a semantic layer for my sales data"
```

The **oxy-semantic-layer** skill loads and guides you through:

1. Running `oxy sync` to extract database schemas
2. Creating view files with entities, dimensions, and measures
3. Creating topic files to organize views
4. Validating with `oxy build`

### Creating Workflows

```text
"Build a workflow to analyze customer churn"
```

The **oxy-workflow-builder** skill loads and helps you:

1. Choose the right tool (semantic queries, SQL, or AI agents)
2. Design multi-step workflows
3. Write parameterized SQL with Jinja2 templates
4. Create AI agents for complex analysis

### Quick Validation

Use commands for fast operations:

```bash
/oxy:validate          # Check all config files
/oxy:build            # Compile semantic layer
/oxy:sync bigquery    # Sync a specific database
/oxy:test my-agent.agent.yml
```

### Validating Configurations

When you create or edit Oxy YAML files:

```text
"Can you check if my view file is correct?"
```

The **config-validator** agent analyzes your files for:

- YAML syntax errors
- Schema violations
- Entity key reference issues
- Invalid SQL expressions
- Missing required fields

## Common Workflows

### New Project Setup

```text
1. User: "Initialize a new Oxy project for PostgreSQL analytics"
2. Skills guide through: oxy init → configure databases → set API keys
3. Command: /oxy:sync to extract schemas
4. Skill helps create first semantic layer views
5. Command: /oxy:build to compile
```

### Semantic Layer Development

```text
1. Command: /oxy:sync to update database schemas
2. User: "Create views for my orders and customers tables"
3. Skill generates view files with entities, dimensions, measures
4. Command: /oxy:validate to check syntax
5. Command: /oxy:build to compile
6. Test with semantic queries
```

### Workflow Development

```text
1. User: "Create a workflow to aggregate daily sales"
2. Skill helps design ETL pipeline
3. Skill generates .workflow.yml with multiple steps
4. Command: /oxy:test workflow.yml
5. Run with: oxy run workflow.yml
```

## File Structure

After installation, the plugin provides:

```text
skills/
├── oxy-semantic-layer/
│   ├── SKILL.md              # Main skill content
│   ├── README.md             # User documentation
│   ├── QUICK-REFERENCE.md    # Syntax reference
│   ├── view-template.yml     # View file template
│   └── topic-template.yml    # Topic file template
└── oxy-workflow-builder/
    ├── SKILL.md
    ├── README.md
    ├── QUICK-REFERENCE.md
    ├── workflow-template.yml
    ├── agent-template.yml
    └── sql-template.sql

commands/
├── validate.md     # /oxy:validate
├── build.md        # /oxy:build
├── sync.md         # /oxy:sync
└── test.md         # /oxy:test

agents/
└── config-validator.md
```

## Examples

### Semantic Layer View

```yaml
name: customer_orders
description: "Customer order transactions"
datasource: "postgres"
table: "public.orders"

entities:
  - name: order
    type: primary
    key: order_id

  - name: customer
    type: foreign
    key: customer_id

dimensions:
  - name: order_id
    type: string
    expr: order_id

  - name: customer_id
    type: string
    expr: customer_id

  - name: order_date
    type: date
    expr: order_date

measures:
  - name: total_orders
    type: count
    synonyms: ["order count"]

  - name: total_revenue
    type: sum
    expr: order_amount
    synonyms: ["revenue", "sales"]
```

### Workflow

```yaml
name: daily_aggregation
description: "Aggregate sales by day"

steps:
  - name: extract
    sql: SELECT * FROM orders WHERE date = '{{ date }}'

  - name: aggregate
    sql: |
      SELECT
        date,
        SUM(amount) as total
      FROM {{ steps.extract.result }}
      GROUP BY date
```

## Troubleshooting

**Skills not loading?**

- Verify plugin is enabled in Claude Code settings
- Check that skill SKILL.md files exist
- Restart Claude Code session

**Commands not appearing?**

- Run `/help` to see all available commands
- Ensure Oxy CLI is installed: `oxy --version`
- Check command files have proper frontmatter

**Validation errors?**

- Use `/oxy:validate` to see detailed errors
- Check entity keys reference dimension names (not columns)
- Verify all view files referenced in topics exist
- Ensure database connections in config.yml are correct

## Resources

- [Oxy Documentation](https://docs.oxy.tech)
- [Semantic Layer Guide](https://docs.oxy.tech/learn-about-oxy/semantic-layer)
- [Workflows Guide](https://docs.oxy.tech/learn-about-oxy/automations)
- [Oxy DeepWiki](https://deepwiki.com/oxy-hq/oxy)
- [GitHub Repository](https://github.com/oxy-hq/skills)

## Contributing

This is the official Oxy plugin maintained by the Oxy team. For issues or feature requests, please visit the [GitHub repository](https://github.com/oxy-hq/skills/issues).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Updates

```bash
/plugin update oxy-skills
```

---

Built with ❤️ by the [Oxy Team](https://oxy.tech)
