# Cheatsheet — `.flow.test.yml` by hand

For devs who want to author a flow without invoking the skill, or who want
to read an existing flow and understand it. The
[`README.md`](https://github.com/oxy-hq/oxygen-internal/blob/main/web-app/tests/agentic/README.md)
in `oxy-hq/oxygen-internal` is the source of truth — re-read it whenever you
suspect this cheatsheet has drifted.

---

## File location & naming

```
web-app/tests/agentic/flows/<descriptive-kebab-name>.flow.test.yml
```

Lower-kebab. Describes what the flow tests, not the surface (good:
`chat-ask`, `ide-save`, `reset-button-clears-workspace`; bad: `chat-1`,
`test-2`).

Always include the `# yaml-language-server: $schema=` header pointing at
`json-schemas/flow-test.json` — IDE autocomplete and inline diagnostics
depend on it.

---

## Top-level shape

```yaml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json

name: <human-readable summary>     # required, free-form
target: <enum>                     # documentation hint, see schema for current enum
settings:
  runs: 1
  model: claude-sonnet-4-6
  judge_model: claude-haiku-4-5-20251001
  trace: on-failure                 # on-failure | always | never
  cache_actions: true
  max_steps: 30                     # upper bound on LLM tool-pick iterations per step
setup:                              # ordered fixture commands run before each case
  - <command>
cases:                              # at least one
  - name: <descriptive>
    tags: [<surface>, <classification>]
    steps:                          # ordered
      - act:      <text>
      - wait_for: <primitive>
    expect:                         # zero or more
      - assert: <claim>
      - judge:  <claim>
```

`target:` enum (verify in `json-schemas/flow-test.json` — it evolves):
`chat`, `ide`, `threads`, `onboarding`, `any`.

---

## `setup:` fixture commands

Documented in the README. Currently:

| Command | What it does |
|---|---|
| `reset_test_file` | Wipes `demo_project/test.sql` to a clean state for IDE save flows. |
| `goto:/path` | Navigate to `<OXY_BASE_URL><path>` before the case starts. |

If the README documents new fixtures (`seed_org`, `seed_blank_workspace`,
`seed_demo_workspace`, `seed_llm_key`, `goto_workspace`, …) — use them.
**Don't invent commands the README doesn't list.** Unknown commands are
silently ignored or throw, depending on the loader; either way the flow
won't do what you intend.

---

## `act:` — natural-language step

The LLM reads the page via `browser_snapshot` (a compact accessibility-tree
text under 12 kB) and chooses one of the generic browser tools to act.

**Effective `act:` prompts:**

- **Explicit selectors when stable:**
  `Click [data-testid=agent-selector-button]`. The model uses them verbatim
  and converges in 1–2 iterations. Grep `web-app/src/**/*.tsx` for testids
  before authoring; if a button you need doesn't have one, request a
  one-line testid addition before authoring the flow.

- **Numbered sub-steps for tightly-coupled actions:** stays atomic from the
  cache's perspective but the model plans ahead. See the existing flows
  for canonical phrasings.

- **Disambiguators for duplicate elements:**
  *"the file editor's Monaco surface — the top one, NOT the SQL results
  pane below"*.

- **State-change anchors:**
  *"After clicking, the URL should change to /ide/files/<base64>"*.
  Orients the model on what success looks like.

- **Tool hints when the right primitive is non-obvious:** for Monaco,
  `Use browser_keyboard_type (NOT browser_type — Monaco's hidden textarea
  makes selector-based fill unreliable)`.

**What to avoid:**

- Pure natural language without selectors when the page has duplicates.
  *"Click the default agent"* is ambiguous; the page has the word
  "default" in three places.
- "Verify X" steps that don't act on the page. Verifications belong
  under `expect:`, not `steps:`.
- `force: true` on `browser_snapshot`. The model can pass it but rarely
  should — the in-turn snapshot cache is automatically refreshed by
  state-changing tools.

---

## `wait_for:` — gate the next step

Built-in primitives (verify in the README — new ones may be added):

| Primitive | What it waits for |
|---|---|
| `streaming_complete` | The chat / builder SSE stream has ended. |
| `network_idle` | No in-flight requests for ~500 ms. |
| `selector:<sel>` | A Playwright-syntax selector becomes visible. |

**Where to put a `wait_for:`:** after every `act:` whose post-condition is
non-trivial. Without these gates the next `act:` runs before the page is
ready and either flakes or burns iterations as the model figures out the
page is mid-transition.

**Long waits.** If the README documents a `;timeout_ms=<n>` suffix on
`selector:` waits, use it for waits known to exceed 30 s (build phases,
long pipelines, agentic runs):

```yaml
- wait_for: "selector:[data-testid=build-finished];timeout_ms=120000"
```

If the README does not document this suffix, **don't write it** — it won't
parse.

---

## `expect:` — assert vs judge

Two kinds:

### `assert:` (free, deterministic)

Documented forms (verify in the README — `runner/judge.ts` is the
authoritative implementation):

```yaml
- assert: "selector <sel> is visible"
- assert: "selector <sel> is not visible"
- assert: "selector <sel> has attribute <attr>=<value>"
- assert: "text \"<exact text>\" is visible"
- assert: "save button is not visible"        # IDE-specific helper, waits up to 5 s
```

**Use asserts for every structural claim.** They cost $0 and run
deterministically.

### `judge:` (~$0.002 each, semantic)

LLM-as-judge against the current screenshot + DOM text. Use for soft
semantic claims that aren't reducible to a structural check:

```yaml
- judge: "the response includes a coherent answer about weekly sales per store, not an error message"
- judge: "the editor content includes the line '-- agentic test edit'"
- judge: "the chart contains plotted data points (axes, lines, or bars are visible) and is not an error placeholder"
```

**Rules of thumb:**

- One `judge:` per case (the dev's stated success criterion in plain
  English).
- Never `judge:` something you can `assert:` instead.
- Don't write judge claims that reference internal field/schema names —
  the judge sees what a user sees.

---

## Action cache contract

Every successful `act:` step records the sequence of state-changing tool
calls (`browser_click`, `browser_type`, `browser_press_key`,
`browser_keyboard_type`, `browser_navigate`) into
`tests/agentic/.cache/bespoke-actions.json`. On a warm run the recorded
sequence replays directly against Playwright with **no LLM call** — per-case
cost floors at the judge call (~$0.002).

**Cache key:** `sha256(flow_file | case_name | step_index | step_text)`.

Two consequences worth understanding:

1. **Editing a step's text invalidates only that step's cache entry.**
   Adjacent steps in the same case still warm-replay.
2. **Verbatim step text in two different flows shares the cache entry.**
   If two flows have an identical `act:` (byte-for-byte), only one of them
   needs to derive it. **This is the only way you get cross-flow reuse**,
   so prefer copying canonical step text over paraphrasing.

**Invalidation.** If a recorded selector no longer matches the page, the
entry throws on replay, the runtime invalidates it, and re-derives from
scratch. There's no partial-replay path — invalidation is drop-and-redrive.

**`cache_actions: false`.** Disables caching for the whole flow. Flip to
`false` when:

- A step types a real secret. Cached replay is deterministic — the recorded
  value is replayed verbatim. Even if you use `${VAR}` substitution, the
  expanded value lands in the cache JSON. **For real secrets, use env
  substitution AND `cache_actions: false`.**
- A step types a per-run-varying value (timestamps, generated IDs). Without
  caching off, the second run will replay the first run's stale value.

**Don't use `cache_actions: false` to "make a flaky flow stable".** Flaky
warm-replay is a runtime bug — file it against the runner, don't paper
over it.

---

## `${VAR}` substitution

If the YAML loader supports it (check `web-app/tests/agentic/runner/yaml-loader.ts`
or the README), `${ENV_VAR_NAME}` in any string field is expanded from
`process.env` at load time. Missing variables throw — this is the right
behaviour for secrets, since you don't want a fake value to leak into the
cache.

```yaml
- act: "Type ${ANTHROPIC_API_KEY} into the LLM key input."
```

If the loader does *not* yet support substitution, route the secret some
other way (a `setup:` fixture, an env var the runner reads outside YAML)
and don't put it in the YAML at all.

---

## Common LLM failure modes & fixes

From the README (re-read it for the current canonical list):

| Symptom | Fix |
|---|---|
| Step burns 30 s on a `browser_click` | Wrong selector — the model is waiting on Playwright's old default. The runtime now uses 5 s; if you still see 30 s you're on an outdated branch. |
| Step takes 12+ iterations | Vague `act:` prompt. Add explicit selectors or numbered sub-steps. |
| `assert: "selector ... is visible"` flakes | The page renders the element late. Insert a `wait_for: selector:<sel>` step before the assertion, or use `judge:` (which captures a fresh screenshot at evaluation time). |
| Save button assertion races (IDE flow) | Use `assert: "save button is not visible"` — that helper does a 5 s waitFor rather than an immediate check. |
| Monaco appears empty after typing | Use `browser_keyboard_type`, not `browser_type`. Click `.monaco-editor` first to focus. |
| `model: claude-sonnet-4-7` returns 404 | Not yet GA on the account. Use `claude-sonnet-4-6` until 4-7 ships. |
| Step succeeds locally, fails in CI | The action cache replayed a stale selector. Either bump `CACHE_VERSION` in the runner, or change the step text by one character to force re-derivation. |

---

## Cost reference

| Scenario | Per-case cost |
|---|---|
| Cold (cache miss, well-anchored prompt) | ~$0.05–0.15 |
| Cold (cache miss, vague prompt) | ~$0.20–0.40 |
| Warm (cache hit, full flow) | ~$0.002–0.005 (judge only) |

Per-step cost lands in the markdown report at
`tests/agentic/.results/<ts>.md` and the JSON next to it. Trust those
numbers — they apply Anthropic's published rates from `runner/pricing.ts`.

---

## Running

From `web-app/`:

```bash
pnpm test:agentic                                # all flows
pnpm test:agentic <pattern>                      # filename match
pnpm test:agentic --tag <tag>                    # tag filter
pnpm test:agentic --output results.json          # write JSON
HEADED=1 pnpm test:agentic <pattern>             # see browser
DEBUG=1 pnpm test:agentic <pattern>              # stream agent reasoning
pnpm test:agentic --no-auto-backend              # don't auto-spawn `oxy start`
pnpm test:agentic --no-auto-frontend             # don't auto-spawn `pnpm dev`
```

Use `/run-agentic-tests <pattern>` to run with `HEADED=1 DEBUG=1` and the
right env vars for your detected backend mode (cloud vs local).

## Output artefacts

- `tests/agentic/.results/<ts>.md` — markdown summary (per-case pass/fail,
  per-step debug table, cost). Auto-appended to `$GITHUB_STEP_SUMMARY` in
  CI.
- `tests/agentic/.results/<ts>.json` — same data programmatically.
  Schema: `runner/types.ts:RunResults`.
- `tests/agentic/.traces/<flow>-<case>.zip` — Playwright trace on
  failure. Open with `pnpm exec playwright show-trace <path>`.
- `tests/agentic/.cache/bespoke-actions.json` — the action cache. Delete to
  force a full re-derive next run.

---

## When to *not* use this layer

- Behaviour that has no UI footprint — write a unit test (Vitest in
  `web-app`, `cargo nextest` in the Rust crates).
- Oxy agent / workflow output correctness — use the `oxy-test-drafter`
  skill and `*.agent.test.yml` / `*.aw.test.yml`.
- Backend HTTP contract — Hurl smoke tests at `tests/smoke/smoke.hurl`,
  or Rust integration tests next to the crate code.
