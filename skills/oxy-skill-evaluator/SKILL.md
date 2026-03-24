---
name: oxy-skill-evaluator
description: Evaluate the output of an oxy skill run against a rubric and propose specific improvements to the skill's SKILL.md. Use when the user asks to evaluate a skill, score skill output, or improve a skill based on test results.
---

# Oxy Skill Evaluator

You evaluate the output of one of the 4 oxy skills against its rubric and propose specific,
actionable edits to the skill's `SKILL.md` file.

## When You Activate

Activate when the user says:
- "Evaluate the [skill name] output"
- "Score the semantic layer / workflow / ETL / app builder results"
- "What needs to be fixed in the [skill] skill?"
- Or when `/oxy:eval-and-improve` invokes you for a specific skill

---

## Evaluation Workflow

### Step 1: Identify What to Evaluate

Ask the user (or read from context) which skill just ran and where the output files are.
Expected outputs per skill:
- **oxy-semantic-layer**: `semantics/views/*.view.yml`, `semantics/topics/*.topic.yml`
- **oxy-workflow-builder**: `workflows/*.workflow.yml`, `agents/*.agent.yml`, `example_sql/*.sql`
- **oxy-etl-builder**: `etl/sources/<provider>/`, `etl/runners/<provider>_<entity>.py`
- **oxy-app-builder**: `apps/*.app.yml` or `*.app.yml`

### Step 2: Read the Rubric

Read the rubric for the skill being evaluated:
- Semantic layer: `eval/rubrics/semantic-layer.md`
- Workflow builder: `eval/rubrics/workflow-builder.md`
- ETL builder: `eval/rubrics/etl-builder.md`
- App builder: `eval/rubrics/app-builder.md`

If `eval/rubrics/` is not in the current directory, look for it relative to the skills plugin
directory (where this SKILL.md lives: `../../../eval/rubrics/`).

### Step 3: Inspect Output Files

Read every generated file. For each rubric item, check the file content. Do NOT skip any
must-pass items. Verify:

**For YAML files**: Use `Read` to inspect structure. Check field names exactly — a field
named `query:` is different from `sql_query:`.

**For Python files**: Use `Bash` to run `python -m py_compile <file>` and check exit code.

**For runtime checks**: Use `Bash` to run the verification commands listed in the rubric:
```bash
oxy validate --file=<file>
oxy run <workflow>.workflow.yml --dry-run
oxy build
```

### Step 4: Score Each Item

For each rubric item, record:
- ✅ PASS or ❌ FAIL
- Brief evidence (one line: what you found that confirms pass or fail)

Present results grouped by MUST-PASS first, then SHOULD-PASS:

```
## Skill: oxy-workflow-builder
### MUST-PASS (X/10 passed)
✅ M1 — tasks: array present at top level (confirmed in workflows/daily_report.workflow.yml:4)
❌ M2 — type: sql found instead of type: execute_sql (line 12)
...

### SHOULD-PASS (X/5 passed)
✅ Q1 — semantic layer checked before SQL (saw grep commands in Claude output)
❌ Q4 — {% set %} syntax used instead of variables: block defaults
```

### Step 5: Identify Root Causes in SKILL.md

For each failed item, identify which part of the skill's SKILL.md caused it. Common patterns:
- Missing documentation → Claude didn't know the correct syntax
- Conflicting instructions → SKILL.md says two different things
- No example provided → Claude fell back to general knowledge
- Wrong example in template → Claude followed the wrong template

To find root causes:
1. Read the skill's current `SKILL.md`
2. Search for the section related to the failing item
3. Identify the gap or error

### Step 6: Propose SKILL.md Edits

For each failed must-pass item, propose a specific edit to the skill's `SKILL.md`.
Format proposals as:

```
### Fix for M2 (type: execute_sql)
File: skills/oxy-workflow-builder/SKILL.md
Section: "Workflow File Structure"
Issue: Template shows correct structure but no explicit warning about wrong values.
Proposed addition after line ~185:

> ⚠️ CRITICAL: The task type must be `execute_sql` exactly.
> Do NOT use `type: sql`, `type: execute`, or any other variant.
> These will pass `oxy validate` but fail at runtime.
```

Be specific: include the file, section, and exact text to add or change.

### Step 7: Apply Fixes (With Confirmation)

After presenting all proposed fixes, ask the user:
"Should I apply these changes to the SKILL.md files now?"

If yes:
1. Apply each change using Edit tool
2. Re-run the failing verification commands to confirm fixes work
3. Report final pass/fail counts

---

## Output Format

Always end with a summary table:

```
## Summary: oxy-[skill-name]

| Category | Passed | Failed | Total |
|----------|--------|--------|-------|
| Must-Pass | X | Y | Z |
| Should-Pass | X | Y | Z |

Skill ready for production: YES / NO (must-pass all green)

Top 3 fixes needed:
1. [M#] — one line description
2. [M#] — one line description
3. [Q#] — one line description
```

---

## Retrieval Tool Reference

The correct syntax for the `retrieval` tool in agent files (commonly missing):

```yaml
tools:
  - type: execute_sql
    database: <db_name>
  - type: retrieval
    src:
      - example_sql/*.sql
      - workflows/*.workflow.yml
    key_var: OPENAI_API_KEY   # embedding model API key env var
```

Required fields: `type`, `src`
Optional: `name` (defaults to "retrieval"), `key_var`, `embed_model`, `top_k`, `db_path`

---

## Notes

- `--dry-run` only works for SQL files (`oxy run query.sql --dry-run`). For workflow files,
  `--dry-run` is silently ignored. The only true verification for workflows is running them.
  Wrong field names (like `type: sql` instead of `type: execute_sql`) only surface at runtime.
- If `oxy build` or `oxy run` commands fail due to missing `OXY_DATABASE_URL`, note this
  as an environment issue, not a skill failure. Use oxy ≥ 0.5.27 or set the env var.
- Skill activation reliability (whether skill name appeared in Claude output) is informational.
  Always verify in a fresh session if uncertain whether the skill actually ran.
