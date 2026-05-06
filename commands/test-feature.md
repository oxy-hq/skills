---
name: test-feature
description: Generate an agentic browser test (.flow.test.yml) from a free-form description, skipping Q&A
activeForm: Generating agentic browser test from description
argument-hint: "<description of feature to test>"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# Generate an agentic browser test from a description

One-shot generator for `.flow.test.yml` files. Skips Q&A, takes the
description as `$ARGUMENTS`, infers the answers, writes the YAML, runs the
self-check, and reports back. Use when the description is unambiguous; for
vague requests, the `agentic-browser-test` skill prompts a short Q&A
instead.

This command must be run from the root of an `oxy-hq/oxygen-internal`
checkout.

## Steps

### 1. Sanity-check the working directory

```bash
test -f web-app/tests/agentic/README.md && test -f json-schemas/flow-test.json
```

If either path is missing, this is not an `oxy-hq/oxygen-internal` checkout
or the agentic-test layer hasn't landed on this branch yet. Tell the dev:
"This command must be run from the root of an oxy-hq/oxygen-internal
checkout where the agentic browser-test layer is present (see
`web-app/tests/agentic/README.md`)." Exit.

### 2. Re-read source of truth

Always re-read these — they evolve:

- `web-app/tests/agentic/README.md` — runner mechanics, primitives, the
  setup-fixture command list, the `wait_for:` enum, the `assert:` forms.
- `json-schemas/flow-test.json` — `target:` enum, settings keys, valid
  step shapes.
- The most recent flow file in `web-app/tests/agentic/flows/` — the
  team's current authoring taste.

If `internal-docs/agentic-browser-testing-followups.md` exists, read it for
recently-landed primitives (`${VAR}` substitution, sub-flow includes, new
fixtures).

### 3. Infer the answers

From `$ARGUMENTS`, infer:

| Field | How to infer |
|---|---|
| `target:` | Match the surface phrase to the schema's enum (chat / ide / threads / onboarding / any). When ambiguous, default to `any`. |
| Filename | Lower-kebab descriptive name. Don't shadow an existing flow filename. |
| `setup:` | If the dev mentions a file edit, include `reset_test_file`. Always include `goto:/<path>` to land on the page where the case starts. |
| `cache_actions:` | `true` unless the description mentions a real secret or per-run-varying value. |
| `max_steps:` | 15–25 for typical flows. Bump only if the flow has long pipelines. |
| Step text | Convert the dev's verbal user actions into one `act:` per logical action, each followed by a `wait_for:` that names the gate proving the action worked. **Bias hard toward explicit `[data-testid=…]` selectors** — grep `web-app/src/**/*.tsx` for the testids referenced by the dev's description before authoring. |
| `expect:` | One `judge:` for the dev's stated success criterion. Zero or more `assert:` for any structural claim the description names ("a SQL artifact appears", "the save button hides"). |

### 4. Grep for testids

Before writing any `act:` step that mentions a button/input/visible
component:

```bash
grep -nE 'data-testid="[^"]*"' web-app/src/**/*.tsx \
  | grep -i '<keyword from the dev's description>'
```

Use the matched testid verbatim in the `act:` text. If none exists for a
component the test needs, mention to the dev that adding one is a one-line
follow-up that drops cold cost ~5×.

### 5. Write the YAML

```bash
mkdir -p web-app/tests/agentic/flows
```

Write the file at `web-app/tests/agentic/flows/<name>.flow.test.yml`. Copy
the `# yaml-language-server: $schema=` header from an existing flow. Match
the existing flows' two-space indent and quoting style.

### 6. Self-check

Run both checks. Don't hand off broken YAML.

**Parse-check:**

```bash
cd web-app
ANTHROPIC_API_KEY=fake-test-key \
  npx tsx -e "import('./tests/agentic/runner/yaml-loader.ts').then(m => m.loadFlow('tests/agentic/flows/<name>.flow.test.yml')).then(f => console.log('parsed OK:', f.name)).catch(e => { console.error('PARSE FAIL:', e.message); process.exit(1) })"
```

**Schema-check** — use whichever validator the repo already wires up; if
none, fall back to `npx ajv-cli`:

```bash
# Convert the YAML to JSON for ajv (it doesn't read YAML directly).
npx --yes js-yaml web-app/tests/agentic/flows/<name>.flow.test.yml > /tmp/flow.json
npx --yes ajv-cli@latest validate -s json-schemas/flow-test.json -d /tmp/flow.json
```

If either fails, iterate on the YAML and re-run. Common fixes:

- Unknown `target:` value → check the schema's enum.
- Unknown `wait_for:` primitive → check the README.
- Unknown `setup:` command → check the README.
- Indentation off → match an existing flow byte-for-byte for the
  surrounding structure.

### 7. Report back

Show the dev:

1. The path to the new file.
2. The exact command to watch the first run:
   ```bash
   HEADED=1 pnpm test:agentic <flow-stem>
   ```
   (or `/run-agentic-tests <flow-stem>` for env auto-detection).
3. Cost expectation: cold ~$0.05–0.40, warm (after the first run)
   ~$0.002.
4. Where the artefacts land:
   - Markdown report: `web-app/tests/agentic/.results/<ts>.md`
   - JSON: `web-app/tests/agentic/.results/<ts>.json`
   - Trace on failure: `web-app/tests/agentic/.traces/<flow>-<case>.zip`
     (open with `pnpm exec playwright show-trace <path>`)

### 8. Offer a smoke run (optional)

If the dev wants to verify the flow at least reaches the target page
before paying full cold cost, offer:

```bash
HEADED=1 DEBUG=1 \
  pnpm test:agentic <flow-stem> --no-auto-backend --no-auto-frontend
```

Watching the first 1–2 steps is enough to catch typos in the setup or
the first selector.

## Error handling

- **The dev's description is too vague to author from.** Don't guess
  beyond what's stated. Stop and use `AskUserQuestion` for one targeted
  question (usually about the success criterion or the surface area).
- **A required testid doesn't exist on the page.** Tell the dev. Offer to
  author the flow against natural-language descriptions of the element
  (more expensive — 5–10× cold cost) AND to file a follow-up to add the
  testid.
- **The README documents a primitive this command doesn't know about.**
  Trust the README. The skill is designed to forward-adapt.

## Notes

- Never invent setup commands, `wait_for:` primitives, or `assert:` forms
  the README doesn't document. Unknowns are silently dropped or throw.
- Never put real secrets in the YAML. Use `${VAR}` substitution if the
  loader supports it AND set `cache_actions: false` on the flow.
- Don't overwrite an existing flow file. If the dev wants to add a case
  to an existing flow, route them to `/agentic-test-add-case`.
