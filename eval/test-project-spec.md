# Eval Prompt Guide

This file defines the standard prompts used by `/oxy:eval-and-improve` to trigger and score
each skill. Its sole purpose is **evaluating and improving the skill files** — not building
a production oxy instance.

For the eventual 1-shot instance builder (all 4 skills chained on a new empty repo), see
the `oxy-instance-builder` skill once it is created.

---

## What This Eval Does

- Copies an existing client repo to a temp directory (isolated, nothing in production is touched)
- Runs each skill against the real database from that client project
- Scores the output against structural rubrics (`eval/rubrics/`)
- Proposes specific improvements to each `SKILL.md`

The eval reuses a real database connection because `oxy run` must actually execute —
`oxy validate` alone is insufficient (it passes even with wrong field names at runtime).

---

## Setup: Isolated Eval Environment

**Always run eval in a fresh copy of the client project, never in the live repo.**
The skills will create files; you don't want those in production.

```bash
# 1. Clone or copy the client project to a temp directory
git clone /path/to/pokehouse-oxy /tmp/eval-run
# or: cp -r /path/to/pokehouse-oxy /tmp/eval-run

cd /tmp/eval-run

# 2. Copy credentials if .env was gitignored
cp /path/to/pokehouse-oxy/.env .env

# 3. Sync the database schema (READ ONLY — only writes local .databases/ directory)
oxy sync

# 4. Ensure oxy can run workflows/agents:
#    Option A — oxy >= 0.5.27 (no extra env var needed)
#    Option B — set postgres URL:
export OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy
oxy start --enterprise  # starts local postgres

# 5. Launch Claude Code with the skills plugin
claude --plugin-dir /path/to/skills

# Then run: /oxy:eval-and-improve
```

### Safety Notes
- `oxy sync` is **read-only against your database** — only writes local `.databases/` metadata
- `oxy run` during eval only executes SELECT queries and `--dry-run` checks
- All skill-generated files go into the temp directory
- Clean up after: `rm -rf /tmp/eval-run`

---

## Eval Prompts (Per Skill)

These prompts are intentionally generic — they work for any client's schema by reading
whatever is in `.databases/` rather than referencing specific table names.

### Skill 1: oxy-semantic-layer

```
Look at the tables in .databases/ and create a comprehensive semantic layer for this project.
For each major table, create a view file in semantics/views/ with appropriate entities,
dimensions, and measures for business analytics. Group related views into one or more topic
files in semantics/topics/. Make sure entity keys reference dimension names, not raw column
names. Add synonyms to dimensions where helpful for natural language queries.
```

### Skill 2: oxy-workflow-builder

Run after Skill 1 output exists.

```
Build a data workflow and analyst agent for this project.

First, check semantics/ to see what views and topics exist.

Then create:
1. A multi-step SQL workflow calculating key operational metrics for a configurable date range.
   Use at least 2 tasks. Define parameters using variables:.

2. A data analyst agent with: a clear system_instructions prompt, a database tool, and a
   retrieval tool that indexes SQL files in example_sql/ and workflows/.
```

### Skill 3: oxy-etl-builder

Adapt the provider/endpoint for the specific client being tested:

```
Create an ETL pipeline to extract [entity] data from the [Provider] API.
Endpoint: [endpoint path]. Auth: [env var name]. Set up incremental loading by [date field].
```

| Client | Provider | Endpoint | Auth env var |
|--------|----------|----------|--------------|
| pokehouse-oxy | Toast POS | `/restaurants/v1/restaurantInfo` | `TOAST_API_KEY` |
| hubspot-oxy | HubSpot | `/crm/v3/objects/contacts` | `HUBSPOT_ACCESS_TOKEN` |

### Skill 4: oxy-app-builder

Run after Skills 1 and 2 output exists.

```
Build an executive dashboard app. Look at what data is available in semantics/ and workflows/,
then create an app called 'executive_overview' showing:
1. A summary table of the top KPIs for this business (based on available data)
2. A line chart showing a key metric trend over the last 90 days
3. A bar or pie chart showing distribution by a key categorical dimension
```

---

## Recording Results

After each skill run, score output against `eval/rubrics/<skill-name>.md` and record in
`eval/results/<client>-<date>.md`:

```markdown
# Eval Results: <client> — <YYYY-MM-DD>

## Skill 1: oxy-semantic-layer — X/Y passed
Failures:
- [ ] ...
Proposed SKILL.md changes:
- ...

## Skill 2: oxy-workflow-builder — X/Y passed
...

## Skill 3: oxy-etl-builder — X/Y passed
...

## Skill 4: oxy-app-builder — X/Y passed
...

## Notes
...
```
