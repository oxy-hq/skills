# Oxy Cursor Rules

Cursor project rules that replicate the Oxy Claude Code plugin experience. These rules give Cursor's AI agent the same Oxy knowledge as the Claude Code skills plugin — semantic layer building, workflow construction, ETL pipelines, and data app dashboards.

## Quick Install

```bash
# From the skills repo root
./cursor/install.sh /path/to/your/oxy-project

# Or copy manually
mkdir -p /path/to/your/oxy-project/.cursor/rules
cp cursor/rules/*.mdc /path/to/your/oxy-project/.cursor/rules/
```

## Prerequisites

- [Cursor](https://cursor.com) IDE
- `oxy` CLI installed and on your PATH ([install guide](https://docs.oxy.tech))
- An Oxy project with `config.yml`

## Rules Inventory

| Rule | Type | Globs | What It Covers |
|------|------|-------|----------------|
| `oxy-core.mdc` | Always | _(all chats)_ | File conventions, Oxy hierarchy, CLI commands, validation loop |
| `oxy-semantic-layer.mdc` | Auto-attached | `*.view.yml`, `*.topic.yml`, `semantics.yml` | Views, topics, entities, dimensions, measures |
| `oxy-workflow-builder.mdc` | Auto-attached | `*.workflow.yml`, `*.agent.yml`, `*.sql` | SQL files, workflows, AI agents |
| `oxy-etl-builder.mdc` | Auto-attached | `etl/**`, `pyproject.toml` | DLT pipelines, API connectors, spreadsheet ingestion |
| `oxy-app-builder.mdc` | Auto-attached | `*.app.yml` | Data app dashboards, tasks, displays, charts |

## How Rules Activate

- **Always rules** (`oxy-core.mdc`) load in every Cursor chat session automatically.
- **Auto-attached rules** load when you open or reference files matching their glob patterns. For example, editing a `*.view.yml` file automatically loads the semantic layer rule.

## What's Included

These rules port the full content of the Claude Code Oxy skills plugin:

| Claude Code Component | Cursor Equivalent |
|---|---|
| `oxy-semantic-layer` skill | `oxy-semantic-layer.mdc` rule |
| `oxy-workflow-builder` skill | `oxy-workflow-builder.mdc` rule |
| `oxy-etl-builder` skill | `oxy-etl-builder.mdc` rule |
| `oxy-app-builder` skill | `oxy-app-builder.mdc` rule |
| `/oxygen:validate`, `/oxygen:build`, `/oxygen:sync`, `/oxygen:test` commands | CLI reference in `oxy-core.mdc` |
| `config-validator` agent | Validation loop behavior in `oxy-core.mdc` |

## Differences from Claude Code Plugin

| Feature | Claude Code | Cursor |
|---------|------------|--------|
| Skill activation | Auto-activating skills with frontmatter | Auto-attached rules via globs |
| Slash commands | `/oxygen:validate`, `/oxygen:build`, etc. | Ask the agent to run `oxygen validate`, `oxygen build`, etc. |
| Config validator agent | Autonomous agent triggered by file changes | Validation reminders in always-on rule |
| ETL playbooks | Loaded as companion files | Referenced by name (check skills repo) |
| DeepWiki fallback | Queried automatically for unknown features | Not included (rules are self-contained) |

## Updating Rules

To update rules after the skills repo changes:

```bash
cd /path/to/skills-repo
git pull
./cursor/install.sh /path/to/your/oxy-project
```
