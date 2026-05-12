---
name: oxy-agentic-builder
description: Build and configure Oxy `.agentic.yml` files — multi-step FSM agents that ground questions in the semantic layer, generate SQL, execute it, and interpret results. Use when the user asks to create, edit, or troubleshoot an agentic analytics or app-builder agent, or to choose between `.agent.yml`, `.agentic.yml`, and `.workflow.yml`.
---

# Oxy Agentic Builder

You are an expert at authoring Oxy `.agentic.yml` files. These configure a
fixed-shape multi-step pipeline (clarify → specify → solve → execute →
interpret) that grounds a natural-language question in the project's
semantic layer, generates and runs SQL, and produces a structured answer.

## When to use which agent file

| File              | Use when                                                                                  |
|-------------------|-------------------------------------------------------------------------------------------|
| `.agentic.yml`    | Conversational data Q&A backed by the semantic layer; multi-turn, validator-driven        |
| `.agent.yml`      | Single LLM call with custom tools (Python, raw SQL, file I/O); no semantic layer required |
| `.workflow.yml`   | Deterministic multi-step pipeline — no LLM reasoning between steps                        |

If the user's data already has views and topics, prefer `.agentic.yml`. If
they need an agent that runs a Python helper or reads arbitrary files,
use `.agent.yml`. If the steps are fixed and don't need an LLM to choose
between them, use `.workflow.yml`.

## File shape

`.agentic.yml` files are short — almost everything is a sensible default.
A minimal file looks like this:

```yaml
databases:
  - warehouse
llm:
  ref: claude-sonnet-4-6
context:
  - ./semantics/**/*.view.yml
  - ./semantics/**/*.topic.yml
```

The full annotated shape (every field is optional except `databases` in
practice — the agent has nothing to query without one):

```yaml
instructions: |                       # Global system prompt for every state
  ...                                 # Optional. Per-state additions go below.

databases:                            # Connector names from config.yml
  - warehouse

context:                              # Globs resolved relative to this file
  - ./semantics/**/*.view.yml         # → semantic catalog
  - ./semantics/**/*.topic.yml        # → semantic catalog
  - ./example_sql/*.sql               # → injected into Solving prompt
  - ./docs/*.md                       # → injected into Clarifying/Interpreting
  - ./procedures/**/*.procedure.yml   # → discoverable via search_procedures

llm:                                  # Model + auth (defaults to Anthropic)
  ref: claude-sonnet-4-6              # Reference an entry in config.yml
  max_tokens: 8192
  extended_thinking:                  # UI-toggled alternative preset
    model: claude-opus-4-6
    thinking: adaptive

thinking: adaptive                    # Default thinking mode for all states

states:                               # Per-state overrides (see below)
  clarifying: { ... }
  specifying: { ... }
  solving:    { ... }
  executing:  { ... }
  interpreting: { ... }

validation:                           # Optional; defaults run all rules
  rules:
    specified: [ ... ]
    solvable:  [ ... ]
    solved:    [ ... ]

semantic_engine:                      # Optional; omit to use Oxy's bundled
  vendor: cube                        # semantic layer
  base_url: https://cube.example.com
  api_token: "${CUBE_API_TOKEN}"
```

## The pipeline

The runtime owns the state machine. You cannot add, rename, or remove
states — only configure overrides on the ones below.

```
Clarifying → Specifying → Solving → Executing → Interpreting → Done
     ↑           ↑           ↑          ↑             ↑
     └───────────┴───────────┴──────────┴─────────────┘
                  Diagnosing (back-edges)
```

| State          | What it does                                            | Tools available                                          |
|----------------|---------------------------------------------------------|----------------------------------------------------------|
| `clarifying`   | Triage question type; resolve metrics/dimensions        | `search_catalog`, `search_procedures`, `ask_user`        |
| `specifying`   | Ground intent into a query spec; resolve joins          | `get_valid_dimensions`, `get_column_range`               |
| `solving`      | Generate SQL — skipped if semantic layer compiled it    | `explain_plan`, `dry_run`                                |
| `executing`    | Run the query against the connector; validate results   | (none — runs the SQL)                                    |
| `interpreting` | Turn results into natural language + chart              | `render_chart`                                           |

**Skipped state:** if `clarifying` produces an intent the semantic layer
can compile directly, `solving` is dynamically skipped and the spec goes
straight to `executing`. Do not write `instructions:` that assume the LLM
authors SQL — it may never see the prompt.

**Back-edges:** when a validator fails (see `validation:` below), the
solver enters `diagnosing`, picks a recovery target, and re-enters the
upstream state. Retries do not anchor on the previous failure — generate
fresh from the spec.

## Top-level fields

### `instructions`

A string injected into every state's system prompt. Use it for stable
context: persona, dialect quirks, currency/locale, semantic-layer
conventions ("MRR = the `monthly_recurring_revenue` measure"). Keep
state-specific guidance in the per-state `instructions:` instead.

### `databases`

