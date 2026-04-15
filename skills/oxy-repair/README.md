# Oxy Repair

Diagnose and fix failing or flaky Oxy test cases by repairing the semantic layer and agent system instructions — without weakening the tests.

## What It Does

The **oxy-repair** skill takes a failing test case, finds the root cause, and makes targeted fixes so the agent produces the correct answer reliably. It:

1. Runs `oxygen test <file> --case <name> --output-json` to reproduce the failure
2. Inspects the results JSON — `actual_output`, `expected`, `references` (tool calls), and judge reasoning
3. Classifies the root cause (missing dimension, insufficient measure, vague instructions, judge noise, etc.)
4. Makes the smallest semantic layer or agent instruction fix that addresses the root cause
5. Rebuilds with `oxygen build` and reruns the test across multiple rounds to confirm stability
6. Reports what changed, why, and the validation results

**The expected answer is the source of truth.** This skill repairs the system to match the expected answer — it never rewrites the expected answer to match current behavior.

---

## Required Inputs

- A failing or flaky test case (in an existing `.test.yml` file)
- The repo root of the target Oxy project

Optionally:
- Observability traces from the Oxy platform (query traces, tool call logs, LLM traces)
- Specific error messages or symptoms the user has observed

---

## Example Invocations

```
"The total-revenue test case is failing. Can you figure out why and fix it?"
```

```
"My tests in tests/analyst.sales_performance.test.yml are flaky — the revenue
questions pass sometimes and fail sometimes. Help me stabilize them."
```

```
"Debug this failing eval. The agent says it can't find customer data,
but I know the view exists."
```

```
"Use the test output JSON to diagnose why the unemployment comparison
question keeps getting different answers, then fix it."
```

```
"Improve the semantic layer so my agent tests pass more consistently."
```

---

## Output

### 1. Targeted repairs to source files

Edits to semantic layer files (`*.view.yml`, `*.topic.yml`), agent YAML (`*.agent.yml`), or related configuration — whatever is needed to fix the root cause.

### 2. Diagnostic summary (in conversation)

```
## Repair Summary

Target test: tests/analyst.regional_analysis.test.yml
Target case: unemployment-comparison
Root cause: semantic layer missing comparison dimension
Files changed:
- semantics/views/regional.view.yml
- analyst.agent.yml

What changed:
- added dimension `unemployment_vs_avg` to regional view — lets semantic query
  return pre-grouped above/below average rows instead of raw data
- tightened system instruction to prefer semantic_query over execute_sql

Validation:
- round 1: 2/3 pass
- round 2: 3/3 pass
- round 3: 3/3 pass

Notes:
- one prior FAIL appears to have been a judge-model false negative
```

---

## Root Cause Categories

| Category | Symptoms | Typical Fix |
|----------|----------|-------------|
| **Missing dimension/grouping** | Agent fetches raw data, post-processes it, results vary | Add computed dimension to view |
| **Missing measure** | Agent manually computes ratios/percentages | Add derived measure |
| **Vague agent instructions** | Agent picks wrong tool or takes brittle path | Tighten system instructions (keep general, not hard-coded) |
| **Judge inconsistency** | Correct answer marked FAIL; `cot` says PASS | Don't chase — surface as judge issue, recommend better model |
| **Underspecified prompt** | Agent takes different valid interpretations | Surface to user; don't silently weaken expected |
| **Data unavailable** | Needed information doesn't exist in the system | State clearly; don't fake support |

---

## What Gets Modified

| File type | Modified? | Examples |
|-----------|-----------|----------|
| View files (`*.view.yml`) | Yes | Add dimensions, measures, fix joins, improve descriptions |
| Topic files (`*.topic.yml`) | Yes | Add missing views, fix descriptions |
| Agent files (`*.agent.yml`) | Yes | Fix system instructions, tool-choice guidance |
| Test files (`*.test.yml`) | No* | Only mechanical additions like a missing `name:` field |
| Workflow files | Rarely | Only if directly causing the failure |

*The expected answer is sacred — this skill does not weaken tests to make them pass.

---

## Relationship to oxy-test-drafter

| | oxy-test-drafter | oxy-repair |
|---|---|---|
| **Purpose** | Create and fill test cases | Fix failing test cases |
| **Modifies `.test.yml`** | Yes (primary output) | No (except mechanical fixes) |
| **Modifies semantic layer** | Never | Yes (primary action surface) |
| **Modifies agent YAML** | Never | Yes (when needed) |
| **Source of truth** | Observed agent output | Expected answer in test |

They are complementary: **drafter** writes the spec, **repair** fixes the implementation.

---

## Repair Philosophy

1. Diagnose before fixing — read the results JSON first
2. Prefer semantic layer fixes when the problem is representational
3. Never hard-code answers into instructions
4. Expose computed groupings as dimensions, not agent post-processing
5. Validate over multiple rounds — one pass is not enough
6. Watch for judge false negatives — not every FAIL is an agent bug
7. Make the smallest robust fix that generalizes

---

## What This Skill Does NOT Do

- Rewrite `expected` strings to make failing tests pass
- Remove or skip difficult test cases
- Hard-code one-off answers into system instructions
- Make sweeping refactors or "while I'm here" improvements
- Treat judge false negatives as semantic-layer bugs
- Stop after a single lucky pass
- Fix issues unrelated to Oxy answer correctness
