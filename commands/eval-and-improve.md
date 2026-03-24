---
name: oxy:eval-and-improve
description: Evaluate all 4 oxy skills against rubrics using the current project's real database, then propose and apply improvements to each SKILL.md file.
activeForm: Evaluating and improving oxy skills
argument-hint: "[skill-name]  (optional: run eval for one skill only, e.g. 'semantic-layer')"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Eval and Improve Oxy Skills

Evaluate all 4 oxy skills (or one specific skill) by running them against the current
project's real database, scoring the output against rubrics, and proposing targeted
improvements to each `SKILL.md` file.

## Prerequisites Check

Before starting, verify:

1. **You are in a copy of a real oxy project, not the live repo.**
   Run `pwd` and confirm this is a temp/eval directory, not production.

2. **Skill output directories are clean.**
   The eval tests what each skill generates from scratch. Before starting, remove any
   pre-existing skill outputs so skills aren't judged on files they didn't create:
   ```bash
   rm -f semantics/views/*.view.yml semantics/topics/*.topic.yml
   rm -f workflows/*.workflow.yml *.agent.yml *.app.yml
   ```
   Keep: `config.yml`, `semantics.yml`, `example_sql/`, `globals/`, `.env`

3. **Database schema is synced:**
   Run `oxy sync` if `semantics.yml` is missing or stale.

4. **oxy build requires a running PostgreSQL instance.**
   Run `oxy start` in a separate terminal before starting this eval session.
   `oxy start` launches a Docker PostgreSQL container and the oxy web server.
   It exposes PostgreSQL on port 15432 with default credentials.
   Add this to the project's `.env` so oxy can connect:
   ```
   OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy
   ```
   Note: `oxy --version` ≥ 0.5.27 is only needed for `oxy run --dry-run` on SQL files,
   not for `oxy build`.

4. **Export OXY_DATABASE_URL at the start of this session.**
   Each Bash tool call runs in a fresh shell, so `export` does not persist between calls.
   Read the value from `.env` once and prepend it to every `oxy` command:
   ```bash
   export OXY_DATABASE_URL=$(grep OXY_DATABASE_URL .env | cut -d= -f2-)
   ```
   Then use this pattern for all oxy commands throughout the eval:
   ```bash
   OXY_DATABASE_URL=$(grep OXY_DATABASE_URL .env | cut -d= -f2-) oxy build
   OXY_DATABASE_URL=$(grep OXY_DATABASE_URL .env | cut -d= -f2-) oxy run ...
   ```

5. **Skills plugin directory is known.**
   The rubrics and skill files are at `<plugin-dir>/eval/rubrics/` and
   `<plugin-dir>/skills/`. Resolve the plugin dir in this order:
   1. Read `CLAUDE.md` in the current directory — look for a line starting with `PLUGIN_DIR:`
      (this is a user-set override; skip if absent)
   2. Run this targeted search to find the oxy-skills plugin by its marker:
      ```bash
      grep -rl '"name": "oxy-skills"' ~/.claude/plugins ~/.claude/projects ~/Documents 2>/dev/null \
        | grep "\.claude-plugin/plugin\.json" | head -1
      ```
      The plugin dir is two levels up from the matched file (i.e. strip `/.claude-plugin/plugin.json`).
   3. If still not found, ask the user for the path before proceeding.

---

## Execution Order

If no skill name argument is given, run all 4 skills in this order (each builds on the last):

```
1. oxy-semantic-layer  →  score  →  propose fixes  →  apply fixes
2. oxy-workflow-builder  →  score  →  propose fixes  →  apply fixes
3. oxy-etl-builder  →  score  →  propose fixes  →  apply fixes
4. oxy-app-builder  →  score  →  propose fixes  →  apply fixes
5. End-to-end summary
```

If a skill name argument is given (e.g. `semantic-layer`), run only that skill's cycle.

**Important**: Each skill should be run in a fresh context to test cold activation reliability.
The eval command itself stays running, but it spawns each skill invocation as a separate
prompt sequence. The easiest way to simulate fresh activation is to run each skill prompt
explicitly and observe whether the skill activation indicator appears.

---

## Per-Skill Cycle

For each skill, do these steps in order:

### Step A: Run the Skill

Use the exact prompt below for each skill. Do NOT paraphrase or add specifics —
these are intentionally generic so the skill must figure out what to build from context.

**oxy-semantic-layer prompt:**
```
Look at the tables in .databases/ and create a comprehensive semantic layer for this project.
For each major table, create a view file in semantics/views/ with appropriate entities,
dimensions, and measures for business analytics. Group related views into one or more topic
files in semantics/topics/. Make sure entity keys reference dimension names, not raw column
names. Add synonyms to dimensions where helpful for natural language queries.
```

