# Rubric: oxy-workflow-builder

Score each item ✅ pass or ❌ fail after running the skill.
Items are split into **must-pass** (skill fails eval if any of these fail) and
**should-pass** (quality improvements to track over time).

---

## MUST-PASS — Runtime Correctness

These items mean `oxy run` will fail or produce wrong results if they don't pass.

- [ ] **M1** Workflow file uses `tasks:` as a top-level array. No `database:` or `query:` at the workflow root level.
- [ ] **M2** Each task uses `type: execute_sql` — NOT `type: sql` or any other variant.
- [ ] **M3** Each task uses `sql_query:` — NOT `query:` or `sql:`.
- [ ] **M4** Each task has `database:` inside the task block (not at workflow root).
- [ ] **M5** If parameters are defined: they use `variables:` — NOT `parameters:`.
- [ ] **M6** `oxy validate --file=<workflow>.workflow.yml` passes AND `oxy run <workflow>.workflow.yml` executes without a field/type error. Note: `--dry-run` is not implemented for workflow files (it is silently ignored). Actual execution is required to confirm field names are correct at runtime.
- [ ] **M7** Agent file has `system_instructions`, `model`, and `tools` fields.
- [ ] **M8** Agent has a `database` tool with a valid `database:` field matching a database name in `config.yml`.
- [ ] **M9** Agent has a `retrieval` tool with `type: retrieval` and a `src:` list of glob patterns (e.g. `example_sql/*.sql`).
- [ ] **M10** `oxy validate --file=<agent>.agent.yml` passes.

---

## SHOULD-PASS — Quality & Best Practice

- [ ] **Q1** Skill activation message appeared in Claude output on the first trigger prompt. If not shown, note whether output quality still matched skill behavior and retest in a fresh session.
- [ ] **Q2** Skill checked the semantic layer before generating SQL (respects the hierarchy).
- [ ] **Q3** Skill ran `oxy validate` on workflow and agent files after creation.
- [ ] **Q4** SQL column/table names match what's in `.databases/` (no hallucinated names).
- [ ] **Q5** Jinja variables use `{{ variable_name }}` syntax; defaults defined in `variables:` block or inline `{{ var | default('value') }}` — not `{% set var = var | default(...) %}` blocks.
- [ ] **Q6** `system_instructions` is domain-specific (references actual business context, not generic filler).

---

## Notes

**M6 requires actual execution.** `--dry-run` is only implemented for SQL files, not workflow
files. For workflows, run `oxy run <workflow>.workflow.yml` to confirm field names are correct
at runtime. Wrong names (e.g. `type: sql`) only surface as errors when the workflow actually runs.

**Retrieval tool expected syntax** (verify against the oxy agent JSON schema if syntax is unclear):
```yaml
tools:
  - type: execute_sql
    database: <db_name>
  - name: retrieval
    type: retrieval
    src:
      - example_sql/*.sql
      - workflows/*.workflow.yml
```

**Commands to verify manually:**
```bash
# Workflow (note: --dry-run is silently ignored for workflow files)
oxy validate --file=workflows/<name>.workflow.yml
oxy run workflows/<name>.workflow.yml

# Agent
oxy validate --file=agents/<name>.agent.yml

# Check for retrieval tool
grep -A5 "retrieval" agents/*.agent.yml

# Check workflow fields
grep "type:" workflows/*.workflow.yml      # Should show execute_sql
grep "sql_query:" workflows/*.workflow.yml # Should exist
grep "variables:" workflows/*.workflow.yml # Should exist if params used
```
