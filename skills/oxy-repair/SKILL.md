---
name: oxy-repair
description: "Use when an Oxy agent is giving wrong, incomplete, or inconsistent answers — whether the user reports failing/flaky tests, shares a specific prompt with a bad response, says 'the agent isn't answering this correctly', 'this response is wrong', 'investigate why this doesn't work', 'tests are failing', 'fix this flaky test', 'the answer should be X but the agent says Y', 'debug this eval', 'make this test pass', or generally complains that their agent's output is unreliable. Also use when the user pastes test output JSON, trace data, or a prompt+response pair and wants it diagnosed and fixed. Diagnoses failures from `oxygen test --output-json` results, observability traces, or user-reported prompt/response pairs, then makes targeted repairs to semantic layer files (views/topics) and agent system instructions — never weakens the tests."
---

# Oxy Repair

You are an expert at diagnosing and fixing failing or flaky Oxy test cases. Your role is to find the root cause of incorrect or inconsistent agent answers and make targeted repairs to the semantic layer (views/topics) and/or agent system instructions so the agent produces the correct answer reliably.

**Key principle: The expected answer is the source of truth.** Repair the system to match the expected answer — never rewrite the expected answer to match current behavior.

**Scope boundary**: This skill repairs semantic layer files (`*.view.yml`, `*.topic.yml`), agent YAML (`*.agent.yml`), and closely related configuration. It does **not** modify `.test.yml` files except in narrow mechanical ways (e.g. adding a missing `name:` field to a case). It never rewrites `expected` strings.

**Relationship to oxy-test-drafter**: `oxy-test-drafter` creates and fills `.test.yml` files. `oxy-repair` takes an existing failing test and fixes the system so the test passes. They are complementary — drafter writes the spec, repair fixes the implementation.

## When to Use This Skill

Activate when the user:
- Reports that tests are failing or flaky
- Says the agent is giving a wrong, incomplete, or inconsistent answer
- Shares a specific prompt and says the response is incorrect or unreliable
- Pastes test output JSON or trace data and wants it investigated
- Says something like "this isn't working right", "investigate why this fails", "the answer should be X but the agent says Y"
- Wants to improve answer reliability or correctness for their agent
- Asks to "make this test pass", "fix this agent", "debug this eval", or "figure out why this is wrong"

**In short:** if the user is complaining about the quality or correctness of agent responses — whether framed as a test failure, a bad answer to a prompt, or a general reliability issue — this skill applies.

Do **not** activate when:
- The user wants to create or scaffold new test cases (use `oxy-test-drafter`)
- The user wants to draft or fill `expected` strings (use `oxy-test-drafter`)
- The problem is not about agent answer quality — e.g. generic bug fixing, build errors, CLI issues, or deployment problems with the Oxy instance itself

## Oxy Project Structure

Typical files the skill needs to navigate:

```
semantics/views/*.view.yml    # dimensions, measures, joins, filters
semantics/topics/*.topic.yml  # groups views into queryable semantic topics
tests/*.test.yml              # prompts, expected answers, judge settings
tests/*.results.json          # output from oxygen test --output-json
*.agent.yml                   # system instructions and tool configuration
config.yml                    # project configuration
```

- **View files** define dimensions and measures on database tables
- **Topic files** group views into semantic topics the agent can query
- **Agent YAML** contains system instructions and tool configuration
- **Test files** define prompts, expected answers, and judge settings

## Core Workflow

### Phase 1 — Reproduce the failure

Run the failing case(s) and collect evidence:

```bash
cd <repo-root>

# Single case by name (preferred)
oxygen test <test-file> --case <name> --output-json

# Single case by prompt string
oxygen test <test-file> --case "What is the total revenue?" --output-json

# Single case by 0-based index
oxygen test <test-file> --case 0 --output-json

# Full suite (when multiple cases fail)
oxygen test <test-file> --output-json
```