**oxy-workflow-builder prompt** (run after semantic layer exists):
```
Build a data workflow and analyst agent for this project.

First, check semantics/ to see what views and topics exist.

Then create:
1. A multi-step SQL workflow calculating key operational metrics for a configurable date range.
   Use at least 2 tasks. Define parameters using variables:.

2. A data analyst agent with: a clear system_instructions prompt, a database tool, and a
   retrieval tool that indexes SQL files in example_sql/ and workflows/.
```

**oxy-etl-builder prompt** (adapt provider/endpoint for the client being tested):
```
Create an ETL pipeline to extract [entity] data from the [Provider] API.
Endpoint: [endpoint path]. Auth: [env var name]. Set up incremental loading by [date field].
```
See `<plugin-dir>/eval/test-project-spec.md` for client-specific values to fill in.

**oxy-app-builder prompt** (run after semantic layer and workflow exist):
```
Build an executive dashboard app. Look at what data is available in semantics/ and workflows/,
then create an app called 'executive_overview' showing:
1. A summary table of the top KPIs for this business (based on available data)
2. A line chart showing a key metric trend over the last 90 days
3. A bar or pie chart showing distribution by a key categorical dimension
```

Trigger the skill by phrasing the prompt to match its activation description:
- Semantic layer: "Look at the tables in .databases/ and create a semantic layer..."
- Workflow builder: "Build a data workflow and analyst agent..."
- ETL builder: "Create an ETL pipeline to extract data from..."
- App builder: "Build an executive dashboard app..."

Wait for the skill to complete all file generation and validation steps.

### Step B: Invoke oxy-skill-evaluator

Say: "Evaluate the [skill name] output against its rubric."

The `oxy-skill-evaluator` skill will activate, read the rubric, inspect the files, run
verification commands, and score each rubric item.

### Step C: Review and Apply Fixes

The evaluator will propose specific edits to the skill's `SKILL.md`. Review them, then:
- If the fix is clearly correct: apply it immediately with Edit
- If the fix needs verification (e.g. confirming correct oxy syntax): fetch the relevant
  JSON schema first, then apply
  ```bash
  curl -s https://raw.githubusercontent.com/oxy-hq/oxy/refs/heads/main/json-schemas/agent.json
  ```
- If uncertain: note the item and continue; address it in the end-to-end review

### Step D: Re-run Failing Checks

After applying fixes, re-run the specific `oxy validate` or `oxy run --dry-run` commands
that previously failed to confirm the fix works.

---

## End-to-End Summary

After all 4 skills have been evaluated, produce a final summary:

```
# Eval Run Summary — <project> — <date>

| Skill | Must-Pass | Should-Pass | Ready? |
|-------|-----------|-------------|--------|
| oxy-semantic-layer | X/Y | X/Y | YES/NO |
| oxy-workflow-builder | X/Y | X/Y | YES/NO |
| oxy-etl-builder | X/Y | X/Y | YES/NO |
| oxy-app-builder | X/Y | X/Y | YES/NO |

## Cross-Skill Handoffs
- Did workflow-builder check semantics/ before writing SQL (to inform column/table choices)? YES/NO
  (Note: workflows always use execute_sql tasks with raw SQL — semantic_query is for apps/agents, not workflows)
- Did app-builder read workflow output task names before writing data: references? YES/NO

## SKILL.md Changes Made
1. <skill>: <description of change>
2. ...

## Remaining Issues
Items that could not be fixed automatically (require oxy version verification, etc.):
1. ...
```

Save this summary to `eval/results/<project-name>-<YYYY-MM-DD>.md` in the plugin directory.

---

## Notes

- **Do not run this in the live production repo.** All file creation happens in the current
  working directory. Confirm you are in a temp/eval copy before proceeding.
- **`oxy validate` ≠ runtime correctness.** `--dry-run` only works for SQL files, not
  workflow files. For workflows, `oxy validate` checks YAML syntax but not field semantics.
  The only true verification is actually running the workflow. Wrong field names (e.g.
  `type: sql` instead of `type: execute_sql`) will fail at `oxy run` time.
- **Skill activation**: If a skill does not show its activation indicator on the first
  prompt, note it in the results. The eval can still proceed, but this should be investigated
  in a separate fresh session.
- **ETL dry-run**: For the ETL skill, runtime testing requires actual API credentials.
  Use `python -m py_compile` for syntax checking and `uv run python -m etl.runners.<runner> test`
  if credentials are available.
