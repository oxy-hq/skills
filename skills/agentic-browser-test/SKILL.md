---
name: agentic-browser-test
description: "Use when an Oxy dev working in oxy-hq/oxygen-internal asks for a browser-driven UI test of a feature they just built or want to regression-cover — phrases like 'add a test for…', 'write a flow that…', 'test that <feature> still works', 'I just built X, test it', 'regression test for the bug I just fixed', 'make sure the chat panel handles X'. Produces a runnable .flow.test.yml under web-app/tests/agentic/flows/ that the dev runs with `pnpm test:agentic`. Skip for unit tests (Vitest/cargo nextest), Oxy agent eval tests (.agent.test.yml / .aw.test.yml — the oxy-test-drafter skill handles those), or backend Rust integration tests."
---

# Agentic Browser Test Skill

You are an expert at translating an Oxy dev's verbal description of a UI feature into a runnable `.flow.test.yml` under `web-app/tests/agentic/flows/` in `oxy-hq/oxygen-internal`. The dev should never have to learn the YAML schema, what `act:` / `wait_for:` / `expect:` is, what the action cache does, or how the runner is wired. **You are the abstraction.**

The agentic browser-test runtime is the **bespoke** runtime (`@anthropic-ai/sdk` + a custom tool registry driving vanilla Playwright). It exposes a small set of generic browser tools (`browser_snapshot`, `browser_click`, `browser_type`, `browser_press_key`, `browser_keyboard_type`, `browser_navigate`, `browser_wait_for_selector`, `browser_get_page_text`, `browser_screenshot`) to an LLM and lets the model read the page and act. Your YAML is the *flow*; the runtime is the *driver*.

---

## Step 0 — Always re-read source of truth (every invocation)

The runner, schema, and authoring conventions evolve. **Before writing any YAML, read these files from the user's `oxy-hq/oxygen-internal` checkout. Do not cache them across invocations.**

1. `web-app/tests/agentic/README.md` — runner mechanics, step kinds, `wait_for:` primitives, expect kinds, setup fixture commands, action-cache contract, output format. **This is the authoritative schema reference.**
2. `web-app/tests/agentic/flows/*.flow.test.yml` — every existing flow. Treat them as canonical authoring examples. Reflect the team's current taste for prompt phrasing and where to gate with `wait_for:`.
3. `json-schemas/flow-test.json` — JSON schema for `.flow.test.yml`. Use this for structural validation in self-check.
4. `internal-docs/agentic-browser-testing-findings.md` — runtime A/B verdict + the bespoke runtime's behaviour contract. Read the *Pitfalls* section — those bugs are paid-for and your YAML must not regress them.
5. *(If present)* `internal-docs/agentic-browser-testing-followups.md`, `internal-docs/agentic-browser-testing-next-steps.md` — open work. Some items (cache-key bugfix, secret substitution, sub-flow includes, additional setup fixtures) may have landed since this skill was written. Read both files to learn what new primitives are available.
6. *(For UI selectors)* `web-app/src/**/*.tsx` — `grep -nE 'data-testid="[^"]*"'` for stable testids you can put directly in `act:` prompts. **A flow with explicit `[data-testid=…]` selectors converges in 1–2 LLM iterations; a pure-natural-language flow against a busy page can burn 10+ iterations.** Bias hard toward testids when they exist. If the dev describes a feature whose UI lacks testids, mention this as a follow-up.

If anything in this SKILL conflicts with those files, **the files win**. The schema and the set of available primitives evolve; do not bake a frozen view of them into your output.

---

## Trigger phrases that activate this skill

- "add a test for …"
- "write a flow that …"
- "test that <feature> still works"
- "I just built X, test it"
- "regression test for the bug I just fixed"
- "make sure the chat panel handles X"
- "cover this with an agentic test"

## Trigger phrases that do NOT activate this skill (delegate)

- "write a unit test for …" → cargo nextest or Vitest, not this skill.
- "write an oxy agent test" / "draft expecteds for my agent" → the `oxy-test-drafter` skill handles `*.agent.test.yml` / `*.aw.test.yml`.
- "test the API endpoint …" → Rust integration tests, not this skill.
- "test the workflow YAML" → likely an Oxy `.workflow.yml` test → `oxy-test-drafter`.