A list of names referencing entries in the project's `config.yml`. The
HTTP layer resolves these to live connectors. All Oxy-supported types
work (DuckDB, Postgres, BigQuery, Snowflake, ClickHouse). Without a
database the pipeline has nothing to execute against.

### `context`

Globs resolved relative to the `.agentic.yml`'s directory, bucketed by
extension at load time:

| Extension                      | Where it goes                                       |
|--------------------------------|-----------------------------------------------------|
| `.view.yml` / `.view.yaml`     | Semantic catalog                                    |
| `.topic.yml` / `.topic.yaml`   | Semantic catalog                                    |
| `.sql`                         | Example queries injected into Solving's prompt      |
| `.md`                          | Domain docs injected into Clarifying / Interpreting |
| `.procedure.yml` / `.yaml`     | Indexed for the `search_procedures` tool           |

Other extensions are silently ignored. Use a wide enough glob —
`./semantics/**/*` — to catch the full catalog rather than enumerating
files.

### `llm`

| Field                | Type            | Notes                                                                       |
|----------------------|-----------------|-----------------------------------------------------------------------------|
| `ref`                | string          | Model entry from `config.yml`; vendor/key/base_url inherit from that entry. |
| `vendor`             | enum            | `anthropic` (default) \| `openai` \| `openai_compat`                         |
| `model`              | string          | Overrides the model resolved from `ref`.                                    |
| `api_key`            | string          | Falls back to `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`.                        |
| `base_url`           | string          | Proxy / Responses API base / OpenAI-compat root.                             |
| `max_tokens`         | u32             | Defaults to 4096.                                                            |
| `thinking`           | see below       | Default thinking mode for all states; takes precedence over top-level.      |
| `extended_thinking`  | `{ model, thinking }` | Preset activated by the UI's "extended thinking" toggle.                |

Prefer `ref:` over inline credentials. The model entry centralises auth
so multiple agents share one secret.

### `thinking`

Three forms accepted:

```yaml
thinking: adaptive          # shorthand
thinking: disabled          # shorthand — bare or quoted both work
thinking: "disabled"        # equivalent to bare form
thinking: effort:low        # OpenAI o-series shorthand (low|medium|high)

thinking:                   # explicit budget (Anthropic)
  budget_tokens: 10000

thinking:                   # OpenAI o-series map form
  effort: medium
```

Per-state overrides accept the same forms. `disabled` is a string
identifier — bare `disabled` and quoted `"disabled"` are both accepted.
The bare boolean `false` is **rejected**; never write `thinking: false`.

### `states`

Each key matches a pipeline stage by snake_case name. Legal keys:
`clarifying`, `specifying`, `solving`, `executing`, `interpreting`.
Unknown keys are silently ignored — typos cost nothing visible at parse
time, so spell carefully.

Per-state fields:

| Field          | Type             | Meaning                                                                  |
|----------------|------------------|--------------------------------------------------------------------------|
| `instructions` | string           | Appended to the state's system prompt, on top of the global `instructions:`. |
| `thinking`     | (see above)      | Overrides the global thinking config for this state only.                |
| `max_retries`  | u32              | Cap on tool-use rounds before the state fails into Diagnosing.           |
| `model`        | string           | Replaces the model ID for this state. Vendor / key / base_url are inherited. |

Common pattern: a cheap model for `clarifying`, a powerful model for
`solving`, and `thinking: disabled` on `interpreting` to avoid burning
tokens on prose.

### `validation`

When the section is absent, every built-in rule runs with defaults. When
it's present, only the rules you list are evaluated. Stages and rule
names are fixed by the runtime:

| Stage        | Rule                                                                              |
|--------------|-----------------------------------------------------------------------------------|
| `specified`  | `metric_resolves`, `join_key_exists`, `filter_unambiguous`                       |
| `solvable`   | `sql_syntax` (`dialect: …`), `tables_exist_in_catalog`, `spec_tables_present`, `column_refs_valid`, `timeseries_order_by_check` |
| `solved`     | `non_empty`, `shape_match`, `no_nan_inf`, `outlier_detection` (`threshold_sigma`, `min_rows`), `timeseries_date_check`, `truncation_warning`, `null_ratio_check` (`threshold`), `duplicate_row_check` (`max_duplicate_ratio`) |

Each rule entry takes `name`, `enabled` (defaults to `true`), and any
rule-specific params:

```yaml
validation:
  rules:
    solvable:
      - name: sql_syntax
        dialect: postgresql        # generic | ansi | postgresql | mysql
                                   # | bigquery | duckdb | snowflake
    solved:
      - name: outlier_detection
        threshold_sigma: 5.0
        min_rows: 4
      - name: null_ratio_check
        threshold: 0.5
      - name: duplicate_row_check
        max_duplicate_ratio: 0.1
```

### `semantic_engine`

Optional. When set, the solver routes through Cube or Looker instead of
the bundled semantic layer.

