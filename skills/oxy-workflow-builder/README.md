# Oxy Workflow Builder Skill

A Claude Agent Skill for building Oxy workflows, SQL queries, and AI agents with a hierarchy-driven approach.

## What is this?

This skill provides Claude with specialized knowledge for creating Oxy data pipelines and analysis tools, following a clear hierarchy:

1. **Semantic Queries** (preferred) - Use the semantic layer for business-friendly data access
2. **SQL Queries & Workflows** (fallback) - Use for deterministic data operations
3. **AI Agents** (last resort) - Use only when AI reasoning is required

## Skill Structure

This skill follows the [Claude Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) architecture:

```
oxy-workflow-builder/
├── SKILL.md                  # Main skill instructions (Level 2: loaded when triggered)
├── workflow-template.yml     # Template for workflow files (Level 3: loaded as needed)
├── sql-template.sql          # Template for SQL files (Level 3: loaded as needed)
├── agent-template.yml        # Template for agent files (Level 3: loaded as needed)
├── QUICK-REFERENCE.md        # Quick reference guide (Level 3: loaded as needed)
└── README.md                 # This file (documentation)
```

### Progressive Loading

The skill uses progressive disclosure to minimize context usage:

1. **Level 1 (Metadata)**: Claude knows this skill exists and when to use it (~100 tokens)
2. **Level 2 (Instructions)**: When triggered, Claude reads `SKILL.md` for detailed guidance (~6k tokens)
3. **Level 3+ (Resources)**: Claude accesses templates and references only when needed (on-demand)

## When Claude Uses This Skill

Claude automatically activates this skill when you:

- Ask to build data pipelines or workflows
- Need to write SQL queries for analysis
- Want to create AI agents for data analysis
- Ask about extracting insights from data
- Need help choosing between semantic queries, SQL, or agents

## The Hierarchy

### 1. Semantic Queries (Preferred)

Use semantic queries whenever the semantic layer has the needed data:
- Most maintainable approach
- Business-friendly natural language
- No SQL knowledge required
- Automatic cross-view joins

### 2. SQL & Workflows (Fallback)

Use SQL/workflows when:
- Data not yet in semantic layer
- Need custom transformations
- Building ETL pipelines
- Need parameterized queries

### 3. AI Agents (Last Resort)

Use agents only when:
- AI reasoning is required
- Exploratory analysis needed
- Dynamic query generation based on context
- Natural language understanding necessary

## Key Capabilities

### SQL Files (`*.sql`)

- Single-query execution
- Jinja2 templating for parameters
- Dry-run testing before execution
- Direct database access

### Workflow Files (`*.workflow.yml`)

- Multi-step data pipelines
- Orchestrate multiple queries
- Reference previous step results
- ETL operations

### Agent Files (`*.agent.yml`)

- AI-powered data analysis
- Natural language interaction
- Access to databases and tools
- Reasoning and insights generation

## Usage Examples

Ask Claude:

- "Create a workflow to aggregate daily sales data"
- "Write a SQL query to find top customers by revenue"
- "Build an agent to analyze customer behavior trends"
- "Should I use semantic queries or SQL for this report?"

Claude will recommend the right approach based on the hierarchy.

## Quick Commands

```bash
# Check semantic layer first
find semantics/views -name "*.view.yml"
oxygen semantic-engine --dev-mode

# Run SQL query
oxygen run query.sql -v year=2024

# Test SQL without executing
oxygen run query.sql --dry-run

# Run workflow
oxygen run pipeline.workflow.yml

# Run agent with question
oxygen run agent.agent.yml "What are the trends?"

# Validate
oxygen validate
```

## Decision Tree

```
User asks for data analysis
    ↓
Does semantic layer have the data?
    ├─ YES → Use semantic queries (#1)
    └─ NO → Is it deterministic logic?
        ├─ YES → Use SQL/Workflow (#2)
        └─ NO → Need AI reasoning?
            ├─ YES → Use Agent (#3)
            └─ NO → Build semantic layer first
```

## Documentation

For more details on Oxy:

- [Oxy Documentation](https://docs.oxy.tech/)
- [Workflows](https://docs.oxy.tech/learn-about-oxy/automations)
- [SQL Queries](https://docs.oxy.tech/learn-about-oxy/queries)
- [Agents](https://docs.oxy.tech/learn-about-oxy/agents)
- [Semantic Layer](https://docs.oxy.tech/learn-about-oxy/semantic-layer)

## Version

Created: 2025-12-19
Compatible with: Oxy workflows, SQL queries, and agents
