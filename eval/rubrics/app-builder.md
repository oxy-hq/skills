# Rubric: oxy-app-builder

Score each item ✅ pass or ❌ fail after running the skill.
Items are split into **must-pass** (skill fails eval if any of these fail) and
**should-pass** (quality improvements to track over time).

---

## MUST-PASS — Runtime Correctness

These items mean `oxy validate` will fail or the app will error when run.

- [ ] **M1** App file has `name`, `tasks:`, and `display:` at the top level.
- [ ] **M2** `tasks:` is a non-empty array; each task has a unique `name` (snake_case).
- [ ] **M3** `display:` is a non-empty array.
- [ ] **M4** Every display item's `data:` value matches a task `name` exactly. No references to non-existent tasks.
- [ ] **M5** `execute_sql` tasks use `sql_query:` (NOT `query:`) and have `database:` inside the task block (NOT at app root).
- [ ] **M6** Display `type` values are valid: `table`, `markdown`, `line_chart`, `bar_chart`, or `pie_chart`. NOT `bar`, `line`, `chart`, etc.
- [ ] **M7** For `line_chart` and `bar_chart`: `x:` and `y:` values match actual column names returned by the referenced task's SQL (not column aliases that don't exist).
- [ ] **M8** For `pie_chart`: `name:` and `value:` values match actual column names.
- [ ] **M9** `oxy validate --file=<app>.app.yml` passes.

---

## SHOULD-PASS — Quality & Best Practice

- [ ] **Q1** Skill activation message appeared in Claude output on the first trigger prompt. If not shown, note whether output quality still matched skill behavior and retest in a fresh session.
- [ ] **Q2** Skill presented a written plan before writing any YAML (required by skill workflow).
- [ ] **Q3** Skill consulted available semantic layer and workflows before choosing task types.
- [ ] **Q4** At least one task uses `semantic_query` type if a relevant semantic layer topic exists.
- [ ] **Q5** SQL references real table/column names from `.databases/` (no hallucinated names).
- [ ] **Q6** `display:` items have meaningful `title:` fields.
- [ ] **Q7** Skill ran `oxy validate` after creating the file.

---

## Notes

**M6 failure** (`type: bar` vs `type: bar_chart`) was observed in first_test.md expected
output. This is an easy one to catch but may be inconsistent.

**M7 failure** is common: SQL returns `SUM(amount) as revenue` but chart specifies `y: total_revenue`.
The evaluator must inspect the SQL output columns, not just the YAML.

**Commands to verify manually:**
```bash
oxy validate --file=apps/<name>.app.yml
# or if at project root:
oxy validate --file=<name>.app.yml

# Inspect for display type values
grep "type:" apps/<name>.app.yml

# Inspect data: references vs task names
grep "name:" apps/<name>.app.yml | head -10
grep "data:" apps/<name>.app.yml
```
