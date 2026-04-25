# oxy-agentic-builder

Authoring guide for Oxy `.agentic.yml` files — multi-step FSM agents that
turn a natural-language question into a grounded query, run it, and
explain the result. Use this skill when creating or editing the
`analytics.agentic.yml`, `app_builder.agentic.yml`, or any custom
agentic agent that should reason over the project's semantic layer.

## What this skill covers

- The fixed pipeline (`clarifying → specifying → solving → executing →
  interpreting`) and what each state can do.
- Every legal top-level field: `instructions`, `databases`, `context`,
  `llm`, `thinking`, `states`, `validation`, `semantic_engine`.
- Per-state overrides: `instructions`, `thinking`, `max_retries`, `model`.
- The validation rule catalog by stage.
- Common pitfalls (skipped solving, stringly-typed `thinking: disabled`,
  unknown rule names) and how to triage them.

## What this skill does NOT cover

- `.agent.yml` (single-call tool-loop agents) — see `oxy-workflow-builder`.
- `.workflow.yml` / `.procedure.yml` (deterministic pipelines) — see
  `oxy-workflow-builder`.
- `.app.yml` (data apps) — see `oxy-app-builder`.
- `.view.yml` / `.topic.yml` (the semantic layer the agent queries) —
  see `oxy-semantic-layer`.
- `.test.yml` / `.aw.test.yml` (eval suites) — see `oxy-test-drafter`.

## Files

| File                  | Purpose                                                |
|-----------------------|--------------------------------------------------------|
| `SKILL.md`            | Authoring guide; loaded into Claude as the system prompt. |
| `QUICK-REFERENCE.md`  | Dense cheatsheet — tables only, no prose.              |
| `agentic-template.yml`| A working starter file with comments on every block.   |
| `README.md`           | This file.                                             |

## When this skill activates

The skill description triggers on requests like:

- "Create an analytics agent for my warehouse."
- "Build an `.agentic.yml` that uses the semantic layer."
- "Why is my agentic agent skipping the solving state?"
- "Should I use `.agentic.yml` or `.agent.yml` for this?"
- "Add a per-state model override for clarifying."

For broader Oxy questions, the `oxy-repair` skill handles cross-cutting
diagnostics; for the underlying semantic layer, `oxy-semantic-layer`.