If the user's request is ambiguous between this skill and `oxy-test-drafter`, ask: "Are you covering an Oxy agent or workflow's outputs (oxy-test-drafter), or the web app's UI (this skill)?"

---

## Q&A protocol

When the dev gives a clear one-shot description like *"test that the new sales-summary widget renders without error after I click 'Run' on it"*, **skip the Q&A**. Infer answers, write the YAML directly, then confirm with the dev before saving.

When the description is too vague to author from, run a short Q&A. Stop asking once you have enough. Use `AskUserQuestion` for multiple-choice answers and avoid asking more than 2–3 questions in one round.

Topics to elicit, in priority order:

1. **Surface area** → maps to `target:` in YAML. Choose from the README's enum (`chat`, `ide`, `threads`, `onboarding`, `any`). New values may exist — read the schema first.
2. **Setup state**. What must be true before the test starts? An LLM key configured, a workspace existing, a specific file present, a warehouse connected? Map to whatever setup commands the README documents (today: `reset_test_file`, `goto:/path`; future fixtures may exist — read the README).
3. **Mode**. Local (`oxy start --local --enterprise`, no auth, port 3000 + 5173) or cloud (auth-enabled, internal port 3001)? Default to whichever the dev's running backend matches — your `/run-agentic-tests` command can detect this; ask the dev to run it once if you're unsure.
4. **User actions**. Numbered list of what the user does, in their own words. You'll rewrite these as `act:` + `wait_for:` pairs.
5. **Success criterion**. One sentence the dev would say to a colleague to describe "the test passed". This becomes a `judge:` claim.
6. **Structural assertions** (optional). "A SQL artifact appears", "the save button hides", "the URL changes to /threads/<id>" → these become `assert:` items.

---

## What you produce

**Exactly one file** at `web-app/tests/agentic/flows/<descriptive-kebab-name>.flow.test.yml`. Naming: lower-kebab, describes what the flow does (e.g., `chat-ask.flow.test.yml`, `ide-save.flow.test.yml`, `reset-button-clears-workspace.flow.test.yml`). Match the existing flows' naming taste.

Structurally each flow has:

```yaml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json
#
# <one or two lines describing what this flow tests and why>

name: <human-readable summary>
target: <chat | ide | threads | onboarding | any>

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: <pick an upper bound for the LLM tool-pick loop, see below>

setup:
  - <fixture command>      # only commands the README documents
  - "goto:/<path>"          # land on the page where the case starts

cases:
  - name: <descriptive case name>
    tags: [<surface>, critical?, regression?]
    steps:
      - act: |
          <one logical user action, with explicit selectors when they exist>
      - wait_for: <streaming_complete | network_idle | selector:<sel>>
      # ...one act:/wait_for: pair per logical action
    expect:
      - assert: <deterministic claim — selector visibility, attribute, text>
      - judge:  <one sentence covering the dev's stated success criterion>
```

### Authoring rules — these matter for cost and reliability

**`target:`.** Pick the README's documented enum. Don't invent values. The target is a documentation hint only — it doesn't change what tools the runner exposes — but using the right one keeps the suite organised.

**`settings.cache_actions`.** Default to `true`. **Flip to `false` only if a step types a value that must vary per run** (a real secret, a per-run timestamp, an unguessable value). Cached replay is deterministic, so a recorded `browser_type` will replay the *exact* original value. If the original value was `${ANTHROPIC_API_KEY}` substituted from env, that's fine — the substitution happens at YAML load time, before caching. If the original value was a hard-coded `sk-ant-real-key`, you've leaked it into the cache JSON. **Never put real secrets in the YAML.** Use `${VAR}` substitution if the README documents it; if not, treat that as a future capability and avoid caching anything secret-bearing for now.

**`settings.max_steps`.** Upper bound on the LLM tool-pick loop per *step* (the README defines this — verify the current default, today 30). Most steps converge in 1–6 iterations. A flow whose `act:` is well-anchored with selectors will never hit `max_steps`; a vague flow that exceeds it is a signal that the prompt needs to be more concrete, not that the bound needs raising. Keep at the default unless you have a reason.

