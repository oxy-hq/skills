# Oxy `.agentic.yml` Quick Reference

## File shape

```yaml
instructions: |                # global system prompt
databases: [warehouse]         # required in practice
context:                       # globs relative to this file
  - ./semantics/**/*
llm:
  ref: claude-sonnet-4-6
thinking: adaptive
states:
  clarifying:   { ... }
  specifying:   { ... }
  solving:      { ... }
  executing:    { ... }
  interpreting: { ... }
validation: { rules: { specified: [], solvable: [], solved: [] } }
semantic_engine: { vendor: cube, base_url: ..., api_token: "${X}" }
```

## Pipeline states (fixed — not user-defined)

| State          | Purpose                                | Skipped when                            |
|----------------|----------------------------------------|-----------------------------------------|
| `clarifying`   | Triage; resolve metrics/dimensions     | —                                       |
| `specifying`   | Ground intent; resolve joins           | —                                       |
| `solving`      | Generate SQL                           | Semantic layer compiled the spec        |
| `executing`    | Run query; validate results            | —                                       |
| `interpreting` | Natural-language answer + chart        | —                                       |

## State override fields

| Field          | Type   | Notes                                                 |
|----------------|--------|-------------------------------------------------------|
| `instructions` | string | Appended to the global `instructions:` for this state |
| `thinking`     | mixed  | Same forms as top-level `thinking:`                   |
| `max_retries`  | u32    | Tool-use rounds before falling into Diagnosing        |
| `model`        | string | Replaces model ID; vendor/key/base_url inherited      |

## `llm:` fields

| Field               | Default                  | Notes                                                                |
|---------------------|--------------------------|----------------------------------------------------------------------|
| `ref`               | —                        | Resolves vendor + key + model from `config.yml` entry                |
| `vendor`            | `anthropic`              | `anthropic` \| `openai` \| `openai_compat`                            |
| `model`             | from `ref`               | Overrides model resolved from `ref`                                  |
| `api_key`           | env var                  | Falls back to `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`                  |
| `base_url`          | provider default         | Anthropic proxy / OpenAI Responses base / OpenAI-compat root         |
| `max_tokens`        | 4096                     | Per-call output cap                                                  |
| `thinking`          | none                     | Beats top-level `thinking:`                                          |
| `extended_thinking` | none                     | UI-toggled `{ model, thinking }` preset                              |

## `thinking:` forms

```yaml
thinking: adaptive            # shorthand
thinking: disabled            # shorthand — bare or quoted both work
thinking: "disabled"          # equivalent
thinking: effort:low          # OpenAI o-series shorthand
thinking: { budget_tokens: 10000 }
thinking: { effort: medium }  # low | medium | high
```

`disabled` is a string identifier, not a boolean — bare `false` is rejected.

## Context globs by extension

| Pattern        | Where it goes                                       |
|----------------|-----------------------------------------------------|
| `*.view.yml`   | Semantic catalog                                    |
| `*.topic.yml`  | Semantic catalog                                    |
| `*.sql`        | Example queries injected into Solving prompt        |
| `*.md`         | Domain docs injected into Clarifying / Interpreting |
| `*.procedure.yml` | Indexed for `search_procedures`                  |

## Validation rules

| Stage       | Rule names                                                                         |
|-------------|------------------------------------------------------------------------------------|
| `specified` | `metric_resolves`, `join_key_exists`, `filter_unambiguous`                         |
| `solvable`  | `sql_syntax`, `tables_exist_in_catalog`, `spec_tables_present`, `column_refs_valid`, `timeseries_order_by_check` |
| `solved`    | `non_empty`, `shape_match`, `no_nan_inf`, `outlier_detection`, `timeseries_date_check`, `truncation_warning`, `null_ratio_check`, `duplicate_row_check` |

Tunable params:

| Rule                  | Params                                                                          |
|-----------------------|---------------------------------------------------------------------------------|
| `sql_syntax`          | `dialect`: generic \| ansi \| postgresql \| mysql \| bigquery \| duckdb \| snowflake |
| `outlier_detection`   | `threshold_sigma` (5.0), `min_rows` (4)                                         |
| `null_ratio_check`    | `threshold` (0.5)                                                               |
| `duplicate_row_check` | `max_duplicate_ratio` (0.1)                                                     |

## `semantic_engine:` (optional)

| Field                                | Cube     | Looker   |
|--------------------------------------|----------|----------|
| `vendor`                             | `cube`   | `looker` |
| `base_url`                           | required | required |
| `api_token`                          | required | —        |
| `client_id` / `client_secret`        | —        | required |

`${VAR}` env-var interpolation; missing var fails at startup.

## Decision matrix

| Need                                  | Use            |
|---------------------------------------|----------------|
| Chat over the semantic layer          | `.agentic.yml` |
| One-shot tool-using agent             | `.agent.yml`   |
| Deterministic multi-step pipeline     | `.workflow.yml`|

## Common errors → fix

| Error                                      | Fix                                                       |
|--------------------------------------------|-----------------------------------------------------------|
| `no databases configured`                  | Add a connector name to `databases:`                      |
| `unsupported connector type: '…'`          | Match name to a `config.yml` entry                        |
| `ambiguous table: '…'`                     | Drop one DB or qualify view's `data_source`               |
| `environment variable '${X}' is not set`   | Export the env var before launch                          |
| `unsupported semantic engine vendor: '…'`  | Use `cube` or `looker`, or omit `semantic_engine`         |
| `validation config error: unknown rule …`  | Use a rule name from the table above                      |
| `YAML parse error: duplicate key`          | Each top-level key must appear once per file              |
| State override silently ignored            | State key must be one of the 5 fixed names                |
| `thinking: false` rejected                 | Use `thinking: disabled` (bare or quoted) — never bare boolean `false` |

## Validation workflow

```bash
oxy validate --file path/to/your.agentic.yml   # structural parse
oxy validate                                   # all configs
oxy build                                      # semantic layer
```

## Naming

- File: `<stem>.agentic.yml`; stem becomes the `agent_id`.
- snake_case for every `name:` you reference (topics, views, measures).
- Don't add `# yaml-language-server:` schema comments — Oxy publishes
  no canonical schema URL for `.agentic.yml`.