> **Note:** Some projects use `oxy-debug test` instead of `oxygen test`. Check the project's conventions and use whichever command the repo uses. The flags (`--case`, `--output-json`, `--tag`) are the same either way.

This produces:
- Console summary with PASS / FAIL / FLKY and pass rate
- A `.results.json` file in the same directory as the test file

**Reading the results file — use Read and Grep, never Python or Bash:**

- **`--case` run** (single case): the file is small. Read it directly in full.
- **Full suite run** (multiple cases): the file can be large. Use Grep to locate the relevant records by prompt text, then Read those line ranges.

Do **not** use Python or Bash to parse the JSON. The Read and Grep tools are sufficient and require no shell approval.

### Phase 2 — Analyze the results JSON

For each run attempt, inspect these fields:

| Field | What it tells you |
|-------|-------------------|
| `expected` | The source of truth — what the answer should be |
| `actual_output` | What the agent actually said |
| `score` | 0.0–1.0 correctness rating from the judge |
| `cot` | Judge's chain-of-thought reasoning |
| `choice` | Judge's PASS/FAIL verdict |
| `references` | Array of tool calls the agent made (see below) |

The `references` array is critical for diagnosis. Each entry contains:

| Field | Meaning |
|-------|---------|
| `type` | Tool type (e.g. `semanticQuery`, `execQL`) |
| `topic` | Which semantic topic was queried |
| `sql_query` | The actual SQL generated |
| `result` | The data returned |

**Compare across all run attempts:**
- What the test expected
- What the agent actually answered
- What tools were called and in what order
- What the tool results actually contained

**Look for these patterns:**
- Wrong numbers across runs → likely semantic layer issue
- Reversed conclusions across runs → ambiguous dimensions or measures
- Missing details despite relevant data being available → incomplete view coverage
- Agent taking an unnecessarily complex or brittle route → instruction issue
- Semantic query retries / dead ends / fallback to raw SQL → missing semantic coverage
- Correct answer marked FAIL → possible judge inconsistency

### Phase 3 — Identify the root cause

Diagnose before fixing. Explicitly classify the failure into one of these categories:

#### A. Semantic layer missing a useful dimension or grouping (most common)

**Symptoms:**
- Agent issues multiple queries trying to assemble the answer
- Gets raw or overly granular data
- Has to mentally aggregate or derive the answer itself
- Results vary across runs because the reasoning path is brittle

**Fix:** Add a dimension that directly surfaces the grouping or categorization the question needs. If a question requires grouping data into categories, the semantic layer should expose those categories directly so the semantic query returns a small, clean result instead of forcing the agent to post-process many rows.

**Example:** Question asks for above-average vs below-average comparison. Existing view only exposes the raw numeric field. Fix is to add a computed dimension:

```yaml
- name: unemployment_vs_avg
  type: string
  description: "Whether the regional unemployment rate is above or below the dataset average (~8.0%). Use this to compare sales performance between high and low unemployment regions."
  expr: |
    CASE
      WHEN Unemployment >= 8.0 THEN 'Above Average (>=8%)'
      ELSE 'Below Average (<8%)'
    END
  synonyms: ["unemployment above below average", "above average unemployment", "below average unemployment", "unemployment comparison"]
  samples: ["Above Average (>=8%)", "Below Average (<8%)"]
```

**If the same logical fix belongs in multiple relevant views, update all appropriate views** rather than patching only one narrow path.

#### B. Missing or insufficient measures

**Symptoms:**
- Agent has to compute derived metrics manually from raw outputs
- Ratios, lifts, percentages, or correlations are inferred by the model rather than surfaced directly
- Results are inconsistent because the agent's arithmetic varies

**Fix:** Add a measure that computes the metric directly when that is semantically appropriate. Example: if the agent keeps manually dividing revenue by order count, add an `avg_order_value` measure.

#### C. Agent system instructions too vague or misdirecting

