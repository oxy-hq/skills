---
name: oxy-build-bench
description: "Builder-agnostic benchmark framework for Oxy build systems. Runs any registered builder against a database spec, evaluates the output with hard CLI checks (oxy validate, oxy build, semantic smoke tests) and soft LLM checks (oxy test consistency or test_case), and produces a side-by-side comparison report. Use when asked to 'benchmark the build agent', 'compare builders', 'evaluate build quality', 'run the build benchmark', or 'test how good the build agent is'."
---

# Oxy Build Benchmark

You are a builder-agnostic evaluation framework. You run one or more build systems against
the same database + task spec, evaluate each output identically, and produce a comparison.

**Build-instance vs build-agent is one use-case.** The framework supports any system that
satisfies the builder interface: *given a database + build_prompt → produce an Oxy instance
directory.* New builders are added via the spec's `builders:` list — no changes to this
skill required.

---

## Activation

Use this skill when the user says:
- "Benchmark the build agent"
- "Compare build-instance vs build agent"
- "Evaluate build quality for [project/spec]"
- "How good is [builder] at building an Oxy instance?"
- "Run oxy-build-bench on [spec]"

---

## Evaluation Levels

The framework has two evaluation levels. The spec's `eval_cases` field determines which
applies automatically.

**Level 1 — Fresh build (default):**
Hard checks + consistency tests. No expected answers needed. Answers the question:
*"Is this semantic layer stable and coherent?"* Use when building from scratch with no
pre-validated Q&A.

**Level 2 — Verified eval cases:**
Hard checks + `test_case` correctness evals. `test_case` runs the agent against each
prompt and uses an LLM judge to score the actual output against a human-verified
`expected` string (PASS/FAIL). Answers the question: *"Does this semantic layer produce
correct answers?"* Use when the spec's `eval_cases` field is populated with
human-verified expected answers (e.g. via `oxy-test-drafter` or hand-authored).

`eval_cases` absent or empty → Level 1. `eval_cases` populated → Level 2.

---

## Step 1: Read the Spec

Read the `.build-bench.yml` specified by the user. If no path is given, look for
`.build-bench.yml` files under `benchmarks/` and ask which to use. If none exist,
tell the user to run `/oxy-skills:bench-init` to create one.

The spec contains:
- `name` — benchmark display name
- `database` / `connection_env` — database type and env var for connection
- `build_prompt` — natural-language description given to each builder
- `builders[]` — list of builders to run (pluggable; see Builder Interface below)
- `required_artifacts[]` — file types the output must contain
- `required_semantics[]` — topic/measure combos for the smoke test
- `eval_cases[]` — **optional.** Absent → Level 1. Populated with human-verified cases → Level 2.

---

## Step 1b: Generate Consistency Questions (Level 1 only)

When `eval_cases` is absent or empty, generate questions for consistency testing.
These are prompts fed to `type: consistency` tests — the agent runs N times and its
answers are compared against each other. **Do not write or execute any SQL here.
There is no source-of-truth derivation in Level 1.**

### Phase A — Schema Discovery

Query the database's information schema to get all tables and columns:

**ClickHouse:**
```sql
SELECT table, name AS column, type
FROM system.columns
WHERE database = '<database_name>'
ORDER BY table, position
```

**Snowflake:**
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = '<schema_name>'
ORDER BY table_name, ordinal_position
```

**DuckDB / generic:**
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
ORDER BY table_name, ordinal_position
```

Group columns by table. Note which columns are:
- Numeric → candidate measure questions (totals, averages, rankings)
- Date/timestamp → enables time-series questions
- Low-cardinality strings → enables grouping/comparison questions
- Primary/foreign keys → enables join-based questions

### Phase B — Generate Questions

Using the schema above, generate 8–12 business questions covering:

| Coverage requirement | Example |
|---------------------|---------|
| At least 1 question per major table or domain | "What is total revenue?" |
| At least 2 aggregate questions (SUM/AVG/COUNT) | "What is the average order value?" |
| At least 2 ranking/top-N questions | "Which store has the highest revenue?" |
| At least 1 time-series question (if a date column exists) | "How has revenue trended month over month?" |
| At least 1 cross-table question (if foreign keys exist) | "What is the labor cost as a percentage of sales?" |

Log a summary:
```
[Consistency question generation — Level 1]
Schema: 12 tables, 87 columns discovered
Questions generated: 10
```

---

## Builder Interface

Each entry in `builders:` must have:
- `name` — display name used in the report
- `invoke` — one of: `command`, `api`, `manual`

### invoke: command
Claude executes the builder by following the referenced command file.
```yaml
- name: build-instance
  invoke: command
  ref: skills/commands/build-instance.md   # path relative to skills root
```
Read `ref` and follow its steps inside the isolated directory.

### invoke: api
Claude calls an HTTP endpoint with the build prompt and polls until done.
```yaml
- name: build-agent
  invoke: api
  endpoint: http://localhost:8080/runs
  domain: builder   # passed as body field
```
POST `{ "prompt": "<build_prompt>", "domain": "<domain>" }`, then GET the run status
until complete. Copy the resulting files to the isolated directory.

### invoke: manual
Claude prints the build prompt, asks the user to run the builder, and resumes once
the user confirms the output directory is ready.
```yaml
- name: build-agent
  invoke: manual
```
Print:
```
[Manual builder: build-agent]
Please run the build agent with this prompt in a fresh empty directory,
then tell me the directory path when it's done:

<build_prompt>
```

### Adding a new builder
To benchmark a new system:
1. Add an entry to the `builders:` list in the spec
2. Set the appropriate `invoke` type
3. No changes to this SKILL.md needed

---

## Step 2: Set Up Isolated Directories