```yaml
semantic_engine:
  vendor: cube                          # or `looker`
  base_url: https://cube.example.com
  api_token: "${CUBE_API_TOKEN}"        # Cube only

# Looker variant
# semantic_engine:
#   vendor: looker
#   base_url: https://myco.looker.com
#   client_id: "${LOOKER_CLIENT_ID}"
#   client_secret: "${LOOKER_CLIENT_SECRET}"
```

`${VAR}` placeholders are resolved against the process environment at
startup. A missing variable fails fast — the solver never starts with an
empty credential.

## System-instruction patterns

A good `instructions:` string follows this shape:

1. **Role** — one sentence stating who the agent is and what it's for.
2. **Domain conventions** — currency, time zones, fiscal calendar,
   terminology aliases ("MRR", "AOV", "DAU").
3. **Semantic-layer pointers** — name the topics and views the agent
   should prefer; flag any that are deprecated.
4. **Output style** — how to phrase numbers, when to include charts,
   how to handle ambiguity.

```yaml
instructions: |
  You are a revenue analytics assistant for Acme Corp.

  Conventions:
  - All currency in USD; dates as ISO 8601.
  - Fiscal quarter starts in February.
  - "Customer" = the `customer` entity on the `accounts` topic, not
    `users` (which counts seats).

  Prefer measures defined in the semantic layer over hand-written
  aggregations. If a question can be answered by the `revenue` topic,
  do not author SQL.
```

Keep state-specific overrides surgical:

```yaml
states:
  clarifying:
    instructions: |
      "This week" means Monday 00:00 to Sunday 23:59 in America/New_York.
  solving:
    instructions: Always alias aggregate columns; prefer CTEs over subqueries.
```

Avoid duplicating the global `instructions:` inside per-state blocks —
they're concatenated, not replaced.

## Common pitfalls

| Symptom / error                                         | Likely cause                                                | Fix                                                                                          |
|---------------------------------------------------------|-------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| `no databases configured`                               | `databases:` empty or missing                               | Add at least one connector name matching `config.yml`.                                       |
| `unsupported connector type: …`                         | `databases:` lists a name not in `config.yml`               | Rename to match a real entry, or add the connector to `config.yml`.                          |
| `ambiguous table: …`                                    | Same table name in two configured databases                 | Either drop one database or qualify the topic's `data_source` to disambiguate.               |
| `environment variable '${X}' is not set`                | `${VAR}` placeholder in `semantic_engine` / `llm`           | Export the env var before starting the server; missing values never silently pass through.   |
| `unsupported semantic engine vendor: …`                 | `semantic_engine.vendor` is not `cube` or `looker`          | Use one of the two bundled adapters, or omit the section entirely.                           |
| `semantic engine connection error: …`                   | `semantic_engine.base_url` unreachable / token rejected     | Verify the URL and credentials with `curl` before launching the server.                      |
| `validation config error: unknown rule '…'`             | Rule name typo                                              | Use only the rule names listed in the table above; case-sensitive snake_case.                 |
| State override silently ignored                         | Misspelled state key (`solve` vs `solving`)                 | State keys are fixed: `clarifying`, `specifying`, `solving`, `executing`, `interpreting`.    |
| `thinking: false` rejected                              | Boolean `false` is not a valid thinking mode                | Use `thinking: disabled` (bare or quoted both work); the shorthand is a string identifier, never a boolean. |
| LLM never sees the `solving` instructions               | Question was answerable by the semantic layer               | Move guidance into `clarifying` or `interpreting`; `solving` is skipped on the semantic path. |
| `YAML parse error: duplicate key`                       | A top-level key (`llm:`, `states:`) appears twice           | Each top-level key must appear at most once per file.                                        |

## Validation workflow

`.agentic.yml` validation is structural — `oxy validate` parses the file
through the same loader the runtime uses but does not exercise the LLM.

```bash
# Parse a single file. Catches schema errors, missing env vars,
# unsupported vendors, glob errors.
oxy validate --file path/to/your.agentic.yml

# Parse every config in the project.
oxy validate

# Smoke-test the semantic layer (used in `solving` and `clarifying`).
# Run this before launching an agent against fresh views/topics.
oxy build
```

Iteration loop:

1. Edit the `.agentic.yml`.
2. `oxy validate --file <path>` — catches structural errors fast.
3. `oxy build` — catches semantic-layer drift the agent depends on.
4. Launch the dev server and ask the agent a question that exercises the
   path you changed.
5. Watch the streamed events: `LlmStart`/`LlmEnd` per round, `ThinkingStart`
   bracketing reasoning, validator failures surfacing as `Diagnosing`
   transitions. If a validator keeps tripping, tune its params under
   `validation:` rather than disabling it outright.

## DeepWiki fallback

For features beyond this skill, query DeepWiki with:

> I am a user of this project, not its maintainer. Please prioritize the
> project docs, examples, and json-schemas to answer my question: <…>

Restrict to the `oxy-hq/oxy` repository.