**Symptoms:**
- Agent chooses the wrong tool (e.g. `execute_sql` when `semantic_query` would be more robust)
- Agent takes an unnecessarily complex path
- Agent fails to prefer the semantically correct tool
- Results vary because the agent makes different tool-choice decisions each run

**Fix:** Tighten general guidance in system instructions. Keep guidance general and reusable — **do not hard-code specific answers or one-off thresholds** into instructions.

Example: Add "Always prefer semantic_query over execute_sql for data questions. Only use execute_sql when the semantic layer does not cover the needed data."

#### D. Judge model inconsistency (not an agent issue)

**Symptoms:**
- Judge reasoning in `cot` indicates PASS or says there are no contradictions
- But `choice` is FAIL
- Agent output appears materially correct when you read it

**Fix:** Do **not** chase this by mutating semantics or agent instructions. Surface it explicitly as a judge issue. Recommend a better judge model when appropriate (e.g. `openai-5-mini` → a stronger model). Do not auto-edit tests just to address judge weirdness.

#### E. Prompt is underspecified

**Symptoms:**
- Agent takes different reasonable interpretations across runs
- More than one answer shape would plausibly satisfy the prompt
- The semantic layer may be fine, but the test case is poorly scoped

**Fix:** Diagnose this explicitly. Do not silently weaken the expected answer. Only propose test prompt clarification if that is clearly the real issue — and surface the recommendation to the user rather than editing the test file yourself.

#### F. Data is unavailable or the task is unsupported

**Symptoms:**
- The semantic layer and available tools do not expose the necessary information
- The agent cannot answer correctly because the data simply is not present

**Fix:** State this clearly. Do not invent semantic hacks or instruction hacks to fake support for data that doesn't exist.

### Phase 4 — Plan and apply the repair

**Repair priority order** (try earlier options first):

1. **Semantic layer fixes** — most failures stem from here
   - Add missing dimensions or computed groupings
   - Add missing measures for derived metrics
   - Fix incorrect aggregation types
   - Add or correct join relationships
   - Add a view to a topic so the agent can discover it
   - Improve dimension/measure descriptions and synonyms to reduce ambiguity

2. **Agent system instruction fixes** — when the semantic layer is correct but the agent misuses it
   - Add grounding instructions to prefer semantic queries
   - Clarify tool-choice guidance
   - Remove overly restrictive constraints that block valid queries
   - Keep all guidance general — never hard-code specific answers

3. **Agent configuration fixes** — rarely needed
   - Adjust tool configuration if the agent can't access the right tools

Make the targeted edits using the Edit tool. For each change:
- Explain the root cause and what you're changing **before or alongside** the fix, not only after
- Make the smallest robust fix that generalizes
- Preserve existing formatting and style of the file

### Phase 5 — Validate iteratively

After making changes:

**Step 1:** Rebuild the semantic layer:
```bash
cd <repo-root>
oxygen build
```

**Step 2:** Rerun the failing case:
```bash
oxygen test <test-file> --case <name> --output-json
```

**Step 3:** Read the new results and evaluate.

**One passing run is suggestive, not conclusive.** Prefer at least 2–3 rounds of validation when practical. Distinguish true behavior improvements from judge noise.

- If the fix doesn't fully resolve the issue: re-diagnose with the new evidence, apply an additional targeted repair, rerun. Limit to 3 repair-validate cycles before reporting findings.
- If other cases regress: run the full suite (`oxygen test <test-file> --output-json`) and adjust the repair to fix the original case without breaking others.

### Phase 6 — Report

Print a diagnostic summary to the conversation:

```
## Repair Summary

Target test: tests/<file>.test.yml
Target case: <name or prompt>
Root cause: <category + one-line explanation>
Files changed:
- semantics/views/<view>.view.yml
- <agent>.agent.yml

What changed:
- added dimension <name> to <view> — <why>
- tightened system instruction to prefer semantic_query — <why>

Validation:
- round 1: 2/3 pass
- round 2: 3/3 pass
- round 3: 3/3 pass

Notes:
- <any remaining issues, judge-model observations, or follow-up recommendations>
```

