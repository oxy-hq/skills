# Oxy Project Instructions for Claude Code

## Skill Usage

When working on this Oxy project, use the appropriate skill for each task:

- **Semantic Layer**: Whenever user requests creating, updating, or validating
semantic layers, views, topics, or understanding database schemas, use the
**oxy-semantic-layer** skill.

- **Workflows & Queries**: Whenever user requests creating or modify workflow
files, use the **oxy-workflow-builder** skill.

- **ETL Pipelines**: Whenever user requests building data extraction, adding
API connectors, ingesting spreadsheets/documents, or working with ETL, use the
**oxy-etl-builder** skill.

- **Data Apps**: Whenever user requests creating dashboards, data apps,
reports, or interactive analytics interfaces, use the **oxy-app-builder**
skill.

- **Eval / Test Drafting**: ALWAYS use the **oxy-test-drafter** skill
for ANY test or eval request involving an agent, workflow, or agentic
workflow — including "add a test", "create a test case", "test this
agent", "write tests", "run tests", "add evals", "evaluate my agent",
"create an evaluation", "fill in expected answers", or any mention of
`.test.yml` files. Do NOT attempt to run the agent directly or write
test cases without activating this skill first.
