# Oxy skills

Skills that teach a coding agent — Claude Code, Cursor, Codex, Copilot and anything else that
reads [Agent Skills](https://agentskills.io) — how to build on [Oxy](https://oxy.tech).

## Install

Any agent:

```bash
npx skills add oxy-hq/skills
```

Claude Code, as a plugin:

```text
/plugin marketplace add oxy-hq/skills
/plugin install oxy@oxy-hq
```

With the Oxy CLI (`oxyc` ships the same skills):

```bash
npm install -g @oxy-hq/cli && oxyc skills install
```

To update: `npx skills update`, `claude plugin update oxy@oxy-hq`, or reinstall
`@oxy-hq/cli` and run `oxyc skills install` again.

## Skills

| Skill | Use it when |
| --- | --- |
| `oxy-agents` | Use when creating, editing, reviewing or debugging an Oxy agent, a `.agentic.yml` file that answers questions from the semantic model by clarifying, specifying, solving (SQL), executing and interpreting. |
| `oxy-airway-pipelines` | Use when writing, reviewing, or debugging an Oxy Airway ELT pipeline (`.airway.yml`) — sources, the `kind` values Oxy actually wires, credentials, reset, rewind and retry — or when one misbehaves: "unsupported source… |
| `oxy-automations` | Use when writing, debugging, or reviewing an Oxy automation (a `.automation.yml` / legacy `.procedure.yml` workflow — tasks, loops, variables, schedules) in a customer workspace, or when an automation *run*… |
| `oxy-cli` | Use when you need data out of an Oxy deployment — querying a customer's warehouse or semantic layer, reading threads/runs/apps/orgs, checking why an endpoint 4xxs, or reproducing a customer-reported bug against real… |
| `oxy-custom-apps` | Use when building, debugging, reviewing, shipping, or verifying an Oxy custom-app bundle (a code-first React/Vite app served by Oxy at /customer-apps/&lt;org&gt;/&lt;slug&gt;/), including writing Oxy Functions, driving them from… |
| `oxy-data-apps` | Use when creating, editing, reviewing, or debugging an Oxy Data App — a declarative `.app.yml` file of tasks (`execute_sql`, `semantic_query`) and displays (tables, line / bar / pie charts, markdown, side-by-side… |
| `oxy-data-architecture` | Use when deciding where an aggregate gets materialised — writing an `execute_sql` rollup, chaining one after an `airway` ingest step, choosing rollup vs semantic `pre_aggregations`, or whether raw rows must be… |
| `oxy-evals` | Use when writing, running, or acting on evals for an Oxy agent — `.test.yml` files that run an `.agentic.yml` agent and score its answers with an LLM judge — and when the agent's answers are wrong. |
| `oxy-semantic-modeling` | Use when writing, reviewing, or debugging an Oxy semantic model — `.view.yml` views, `.topic.yml` topics, measures, dimensions, entities, pre-aggregations (rollups), and the `meta:` freshness block — in a customer… |

## Contributing

This repository is generated at `a0f02a548654` from `sdk/cli/skills/` in Oxy's product repository, so a
skill changes in the same pull request as the behaviour it describes. Edits made here are
overwritten by the next sync — open an issue instead.