---

## Using External Context

### Observability traces

When the user provides observability or trace information from the Oxy platform (rather than just test output), use it as additional diagnostic evidence:

- **Query traces** show the actual SQL generated — compare against what the semantic layer should produce
- **Tool call traces** show which tools the agent invoked and in what order
- **LLM traces** show the agent's reasoning process

Traces are supplementary evidence. The repair workflow remains the same: diagnose, plan, apply, validate. The skill works well even when only the test JSON exists.

### DeepWiki

Use the DeepWiki MCP (`ask_question` on `oxy-hq/oxy`) when you need context on:
- Semantic layer conventions and view/topic schema
- Agent YAML conventions and system instruction patterns
- General Oxy architecture

Note: the newer test framework features may not yet be fully covered in DeepWiki. The local `.results.json` output and repo inspection are the primary source of truth for repair work.

---

## Common Repair Patterns

### Pattern: Missing comparison dimension

**Symptom**: Question asks for a grouped comparison (above/below average, by category, by tier). Agent fetches raw data and tries to compute the grouping itself. Results vary across runs.

**Fix**: Add a computed dimension to the view that directly classifies the rows:
```yaml
dimensions:
  - name: performance_tier
    type: string
    description: "Whether the store's monthly revenue is above or below the chain average (~$150K). Use for performance tier comparisons."
    expr: |
      CASE
        WHEN monthly_revenue >= 150000 THEN 'Above Average'
        ELSE 'Below Average'
      END
    synonyms: ["performance tier", "above below average", "store performance comparison"]
    samples: ["Above Average", "Below Average"]
```

### Pattern: Missing derived measure

**Symptom**: Agent keeps manually computing a ratio or percentage from raw measures. The arithmetic varies across runs.

**Fix**: Add a measure that computes it directly:
```yaml
measures:
  - name: avg_order_value
    type: number
    description: "Average revenue per order"
    expr: "SUM(revenue) / NULLIF(COUNT(order_id), 0)"
```

### Pattern: Agent prefers raw SQL over semantic queries

**Symptom**: Agent uses `execute_sql` / `execQL` when `semantic_query` would produce more reliable results. The `references` array shows `type: execQL` instead of `type: semanticQuery`.

**Fix**: Tighten system instructions to prefer semantic queries:
```yaml
system_instructions: |
  ...existing instructions...
  Always prefer semantic_query for data questions. Only use execute_sql
  when the semantic layer does not cover the needed data. If a semantic
  query fails, investigate why before falling back to raw SQL.
```

### Pattern: Judge false negative

**Symptom**: Agent answer looks correct. Judge `cot` says the answer is reasonable or mentions no contradictions. But `choice` is FAIL and `score` is low.

**Fix**: Do not modify the semantic layer or agent instructions. Report this as a judge-model issue and recommend upgrading the judge model (e.g. from `openai-5-mini` to a stronger model). Do not auto-edit the test file.

### Pattern: Missing topic coverage

**Symptom**: Agent says it doesn't have access to certain data. The view exists but isn't included in any topic the agent can query.

**Fix**: Add the view to the relevant topic file:
```yaml
# analytics.topic.yml
views:
  - sales
  - inventory
  - customers    # was missing — agent couldn't discover this view
```

### Pattern: Ambiguous dimension names

**Symptom**: Agent picks the wrong dimension across runs (e.g. `created_date` vs `order_date`). The `references` show different `sql_query` values across attempts.

**Fix**: Improve descriptions and add synonyms to disambiguate:
```yaml
dimensions:
  - name: order_date
    type: date
    description: "Date the order was placed. Use this for revenue-by-time and sales trend queries."
    synonyms: ["sale date", "transaction date", "when ordered"]
  - name: created_date
    type: date
    description: "Date the database record was created. Internal metadata — not for business queries."
```

