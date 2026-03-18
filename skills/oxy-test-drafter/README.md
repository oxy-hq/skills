# Oxy Test Drafter

Bootstrap or refine `.test.yml` eval files for Oxy agents and workflows — even when you don't know the correct expected answers yet.

## What It Does

The **oxy-test-drafter** skill automates the tedious part of writing evals: figuring out what the right answer actually is. It:

1. Scaffolds a `.test.yml` from a list of prompts (or loads an existing file)
2. Runs `oxy test <file> --output-json` and parses the JSON traces
3. Reads `actual_output` across multiple run attempts to identify stable facts
4. Drafts concise, natural-language `expected` strings for each case
5. Flags flaky, ambiguous, or unsupported cases with diagnostic notes
6. Outputs the revised test file and a short summary

**This skill is for test drafting only.** It does not modify semantic files, agent YAML, system instructions, or any code outside the test file.

---

## Required Inputs

Either:
- An existing `.test.yml` with `DRAFT:` placeholders or missing `expected` strings, **or**
- A list of prompts you want to test

Plus:
- Path to the target agent/workflow (e.g. `analyst.agent.yml`)
- The repo root of the target project (so `oxy test` can run correctly)

---

## Example Invocations

```
"I have tests/analyst.sales_performance.test.yml with placeholder expected values.
Run it and fill in the expected strings."
```

```
"Create a test file for my analyst agent covering these prompts:
- What is total revenue for all stores?
- Which store had the highest sales last month?
- What are the top 5 products by units sold?"
```

```
"My test file has flaky results on the revenue question. Help me figure out
what a stable expected looks like."
```

---

## Output

### 1. Updated `.test.yml`

Placeholders replaced with drafted `expected` strings. Relative time prompts
rewritten to absolute periods where the run context made the period clear.

### 2. Diagnostic summary (in conversation)

```
## Test Drafting Summary

Updated test file: tests/analyst.sales_performance.test.yml
Cases analyzed: 9
Stable expecteds drafted: 6
Partial/uncertain: 2
Flaky prompts: 1

### Per-case results
| Prompt (truncated)           | Class              | Notes                        |
|------------------------------|--------------------|------------------------------|
| What is total revenue…       | stable             | consistent across 3 runs     |
| Which store had highest…     | stable             | consistent across 3 runs     |
| Top 5 products by units…     | stable_but_partial | ranking stable; values vary  |
| Revenue by region last Q…    | flaky              | results disagree; see notes  |

### Recommended follow-up
- "Revenue by region" prompt is ambiguous — consider splitting by specific region
```

---

## `expected` String Style Guide

Good expected strings are **natural, approximate, and honest**:

| Rule | Good | Bad |
|------|------|-----|
| No "The response should" prefix | `Total revenue is ~$6.7B.` | `The response should explain total revenue...` |
| Approximate numbers | `approximately $6.7 billion` | `$6,737,218,004.32` |
| Absolute time periods | `November 2025` | `last month` |
| Anchor top entries for rankings | `#1 had ~25K engagements; #5 had ~10K` | Full list of all 20 items |
| Encode refusals correctly | `Cannot calculate because targets are company-level only. A correct answer explains this and offers the company-level figure.` | Leave blank or say "should decline" |
| No schema/field names | `Revenue by store` | `store__weekly_sales summed by store__store_id` |

---

## Test File Format

```yaml
name: "Sales Performance Tests"
target: analyst.agent.yml

settings:
  concurrency: 5
  runs: 3
  judge_model: openai-5-mini

cases:
  - prompt: What is the total revenue for all stores?
    expected: |
      Total revenue across all locations is approximately $6.7 billion.
    tags:
      - revenue
      - stores
    tool: ""
```

**File naming**: `<agent-stem>.<category>.test.yml`
**File location**: `tests/` subdirectory of the target repo

---

## CLI Reference

```bash
# Run a test file (from repo root of target project)
oxy test tests/analyst.sales_performance.test.yml --output-json

# Filter by tag
oxy test tests/analyst.sales_performance.test.yml --output-json --tag revenue

# Run all test files
oxy test --output-json
```

Output is written to `<test-name>.results.json` in the same directory as the test file.

---

## What This Skill Does NOT Do

- Modify agent YAML, workflow YAML, or semantic layer files
- Remove difficult or flaky test cases
- Accept null/empty metric results as valid answers
- Invent expected values when the evidence is insufficient
