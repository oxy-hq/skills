# Eval Run Summary — pokehouse-oxy — 2026-03-24

**Project**: `/private/tmp/eval-run-20260324/oxy`
**Database**: ClickHouse (`restaurant_analytics` schema)
**Tables available**: sales_daily_metrics, labor_daily_metrics, orders, order_checks,
order_selections, employees, jobs, time_entries, restaurants, income_statement, dining_options

---

## Scores

| Skill | Must-Pass | Should-Pass | Ready? |
|-------|-----------|-------------|--------|
| oxy-semantic-layer | 9/9 | 6/7 | YES |
| oxy-workflow-builder | 6/6 | 5/6 | YES |
| oxy-etl-builder | 10/10 | 7/7 | YES |
| oxy-app-builder | 9/9 | 6/7 | YES |

**All 4 skills passed all must-pass items.**

---

## Cross-Skill Handoffs

- Did workflow-builder correctly use semantic layer output? **N/A** — workflow used direct SQL against ClickHouse tables, not semantic queries. Semantic layer existed but workflow skill chose SQL path (appropriate given the analytical nature of the task).
- Did app-builder reference workflow outputs correctly? **YES** — dot notation (`ops_metrics.sales_metrics`, `ops_metrics.labor_metrics`, `ops_metrics.efficiency_summary`) correctly referenced all 3 inner workflow tasks.
- Did agent use retrieval tool referencing workflow SQL? **YES** — `data_analyst.agent.yml` retrieval tool indexes `example_sql/*.sql` and `workflows/*.workflow.yml`.

---

## SKILL.md Changes Made

### oxy-semantic-layer

1. **Core Workflow step 1**: Changed from "Read `.databases/` directory" to "Read `semantics.yml` (produced by `oxy sync`) to discover tables and columns. If `.databases/` exists, read that instead."
   - Why: `oxy sync` writes to `semantics.yml`, not `.databases/`, in current oxy versions.

2. **Building Process Step 1**: Updated description to say `oxy sync` writes to `semantics.yml`, with note about older `.databases/` format.

3. **Building Process Step 5 (oxy build)**: Added `oxy start` + `OXY_DATABASE_URL` requirement; made it a mandatory final step with explicit instructions for setting the env var.
   - Why: `oxy build` requires a running PostgreSQL instance; without it, the command fails with "OXY_DATABASE_URL environment variable is required."

### oxy-workflow-builder

4. **Step 4 "Validate and Test"**: Made mandatory; added explicit note that `--dry-run` is silently ignored for workflow files; `oxy run` is required for true verification of field name correctness.
   - Why: Wrong field names (e.g. `type: sql` instead of `type: execute_sql`) pass `oxy validate` but fail at `oxy run` time.

---

## Should-Pass Failures (not blocking)

| Skill | Item | Description |
|-------|------|-------------|
| oxy-semantic-layer | Q7 | `oxy build` not run after initial file creation (needed `oxy start` first) — skill adapted but environment setup slowed this |
| oxy-workflow-builder | Q6 | Semantic layer not consulted before writing SQL — valid choice since SQL needed custom efficiency calculations not in semantic layer |
| oxy-app-builder | Q4 | No `semantic_query` task used — caused by test prompt explicitly requesting the workflow and agent |

---

## Notable Issues Encountered

1. **Boolean samples in semantic layer view files**: `oxy build` rejected unquoted YAML booleans (`samples: [true, false]`). Required quoting as strings (`samples: ["true", "false"]`). Fixed via sed across all view files.

2. **`oxy build` requires PostgreSQL**: Must run `oxy start` first to start Docker PostgreSQL, then set `OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy` inline with each command (env vars don't persist between shell invocations in Claude Code).

3. **`oxy sync` writes to `semantics.yml`**: Skill's SKILL.md referenced `.databases/` directory which doesn't exist in current oxy versions. Skill adapted by reading `semantics.yml` directly; SKILL.md updated.

4. **ETL was a new project**: Core framework (`etl/core/`) had to be created from scratch before the Toast source files. Skill handled this correctly per its scenario detection logic.

---

## Generated Files

### Semantic Layer (11 views + 11 topics)
`semantics/views/`: dining_options, employees, income_statement, jobs, labor_daily, order_checks, order_selections, orders, restaurants, sales_daily, time_entries

### Workflows & Agents
- `workflows/operational_metrics.workflow.yml` — 3-task pipeline: sales_metrics → labor_metrics → efficiency_summary
- `data_analyst.agent.yml` — restaurant ops analyst with execute_sql + retrieval tools

### ETL Pipeline
- `etl/sources/toast/client.py` — ToastClient with TOAST_API_KEY, retry/rate-limit logic
- `etl/sources/toast/restaurants_source.py` — DLT source with incremental loading by `_etl_extracted_at`
- `etl/runners/toast_restaurants.py` — Typer CLI runner extending BasePipelineRunner

### App
- `executive_dashboard.app.yml` — Workflow + agent tasks, 7 display items (tables, bar charts, markdown + AI insights)