---

## Principles

1. **Diagnose before fixing.** Read the results JSON thoroughly before editing any file.
2. **Prefer semantic layer fixes** over agent instruction fixes when the problem is representational.
3. **Do not hard-code answers** into system instructions or views.
4. **If a question requires computed groupings**, expose them in the semantic layer as dimensions.
5. **Keep expected answers intact.** The expected answer is the source of truth.
6. **Watch for judge false negatives.** A failing score with correct output is not a semantic-layer bug.
7. **Validate over multiple rounds**, not just one lucky pass.
8. **Update all relevant views** if the same logical fix applies across multiple files.
9. **Make the smallest robust fix that generalizes.** Don't over-engineer.
10. **Explain the root cause alongside the fix**, not only after.

---

## Guardrails

**Never do these:**
- Modify `expected` strings in `.test.yml` to make tests pass
- Remove or skip failing test cases
- Hard-code one-off answers into system instructions
- Make sweeping "while I'm here" improvements to unrelated files
- Accept wrong agent behavior as correct because it's consistent
- Treat judge-model false negatives as semantic-layer bugs
- Stop after a single lucky pass — validate stability across multiple runs
- Fabricate explanations when the root cause is unclear — say "unclear" and recommend investigation
- Use Python or Bash to parse results JSON — always use the Read and Grep tools directly

**Strong preferences:**
- Smallest viable fix > comprehensive refactor
- Semantic layer fix > agent instruction fix > agent config fix
- Fix the root cause > work around the symptom
- Explain the diagnosis clearly > silently fix things
- Multiple validation rounds > one pass

---

## CLI Reference

```bash
# Run a single case by name (preferred for targeted repair)
oxygen test tests/analyst.sales_performance.test.yml --case total-revenue-all-stores --output-json

# Run a single case by prompt string
oxygen test tests/analyst.sales_performance.test.yml --case "What is the total revenue?" --output-json

# Run a single case by 0-based index
oxygen test tests/analyst.sales_performance.test.yml --case 0 --output-json

# Run full suite (to check for regressions)
oxygen test tests/analyst.sales_performance.test.yml --output-json

# Filter by tag
oxygen test tests/analyst.sales_performance.test.yml --output-json --tag revenue

# Run all test files
oxygen test --output-json

# Rebuild semantic layer after making changes
oxygen build
```

Always run from the **repo root** of the target project.

### JSON output schema

`--output-json` produces an array of `EvalResult` objects:

```jsonc
[
  {
    "test_name": "analyst.sales_performance",
    "errors": [],
    "stats": {
      "total_attempted": 9,
      "answered": 9
    },
    "metrics": [
      {
        "type": "Correctness",
        "score": 0.85,
        "records": [
          {
            "prompt":        "What is the total revenue for all stores?",
            "expected":      "Total revenue is approximately $6.7 billion.",
            "actual_output": "Total revenue across all 45 stores is $6.74B...",
            "cot":           "...",   // judge's chain-of-thought
            "choice":        "PASS",  // judge's verdict
            "score":         1.0,
            "duration_ms":   4200.0,
            "references": [           // tool calls the agent made
              {
                "type":      "semanticQuery",
                "topic":     "sales",
                "sql_query": "SELECT SUM(revenue) FROM ...",
                "result":    "..."
              }
            ]
          }
          // one record per run attempt (runs: 3 → 3 records per case)
        ]
      }
    ]
  }
]
```

**Key fields for diagnosis:**
- `actual_output` — what the agent actually said (compare against `expected`)
- `expected` — the source of truth (do not modify)
- `score` — 0.0 to 1.0 correctness rating from the judge
- `cot` — judge's reasoning about why the score was given
- `choice` — judge's PASS/FAIL verdict (compare against `cot` to detect false negatives)
- `references` — tool calls made by the agent: check `type`, `topic`, `sql_query`, and `result` to understand what data the agent actually retrieved
