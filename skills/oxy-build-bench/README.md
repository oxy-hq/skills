# oxy-build-bench

A builder-agnostic benchmark framework for Oxy build systems.

Run any number of build systems (Claude 1-shot skills, Hai's build agent, or future
builders) against the same database and task spec. Each builder gets an isolated
workspace. Outputs are evaluated identically across:

- **Hard checks** — `oxy validate`, `oxy build`, semantic smoke tests (deterministic, no LLM)
- **Soft checks** — `oxy test` consistency or test_case evals (LLM-judged)

Results are reported in a side-by-side comparison table with a composite score.

## Evaluation Levels

The framework has two levels, selected automatically based on whether the spec has
`eval_cases`:

| Level | When | What it measures |
|-------|------|-----------------|
| **1 — Consistency** | No `eval_cases` in spec (default) | Is the semantic layer stable and coherent? |
| **2 — Correctness** | `eval_cases` present with human-verified `expected` answers | Does the semantic layer produce correct answers? |

**Level 1** is the right starting point for any fresh build. It requires no prior
knowledge of the database and no expected answers. The agent runs each question N times
and the framework checks whether it gives consistent answers.

**Level 2** requires a human to have verified the expected answers first (via
`oxy-test-drafter` or hand-authored). Use it for regression testing against known-good
instances or customer Q&A pairs.

## Quick Start

```bash
# Compare all builders in a spec (Level 1 — no eval_cases needed)
claude /oxy-build-bench benchmarks/pokehouse/pokehouse.build-bench.yml

# Single builder only
claude /oxy-build-bench benchmarks/pokehouse/pokehouse.build-bench.yml --builder build-instance

# Eval-only: skip building, evaluate existing directories
claude /oxy-build-bench benchmarks/pokehouse/pokehouse.build-bench.yml \
  --eval-only --dir-a /tmp/run-a --dir-b /tmp/run-b
```

## Benchmark Spec (`.build-bench.yml`)

```yaml
name: "My Analytics Benchmark"

database: clickhouse
connection_env: CLICKHOUSE_URL

build_prompt: |
  Build a complete analytics agent for our database.
  It should answer questions about revenue, performance, and trends.

builders:
  - name: build-instance
    invoke: command
    ref: skills/commands/build-instance.md

  - name: build-agent
    invoke: manual   # or: api + endpoint when the API is available

required_artifacts:
  - type: topic
  - type: agent

required_semantics:
  - topic_contains: sales
    must_have_measures: [total_revenue]

# eval_cases: omit this field to use Level 1 (consistency).
# Add human-verified cases here to use Level 2 (correctness).
#
# To bootstrap Level 2 cases, run oxy-test-drafter on the built instance,
# review the drafted expected answers, then copy them here.
#
# eval_cases:
#   - name: total-revenue
#     prompt: "What is total revenue?"
#     expected: "Total revenue across all locations is approximately $4.2M."
```

## How Level 1 (Consistency) Works

1. **Schema discovery** — queries `information_schema` to get all tables and columns
2. **Question generation** — LLM generates 8–12 business questions from the schema
3. **Consistency testing** — each question is run N times via `oxy test type: consistency`;
   the agent's answers are compared against each other by an LLM judge
4. No SQL execution, no expected values, no source-of-truth derivation

## How Level 2 (Correctness) Works

1. Same hard checks as Level 1
2. Uses `eval_cases` from the spec as `type: test_case` evals
3. Each case runs the agent against a `prompt`, then an LLM judge scores the actual
   output against the human-verified `expected` string (PASS/FAIL)
4. `expected` values must be human-verified — the framework does not auto-generate them

## Scoring

### Level 1
| Dimension | Weight | How measured |
|-----------|--------|-------------|
| Structural validity | 20% | `oxy validate` + `oxy build` + file presence |
| Semantic smoke | 30% | `oxy run smoke_test.procedure.yml` per required topic |
| Consistency | 50% | `oxy test type: consistency` — N runs, pairwise agreement |

### Level 2
| Dimension | Weight | How measured |
|-----------|--------|-------------|
| Structural validity | 15% | `oxy validate` + `oxy build` + file presence |
| Semantic smoke | 20% | `oxy run smoke_test.procedure.yml` per required topic |
| Consistency | 15% | `oxy test type: consistency` |
| Ask quality | 50% | `oxy test type: test_case` — LLM judge vs human-verified expected |

## Adding a New Builder

Add one entry to the `builders:` list in your `.build-bench.yml`:

```yaml
builders:
  - name: my-new-builder
    invoke: api
    endpoint: http://my-builder:8080/runs
    domain: builder
```

Supported `invoke` types:
- `command` — Claude follows the referenced command file in the isolated directory
- `api` — POST the build prompt to an HTTP endpoint, poll until done
- `manual` — Claude prints the prompt and waits for you to run the builder and confirm

## Benchmark Scenarios

Pre-built specs in `benchmarks/`:

| Spec | Database | Description |
|------|----------|-------------|
| `benchmarks/pokehouse/` | ClickHouse | Restaurant chain analytics (sales, labor, orders) |
| `benchmarks/hubspot/` | Snowflake | CRM/SaaS MRR and sales performance |

## Relationship to Nick's Testing Framework

Nick's framework (`oxy-test-drafter`, `oxy-repair`) tests the **ask agent** — whether
an already-built instance answers questions correctly.

This framework tests the **build side** — whether a builder can create a correct
instance from scratch. It uses `oxy test` as its final evaluation step, so the two
frameworks compose naturally:

```
[Builder] → [Oxy Instance] → [oxy test] → Score
                ↑
         oxy-build-bench orchestrates this pipeline
```

To graduate from Level 1 to Level 2 for an instance:
1. Run Level 1 to confirm the build is structurally sound
2. Use `oxy-test-drafter` to bootstrap expected answers from the built instance
3. Review and verify the drafted expected answers
4. Add the verified cases to `eval_cases` in the spec
5. Re-run — the framework automatically uses Level 2
