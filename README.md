# Oxy Skills for Claude Code

A Claude Code plugin providing intelligent assistance for building Oxy analytics projects. Includes auto-activating skills, slash commands, and autonomous agents for semantic layer development, workflow creation, and configuration validation.

## Quick Start

```bash
# Install from marketplace
/plugin marketplace add oxy-hq/skills
/plugin install oxy-skills@oxy-hq

# Or use locally
claude --plugin-dir /path/to/oxy-template
```

## Plugin Components

### Skills (Auto-Activate)

**[oxy-semantic-layer](skills/oxy-semantic-layer/SKILL.md)**
Builds semantic layer files (views and topics) for natural language analytics.

- Analyzes database schemas from `.databases/`
- Creates `*.view.yml` files with entities, dimensions, and measures
- Generates `*.topic.yml` files to organize views
- Validates with `oxy build`

**[oxy-workflow-builder](skills/oxy-workflow-builder/SKILL.md)**
Creates data workflows, SQL queries, and AI agents following Oxy patterns.

- Designs multi-step ETL pipelines
- Generates parameterized SQL with Jinja2
- Creates `*.workflow.yml` and `*.agent.yml` files
- Tests with `oxy run`

**[oxy-etl-builder](skills/oxy-etl-builder/SKILL.md)**
Builds ETL pipelines using DLT (data-load-tools) for loading data into warehouses.

- Sets up API connectors (Toast, Square, Stripe, etc.)
- Creates spreadsheet/file ingestion pipelines
- Generates `etl/sources/`, `etl/runners/`, and transform files
- Supports ClickHouse, Snowflake, MotherDuck, DuckDB

### Commands

| Command         | Description                              |
| --------------- | ---------------------------------------- |
| `/oxy:validate` | Validate all Oxy configuration files     |
| `/oxy:build`    | Build semantic layer and embeddings      |
| `/oxy:sync`     | Sync database metadata and schemas       |
| `/oxy:test`     | Run evaluation tests on agents/workflows |

### Agents

**[config-validator](agents/config-validator.md)**
Autonomous validator that checks Oxy YAML files for syntax errors, schema violations, and reference issues.

## Architecture

```text
.claude-plugin/
├── plugin.json          # Plugin manifest
└── marketplace.json     # Marketplace metadata

skills/
├── oxy-semantic-layer/
│   ├── SKILL.md         # Skill instructions for Claude
│   ├── README.md        # User-facing documentation
│   ├── QUICK-REFERENCE.md
│   └── *.yml            # Templates
├── oxy-workflow-builder/
│   └── ...
└── oxy-etl-builder/
    ├── SKILL.md         # ETL skill instructions
    ├── README.md        # User documentation
    ├── playbook-*.md    # Source-specific guides
    └── templates/       # Code templates

commands/
├── validate.md          # Slash command implementations
├── build.md
├── sync.md
└── test.md

agents/
└── config-validator.md  # Autonomous agent instructions

examples/
└── demo-project/        # Sample Oxy project
    ├── config.yml
    ├── semantics.yml
    ├── workflows/
    └── example_sql/
```

## Development

### Prerequisites

- Claude Code CLI
- Oxy CLI (`oxy --version`)
- An Oxy project with `config.yml`

### File Conventions

**Skill files** (`skills/*/SKILL.md`):

```markdown
---
name: skill-name
description: When this skill activates (user-facing)
---

# Skill Title

Instructions for Claude on how to execute this skill...
```

**Command files** (`commands/*.md`):

```markdown
---
name: command-name
description: What this command does
---

#!/bin/bash
# Command implementation
```

**Agent files** (`agents/*.md`):

```markdown
---
name: agent-name
description: When this agent should activate
tools: [Read, Grep, Bash]
---

# Agent Instructions

Autonomous agent behavior...
```

## Examples

See [examples/demo-project/](examples/demo-project/) for:

- Sample semantic layer views
- Multi-step workflows
- AI agent configurations
- Parameterized SQL queries

## Contributing

See [CLAUDE.md](CLAUDE.md) for guidance on developing this plugin with Claude Code.

For issues or feature requests: [GitHub Issues](https://github.com/oxy-hq/skills/issues)

## License

MIT - see [LICENSE](LICENSE)

## Resources

- [Oxy Documentation](https://docs.oxy.tech)
- [Claude Code Plugins Guide](https://docs.anthropic.com/claude/docs/claude-code-plugins)
- [Plugin Development Skill](/plugin-dev)