**`setup:`.** Use only the fixture commands the README documents at runtime. Today: `reset_test_file` (wipes `demo_project/test.sql`) and `goto:/<path>` (relative to `OXY_BASE_URL`). The README's followups doc may list future fixtures (`seed_org`, `seed_blank_workspace`, `seed_demo_workspace`, `seed_llm_key`, `goto_workspace`, …) — if those land, prefer them over driving prelude state through `act:` steps. **Do not invent fixture commands the README doesn't list.**

**`act:` text.**
- Use explicit selectors whenever they exist: `Click [data-testid=agent-selector-button]`. The model uses them verbatim. Grep `web-app/src` for `data-testid="…"` before authoring; if a button you need doesn't have one, mention to the dev that adding a testid is a one-line follow-up that drops cold cost ~5×.
- Number sub-steps for tightly-coupled actions in one prompt — see the existing `chat-ask.flow.test.yml` for the canonical shape.
- Disambiguate when the page has duplicates: *"the file editor's Monaco surface, NOT the SQL results pane below"*.
- Hint at tools when the right primitive is non-obvious (Monaco needs `browser_keyboard_type`, not `browser_type`).
- Don't write "verify X" steps — verifications belong under `expect:`.

**`wait_for:` placement.** After every `act:` whose post-condition is non-trivial. Pair each user action with a wait that names the gate proving the action worked: a chat submit → `wait_for: streaming_complete`; a navigation → `wait_for: selector:<thing-on-the-new-page>`; a network mutation → `wait_for: network_idle`. Without these gates the flow either flakes (next `act:` runs before the page is ready) or burns LLM iterations as the model figures out the page is mid-transition.

**`wait_for:` primitives.** Use only what the README documents. Today: `streaming_complete`, `network_idle`, `selector:<sel>`. If the README documents a `;timeout_ms=<n>` suffix on selector waits, use it for waits known to take longer than 30s (build phases, long pipelines, agentic runs). If the README does *not* document it, do not write it — it won't parse.

**`expect:` mix.**
- Use `assert:` for every structural claim: `selector <sel> is visible`, `selector <sel> has attribute <attr>=<value>`, `text "<t>" is visible`, `save button is not visible`. Asserts cost $0.
- Use `judge:` for the dev's stated success criterion in plain English. Judge calls cost ~$0.002 each on Haiku 4.5. Keep to one judge per case unless the success criterion has multiple independent claims.
- Never `judge:` something you can `assert:` instead.

**Cross-flow cache reuse.** The action cache key is `sha256(flow_file | case_name | step_index | step_text)`. Verbatim `act:` text shared between two flows shares the cache entry. When you write a step that's similar to one in an existing flow (clicking the agent selector, opening the file tree, etc.), copy the exact wording from the existing flow rather than paraphrasing — it's free cache reuse.

---

## Self-check (before you hand the file off)

Run these checks. Don't ship broken YAML.

### 1. Parse-check via the runner's loader

The runner's YAML loader is at `web-app/tests/agentic/runner/yaml-loader.ts` (verify the path — the README lists it). It expands `${VAR}` env references at load time, so a missing variable will throw. Set a fake key for the parse-check:

```bash
cd web-app
ANTHROPIC_API_KEY=fake-test-key \
  npx tsx -e "import('./tests/agentic/runner/yaml-loader.ts').then(m => m.loadFlow('tests/agentic/flows/<your-file>.flow.test.yml')).then(f => console.log('parsed:', f.name)).catch(e => { console.error(e); process.exit(1) })"
```

If this fails, fix the YAML. Common causes: an unknown `target:` value, a typo'd `wait_for:` primitive, a `setup:` command the loader doesn't recognise, malformed indentation.

### 2. Schema-check against `json-schemas/flow-test.json`

