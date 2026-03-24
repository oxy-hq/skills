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

2. **Database schema is synced:**
   ```bash
   ls .databases/
   ```
   If `.databases/` is empty or missing, run `oxy sync` first.

3. **oxy can run workflows** (needed for `--dry-run` checks):
   - Option A: `oxy --version` shows ≥ 0.5.27
   - Option B: `OXY_DATABASE_URL` is set and `oxy start` has been run

4. **Skills plugin directory is known.**
   The rubrics and skill files are at `<plugin-dir>/eval/rubrics/` and
   `<plugin-dir>/skills/`. Ask the user for the plugin dir path if unknown.

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

Use the generic prompt from `eval/test-project-spec.md` for this skill.
(The file is at `<plugin-dir>/eval/test-project-spec.md`)

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
- Did workflow-builder correctly use semantic layer output? YES/NO
- Did app-builder reference workflow outputs correctly? YES/NO

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