For each builder in the spec, create a fresh isolated directory:

```bash
TIMESTAMP=$(date +%s)
mkdir -p "/tmp/bench-<builder-name>-$TIMESTAMP"
```

Copy/generate minimal `config.yml` and `.env` into each directory, pointing to the
same database as the spec (use the `connection_env` value from the spec for credentials).
Use templates from `skills/commands/build-instance.md` Step 1 to generate these files.

Record the start time for each builder:
```bash
date +%s%3N   # milliseconds since epoch, for latency tracking
```

---

## Step 3: Run Each Builder

For each builder in the spec:
1. Note the start timestamp
2. Run according to its `invoke` type (see Builder Interface above)
3. Note the end timestamp
4. Record latency = end − start in milliseconds

If a builder fails (exits with error, API returns failure, or user cancels), mark it
as FAILED and skip its evaluation. Still evaluate any builders that succeeded.

---

## Step 4: Write the Test Cases

For each builder directory that completed successfully, add test cases before calling
`oxy-bench eval`. The format differs by level.

### Level 1 — Consistency tests (embedded in the agent file)

Consistency tests live inside the `.agent.yml` file itself, not in a separate test file.
Find the agent file and append a `tests:` block using the questions from Step 1b:

```bash
find "$DIR" -name "*.agent.yml" | head -1
```

Add to the agent file:
```yaml
tests:
  - type: consistency
    n: 3
    task_description: "<question from Step 1b>"
  # one entry per generated question
```

Pass the **agent file** as `--test-file` when calling `oxy-bench eval`:
```bash
oxy-bench eval --dir "$DIR" --spec "<spec>" --test-file "$DIR/<agent>.agent.yml" ...
```

### Level 2 — Test case eval file

Write `$DIR/bench_eval.test.yml` using the spec's `eval_cases`. The `expected` values
must be human-verified — do not auto-generate or synthesize them. If `eval_cases` are
present but lack `expected` fields, warn the user and fall back to Level 1.

```yaml
name: "Build Bench Eval — <benchmark name>"
target: <agent-filename>

settings:
  runs: 3
  concurrency: 3
  judge_model: <model-name-from-config>

cases:
  - prompt: "<prompt>"
    expected: "<expected>"   # human-verified
  # include all eval_cases that have an expected field
```

---

## Step 5: Run oxy-bench eval

For each builder directory, call the CLI. It handles all hard checks (file presence,
`oxy validate`, `oxy build`, smoke tests), runs `oxy test` on the test file, computes
the composite score, and returns structured JSON.

```bash
# Level 1 — pass the agent file (consistency tests are embedded in it)
oxy-bench eval \
  --dir "$DIR" \
  --spec "<path-to-spec.build-bench.yml>" \
  --test-file "$DIR/<agent>.agent.yml" \
  --format json

# Level 2 — pass the separate eval test file
oxy-bench eval \
  --dir "$DIR" \
  --spec "<path-to-spec.build-bench.yml>" \
  --test-file "$DIR/bench_eval.test.yml" \
  --format json
```

Collect the JSON output for each builder. Example output shape:
```json
{
  "score": 0.72,
  "level": 1,
  "structural": 1.0,
  "smoke": 0.67,
  "consistency": 0.82,
  "ask_quality": null
}
```

To enforce a CI/CD quality gate (exit code 1 if below threshold):
```bash
oxy-bench eval --dir "$DIR" --spec "<spec>" --test-file "$DIR/bench_consistency.test.yml" \
  --format json --min-accuracy 0.7
```

---

## Step 6: Report

Synthesize the per-builder JSON from Step 5 into a side-by-side comparison table.

```
## Build Benchmark: <name>
## Evaluation Level: 1 (consistency) | 2 (verified eval cases)

### Build Latency
| Builder        | Latency  |
|---------------|---------|
| build-instance | 4m 12s  |
| build-agent    | 1m 38s  |

### Hard Checks
| Check                | build-instance          | build-agent             |
|----------------------|------------------------|------------------------|
| File presence        | topic:2 agent:1 view:8 ✓ | ...                  |
| oxy validate         | PASS ✓                  | PASS ✓                 |
| oxy build            | PASS ✓                  | FAIL ✗                 |
| Semantic smoke (X/N) | 3/3 ✓                   | 0/3 — build failed     |

### Soft Checks
| Metric            | build-instance | build-agent |
|-------------------|---------------|-------------|
| Consistency score | 82%           | N/A         |
| Ask quality score | 74%           | N/A         |  ← Level 2 only; omit row if Level 1

### Composite Score
| Builder        | Score | Level |
|---------------|-------|-------|
| build-instance | 72%   | 1     |
| build-agent    | 18%   | 1 (oxy build failed — smoke + consistency skipped) |

### Failures
- build-agent: oxy build failed
```

**Head-to-head for cases without `expected`** (Level 2 only):
After collecting results from all builders, compare their agent outputs for each case
that has no `expected` value using a brief LLM judgment:
> "For the question: [prompt]. Answer A: [output_a]. Answer B: [output_b].
> Which is more complete and accurate? State preference in one sentence."

Record A/B/Tie per question and append to the report.

If only one builder ran, produce a single-column evaluation.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Builder fails or times out (>15min) | Mark as FAILED; skip Steps 4–6 for that builder |
| `oxy-bench eval` exits non-zero | Record builder as failed; note error output in report |
| Database connection fails | Stop; ask user to verify `connection_env` |
| Agent file not found in builder directory | Warn user; skip test file generation for that builder |
| `eval_cases` present but no `expected` fields | Warn user; write Level 1 consistency file instead |
| Builder API unavailable | Fall back to `invoke: manual` automatically |