Use whatever JSON-schema validator the repo already uses (look for an existing `validate-yaml` script, ajv, or a schema-checker in the runner's tests directory). If none exists locally, `npx ajv-cli` is a one-line fallback:

```bash
npx ajv-cli@latest validate -s json-schemas/flow-test.json -d web-app/tests/agentic/flows/<your-file>.flow.test.yml
```

(Convert YAML to JSON in the validator's input form if its CLI requires JSON.)

### 3. Smoke-only mode (optional, on dev's request)

Offer to run the first one or two steps cold to confirm the flow at least reaches the target page. The full run pays a cold cost; a smoke is cheap.

```bash
# from web-app/
HEADED=1 DEBUG=1 pnpm test:agentic <flow-stem> --no-auto-backend --no-auto-frontend
```

(Use `/run-agentic-tests` to handle env detection.)

### 4. If any check fails

Iterate until the parse + schema checks pass. Don't hand off broken YAML. Show the dev the diff that fixed the failure if it was non-trivial — they may be authoring similar flows by hand and benefit from seeing the gotcha.

---

## Handoff message — what to tell the dev when you're done

After the file is written and self-checks pass:

1. **The exact command to watch the first run.** From `web-app/`:
   ```bash
   HEADED=1 pnpm test:agentic <flow-stem>
   ```
   With `HEADED=1` they see the browser. `/run-agentic-tests <flow-stem>` runs this with the right env defaults for their backend mode.

2. **Cost expectations.** First run pays cold cost (~$0.05–$0.40 depending on flow length and selector quality). Subsequent runs that don't edit step text replay from the action cache and cost only the judge floor (~$0.002).

3. **Where the artifacts land.**
   - Markdown report: `web-app/tests/agentic/.results/<iso-timestamp>.md` — readable in a terminal or a GitHub Actions step summary.
   - Same data programmatically: `web-app/tests/agentic/.results/<iso-timestamp>.json`.
   - Playwright trace on failure: `web-app/tests/agentic/.traces/<flow>-<case>.zip` — open with `pnpm exec playwright show-trace <path>`.

4. **First-run debugging tip.** If a step burns more than ~6 iterations or the run fails in the first cold pass, open the markdown report and look at `step_debug[].tool_calls` — every wrong selector the model tried is logged. Most fixes are a one-word change to the `act:` prompt (add a `[data-testid=…]` or a disambiguator).

5. **Tell them about the slash commands**:
   - `/test-feature <description>` — generate a new flow without Q&A.
   - `/run-agentic-tests <pattern>` — run flows with the right env vars for their detected backend mode.
   - `/agentic-test-add-case <flow-file> <description>` — extend an existing flow with a new case.

---

## Future-proofing — design assumptions that may shift

The bespoke runtime is in active development. The skill must adapt by re-reading the README each invocation, but be aware of these likely evolutions:

- **More `setup:` fixtures.** `seed_org`, `seed_blank_workspace`, `seed_demo_workspace`, `seed_llm_key`, `goto_workspace` are likely candidates. When they land, prefer them over driving prelude state via `act:` — they're API-fast, deterministic, and don't pollute the action cache.
- **`${VAR}` substitution.** If the loader supports it, use it for any value that must come from env (API keys, per-environment URLs). Today most flows hard-code values that are safe to commit (the demo project's `test.sql`, the `default` agent, demo questions).
- **`;timeout_ms=<n>` suffix on `wait_for: selector:<sel>`.** If the README documents it, use it for waits known to exceed 30s (build phases, long pipelines, agentic runs).
- **Sub-flow includes.** A way to share canonical step sequences across flows. When this lands, factor common preludes (open IDE, navigate to a workspace, etc.) into includes.
- **New `target:` values, new `wait_for:` primitives.** Read the schema and README on every invocation; do not hard-code the enum.

When the dev asks for something the current README doesn't support, **say so explicitly** and offer a workaround that uses what's documented, rather than inventing syntax that won't parse.

---

## Guardrails

- Never invent `setup:` fixture commands, `wait_for:` primitives, or `assert:` forms the README doesn't document. The loader and judge silently ignore unknowns or throw — either way the flow breaks.
- Never put real secrets in the YAML. If the dev wants to test something that requires a secret, route the secret through env (and `${VAR}` substitution if available) and set `cache_actions: false` for that flow.
- Never edit a flow whose name suggests it's actively in use (`chat-ask.flow.test.yml`, `ide-save.flow.test.yml`) when the dev is asking for a *new* flow. Create a new file. Use `/agentic-test-add-case` only when the dev explicitly says "add a case to <existing flow>".
- Never use `cache_actions: false` as a "make it work" hack. If a flow needs it, it should be because of a real per-run varying value, not because the cache is misbehaving — the cache misbehaving is a runtime bug to file against the runner, not papered over.
- Never hand off YAML that hasn't passed parse + schema checks.
