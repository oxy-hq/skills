# Agentic Browser Test Skill

Generate a runnable `.flow.test.yml` for the agentic browser-testing layer in
[`oxy-hq/oxygen-internal`](https://github.com/oxy-hq/oxygen-internal) from a
verbal description of a feature. The dev never has to learn the YAML schema,
the runner internals, or the action-cache contract.

## What it does

When you're working in a Claude Code session against `oxy-hq/oxygen-internal`
and you say something like:

> "test that clicking the new 'Reset' button clears the workspace"
>
> "add a regression test for the bug I just fixed where pressing Cmd+Enter in
>  the agent builder dialog submitted twice"
>
> "make sure the chat panel still streams responses after this refactor"

…this skill writes a working `.flow.test.yml` file under
`web-app/tests/agentic/flows/` that you can run with `pnpm test:agentic`.

## How it works

1. **Reads the source of truth on every invocation.** The bespoke runtime,
   schema, and authoring conventions evolve. The skill re-reads the README at
   `web-app/tests/agentic/README.md`, the JSON schema at
   `json-schemas/flow-test.json`, the existing flow files, and the
   `internal-docs/agentic-browser-testing-*.md` docs each time it runs. It
   never hard-codes a frozen view of the schema.

2. **Picks the right primitives for what you described.**
   - `target:` — chat / ide / threads / onboarding / any.
   - `setup:` — fixture commands (today: `reset_test_file`, `goto:/path`;
     more land over time).
   - `act:` — natural-language steps with explicit `[data-testid=…]`
     selectors when they exist (drops cold cost ~5×).
   - `wait_for:` — `streaming_complete` / `network_idle` / `selector:<sel>`
     after each user action so the next step doesn't race the page.
   - `assert:` for structural claims, `judge:` for the dev's stated success
     criterion in plain English.
   - `cache_actions: true` by default; flips to `false` only when a step
     types a value that varies per run.

3. **Self-checks before handoff.**
   - Parses the file through `web-app/tests/agentic/runner/yaml-loader.ts`
     so unknown fixtures or typo'd primitives surface immediately.
   - Validates against `json-schemas/flow-test.json`.
   - Optionally runs the first one or two steps cold to confirm the flow
     reaches the target page.

4. **Tells you the exact command to run, what it'll cost, and where the
   artifacts land.** First run pays cold cost (~$0.05–$0.40); subsequent
   runs hit the action cache and cost ~$0.002 of judge LLM.

## Slash commands

The skill ships three commands:

| Command | What it does |
|---|---|
| `/test-feature <description>` | One-shot generation. Skips Q&A, takes a free-form description, writes the YAML, runs the self-check, reports back. |
| `/run-agentic-tests <pattern>` | Runs the runner with `HEADED=1 DEBUG=1` so you can watch. Detects whether your backend is in cloud mode (port 3000 with `auth_enabled: true`) or local mode and sets the right env defaults. |
| `/agentic-test-add-case <flow-file> <description>` | Extends an existing flow with a new case rather than authoring from scratch. Useful for adding regression cases to a flow that already covers a feature. |

## When to use it (and when not)

**Use this skill for:**

- Browser-driven UI tests of features in `oxy-hq/oxygen-internal`.
- Regression tests for UI bugs you just fixed.
- "Make sure feature X still works after this refactor" requests.

**Do NOT use this skill for:**

- Unit tests — Vitest in the web app, `cargo nextest` in the Rust crates.
- Oxy agent / workflow eval tests (`*.agent.test.yml` / `*.aw.test.yml`) —
  those go through the `oxy-test-drafter` skill.
- Backend Rust integration tests — those live next to the crate code.

## What you get

A new file at `web-app/tests/agentic/flows/<descriptive-kebab-name>.flow.test.yml`
that:

- Uses the right `target:` for the surface you're testing.
- Has a `setup:` block that lands the browser at the page where the test
  starts (without driving the cloud-mode prelude unless the test is
  *about* the prelude).
- Pairs each `act:` with a `wait_for:` so steps don't race.
- Uses explicit `[data-testid=…]` selectors when they exist (the skill greps
  `web-app/src/**/*.tsx` for testids before authoring).
- Substitutes any secret a step needs to type via `${VAR}` env references
  (when the loader supports it) — never hard-codes secrets.
- Ends with one `judge:` covering your stated success claim, plus
  zero-or-more `assert:` checks for any structural claims.

## Reference docs

- [`SKILL.md`](SKILL.md) — full instructions Claude follows when authoring.
- [`EXAMPLES.md`](EXAMPLES.md) — six worked examples covering distinct surfaces
  (chat panel, IDE, onboarding, builder dialog, apps page, regression test).
- [`CHEATSHEET.md`](CHEATSHEET.md) — for devs authoring flows by hand:
  schema reference, the action-cache contract, common LLM failure modes
  and fixes.

For the full runtime mechanics — what tools the LLM gets, how the action
cache invalidates, what the judge does — read
[`web-app/tests/agentic/README.md`](https://github.com/oxy-hq/oxygen-internal/blob/main/web-app/tests/agentic/README.md)
in `oxy-hq/oxygen-internal`. That file is the source of truth; this skill is
just the abstraction over it.
