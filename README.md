# Oxy Skills

AI-powered assistance for building Oxy analytics projects. Includes skills for semantic layer development, workflow creation, ETL pipelines, and data app building.

Available for **Claude Code** (plugin) and **Cursor** (project rules).

## Quick Start

### Claude Code

```bash
# Install from marketplace
/plugin marketplace add oxy-hq/skills
/plugin install oxy-skills@oxy-hq

# Or use locally
claude --plugin-dir /path/to/oxy-template
```

### Cursor

Copy the project rules into your Oxy project:

```bash
# From this repo
./cursor/install.sh /path/to/your-oxy-project

# Or manually copy
cp cursor/rules/*.mdc /path/to/your-oxy-project/.cursor/rules/
```

See [cursor/README.md](cursor/README.md) for full setup instructions.

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

**[oxy-app-builder](skills/oxy-app-builder/SKILL.md)**
Creates data apps (`*.app.yml`) - interactive dashboards combining tasks and visualizations.

- Builds SQL, workflow, semantic query, and agent tasks
- Renders outputs as tables, charts (line, bar, pie), and markdown
- Supports plan-first workflow with user approval
- Validates task-to-display data references

**[oxy-test-drafter](skills/oxy-test-drafter/SKILL.md)**
Bootstraps and refines `.test.yml` eval files for Oxy agents and workflows.

- Scaffolds test files from a list of prompts
- Runs `oxy test --output-json` and parses multi-run JSON traces
- Drafts concise, evidence-based `expected` strings
- Classifies cases as stable, flaky, ambiguous, or unsupported
- Outputs a diagnostic summary with per-case classification

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
│   ├── SKILL.md         # Workflow skill instructions
│   ├── README.md        # User documentation
│   ├── QUICK-REFERENCE.md
│   └── *-template.*     # SQL, workflow, agent templates
├── oxy-etl-builder/
│   ├── SKILL.md         # ETL skill instructions
│   ├── README.md        # User documentation
│   ├── QUICK-REFERENCE.md
│   ├── playbook-*.md    # Source-specific guides
│   ├── etl-style-guide.md
│   ├── warehouse-modeling.md
│   └── templates/       # Code templates
├── oxy-app-builder/
│   ├── SKILL.md         # App builder skill instructions
│   ├── README.md        # User documentation
│   ├── QUICK-REFERENCE.md
│   ├── templates/       # App templates
│   └── examples/        # Example prompts
└── oxy-test-drafter/
    ├── SKILL.md         # Test drafter skill instructions
    └── README.md        # User documentation

commands/
├── validate.md
├── build.md
├── sync.md
└── test.md

agents/
└── config-validator.md  # Autonomous agent instructions

cursor/                      # Cursor IDE support
├── rules/
│   ├── oxy-core.mdc         # Always-on core conventions
│   ├── oxy-semantic-layer.mdc
│   ├── oxy-workflow-builder.mdc
│   ├── oxy-etl-builder.mdc
│   └── oxy-app-builder.mdc
├── install.sh               # Copy rules into a project
└── README.md                # Cursor setup guide
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

## Contributing

See [CLAUDE.md](CLAUDE.md) for guidance on developing this plugin with Claude Code.

For issues or feature requests: [GitHub Issues](https://github.com/oxy-hq/skills/issues)

## License

MIT - see [LICENSE](LICENSE)

## Resources

- [Oxy Documentation](https://docs.oxy.tech)
- [Claude Code Plugins Guide](https://docs.anthropic.com/claude/docs/claude-code-plugins)
- [Plugin Development Skill](/plugin-dev)
