# Worked Examples

Six end-to-end examples covering distinct surfaces. Each example shows the
dev's request, the inferred answers, and the resulting YAML file. Use these
as templates — the existing flows in
`web-app/tests/agentic/flows/` are the *canonical* examples (read those
first); the ones below extend the pattern to surfaces that don't yet have
landed flows.

> **Reminder.** Re-read the README and an existing flow before you author.
> Some primitives below (`${VAR}`, `;timeout_ms=`, `seed_*` fixtures) may not
> exist yet at the time you read this. Check the README; if they're not
> there, fall back to the workarounds noted in each example.

---

## 1. Chat panel question + SQL artifact verification

**Dev says:** *"test that asking the default agent a sales question on the
home page returns a SQL artifact"*

**Inferred:**
- Surface: `chat`.
- Setup: `goto:/`. No state needed beyond the demo project.
- Mode: local.
- Actions: open agent selector → pick `default` → type question → submit.
- Success: a SQL artifact renders.
- Structural claims: artifact selector visible; artifact has
  `data-artifact-kind=execute_sql`.

```yaml
# web-app/tests/agentic/flows/chat-ask.flow.test.yml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json
#
# Ask a sales question on the Home page using the demo project's `default`
# agent (Oxymart sales analyst) and verify that a SQL artifact is rendered.

name: chat ask returns SQL artifact
target: chat

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: 15

setup:
  - "goto:/"

cases:
  - name: ask a question and get a SQL artifact
    tags: [chat, critical]
    steps:
      - act: |
          Submit a question to the 'default' agent on the home page chat panel:
          1. Click the agent selector button (it shows the currently-selected
             agent's name like 'analytics', 'default', or 'app_builder' — NOT
             the 'Ask' mode toggle). The selector is
             [data-testid=agent-selector-button].
          2. From the dropdown, click the menu item labeled 'default'.
          3. Type 'What were the total weekly sales by store?' into the
             textarea (selector: textarea[name=question]).
          4. Click the submit button [data-testid=chat-panel-submit-button].
          Do not end the turn until the URL changes to /threads/<id>.
      - wait_for: streaming_complete
    expect:
      - assert: "selector [data-testid=agent-artifact] is visible"
      - assert: "selector [data-testid=agent-artifact] has attribute data-artifact-kind=execute_sql"
      - judge: "the response includes a coherent answer about weekly sales per store, not an error message"
```

**Why this shape works:**
- One compound `act:` for the four tightly-coupled actions — fewer step
  boundaries means smaller cumulative LLM context. (For comparison, the
  README documents that `ide-save` was measured cheaper as four atomic
  steps; chat-ask is at the size where it doesn't matter.)
- The `act:` ends with a state-change anchor (*"Do not end the turn until
  the URL changes to /threads/<id>"*) so the model knows when the action
  has actually landed.
- One `judge:` for the soft semantic claim, two `assert:` for the
  structural claims (free).

---

## 2. IDE file edit + save (Monaco quirk)

**Dev says:** *"test that editing test.sql in the IDE and pressing Cmd+S
saves the file"*

**Inferred:**
- Surface: `ide`.
- Setup: `reset_test_file` (the README's documented fixture for wiping
  `demo_project/test.sql` to a clean state) + `goto:/ide`.
- Actions: open `test.sql` from the file tree → focus Monaco → append a
  line → Cmd+S → wait for save button to hide.
- Success: editor content includes the new line; save button is hidden.

```yaml
# web-app/tests/agentic/flows/ide-save.flow.test.yml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json
#
# Open test.sql from the demo project in the IDE, append a comment, save, and
# verify the save button hides. `reset_test_file` wipes test.sql to a clean
# state so reruns start consistently.

name: IDE open, edit, and save
target: ide

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: 20

setup:
  - reset_test_file
  - "goto:/ide"

cases:
  - name: open test.sql, append a comment, save
    tags: [ide, critical]
    steps:
      - act: "In the IDE, open the file named 'test.sql' from the file tree on the left (it's at the project root). After clicking it, the URL should change to /ide/files/<base64> and the Monaco editor should display the file content."
      - act: |
          Append the line '-- agentic test edit' to the end of the open Monaco editor:
          1. Click the file editor's Monaco surface to focus it. The page has
             TWO Monaco editors (file editor on top, SQL IDE results panel
             below) — use the file editor. A reliable selector is
             `.monaco-editor`.first(). Use browser_click with selector
             ".monaco-editor".
          2. Press 'Meta+End' to jump to the end of the file.
          3. Press 'Enter' to start a new line.
          4. Use browser_keyboard_type with text='-- agentic test edit' (NOT
             browser_type — Monaco's hidden textarea makes selector-based
             focus unreliable; type via the keyboard into whatever is
             focused).
      - act: "Save the file by pressing 'Meta+s'. Wait for the save button [data-testid=ide-save-button] to disappear."
    expect:
      - assert: "save button is not visible"
      - judge: "the editor content includes the line '-- agentic test edit'"
```

**Why this shape works:**
- Atomic steps — four steps, four cache entries. If the dev later changes
  one (e.g. swaps the appended line text), only that step's cache entry
  invalidates; the rest still warm-replay.
- The Monaco quirk is encoded in-line: the model is told to use
  `browser_keyboard_type` rather than `browser_type`. This sidesteps the
  paid-for bug where Monaco's `aria-hidden` textarea makes a selector-based
  fill silently no-op.
- The `assert: "save button is not visible"` form is documented in the
  README — the judge waits up to 5 s for the IDE save button to hide
  (Meta+s → React state flush is async).

---

## 3. Onboarding wizard step verification

**Dev says:** *"test that completing the 'connect a warehouse' step of
onboarding takes you to the next step"*

**Inferred:**
- Surface: `onboarding`.
- Setup: depends on what the README documents. **Today** the only
  documented setup commands are `reset_test_file` and `goto:/path`. **In
  the future** (per `internal-docs/agentic-browser-testing-followups.md`),
  fixture commands like `seed_org` and `seed_blank_workspace` may exist —
  prefer those over driving the prelude through `act:` steps if available.
- Mode: cloud (onboarding only runs when auth is enabled).
- Actions: from a freshly-created blank workspace, click 'Connect a
  warehouse' → pick 'DuckDB' → submit → verify next step shows.
- Success: the wizard advances.

**Today's authoring (no API fixtures):**

```yaml
# web-app/tests/agentic/flows/onboarding-warehouse-step.flow.test.yml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json
#
# Drive the warehouse-connection step of onboarding. Today the prelude is
# walked through the UI; once seed_blank_workspace lands per the followups
# doc, replace the cloud-mode prelude steps with that fixture.

name: onboarding warehouse step advances
target: onboarding

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: 25

setup:
  - "goto:/onboarding"

cases:
  - name: pick DuckDB, submit, advance to next step
    tags: [onboarding, critical]
    steps:
      - act: "On the onboarding 'Connect a warehouse' step, click the DuckDB option. The selector is [data-testid=onboarding-warehouse-duckdb]."
      - wait_for: "selector:[data-testid=onboarding-warehouse-form]"
      - act: "In the DuckDB form, leave the default DB path. Click [data-testid=onboarding-submit-button]."
      - wait_for: "selector:[data-testid=onboarding-step-llm-key]"
    expect:
      - assert: "selector [data-testid=onboarding-step-llm-key] is visible"
      - judge: "the onboarding wizard has advanced past the warehouse step and is now showing the LLM-key step"
```

**Future authoring (when `seed_*` fixtures land — check the README):**

```yaml
setup:
  - seed_blank_workspace        # creates the workspace, drops to the warehouse step
  - "goto_workspace"            # equivalent to goto:/onboarding for the seeded workspace
```

---

## 4. Cmd+I builder dialog

**Dev says:** *"test that Cmd+I opens the agent builder dialog and submitting
a prompt drafts a new agent file"*

**Inferred:**
- Surface: `ide` (the builder lives inside the IDE).
- Setup: `goto:/ide`. Optionally `reset_test_file` if the test creates
  artefacts that need cleanup between runs.
- Actions: press Cmd+I → type prompt → submit → wait for the draft to
  appear in the file tree.
- Success: the dialog opened, accepted the prompt, and a new agent file is
  visible in the tree.

```yaml
# web-app/tests/agentic/flows/builder-edits-app.flow.test.yml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json

name: Cmd+I builder drafts a new agent file
target: ide

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: 25

setup:
  - "goto:/ide"

cases:
  - name: open builder, submit prompt, see new agent in tree
    tags: [ide, builder]
    steps:
      - act: "Press 'Meta+i' to open the agent builder dialog. Wait until the dialog [data-testid=agent-builder-dialog] is visible."
      - wait_for: "selector:[data-testid=agent-builder-dialog]"
      - act: |
          In the agent builder dialog:
          1. Click the textarea inside [data-testid=agent-builder-dialog] (selector: [data-testid=agent-builder-dialog] textarea).
          2. Type 'create a sales analyst agent for the Oxymart demo project'.
          3. Click [data-testid=agent-builder-submit-button].
      - wait_for: streaming_complete
    expect:
      - assert: "selector [data-testid=agent-builder-dialog] is not visible"
      - judge: "a new .agent.yml file has appeared in the IDE file tree on the left"
```

**Why `streaming_complete` here:** the builder uses the same SSE channel as
chat for the LLM-driven generation. The README documents
`streaming_complete` as the wait that gates on the streaming finishing —
reuse it.

---

## 5. Apps page rendering after a workflow run

**Dev says:** *"test that running a workflow from an app definition renders
the resulting chart"*

**Inferred:**
- Surface: `any` (apps live on their own route — pick `any` if no app-specific
  target exists).
- Setup: `goto:/apps/<app-id>` for an app that exists in the demo project. If
  the README documents an `seed_demo_workspace` fixture, prefer it; today
  rely on the demo project's pre-seeded apps.
- Actions: click 'Run' on the app → wait for completion → verify the chart
  renders.
- Success: a chart container is visible and contains an svg.

```yaml
# web-app/tests/agentic/flows/apps-renders-chart.flow.test.yml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json
#
# After clicking Run on a demo-project app, verify that the chart task
# renders an svg-based chart.

name: app run renders chart task
target: any

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: 20

setup:
  - "goto:/apps/sales-summary"

cases:
  - name: run app, see chart render
    tags: [apps, critical]
    steps:
      - act: "On the Apps page, click [data-testid=app-run-button] to execute the app's tasks."
      - wait_for: "selector:[data-testid=app-task-chart] svg"
    expect:
      - assert: "selector [data-testid=app-task-chart] svg is visible"
      - judge: "the chart contains plotted data points (axes, lines, or bars are visible) and is not an error placeholder"
```

**Why `wait_for: selector:<sel> svg`:** the chart container exists from the
moment the app loads; what we actually want to gate on is the *svg* being
inside it, which only happens after the task completes. A selector wait
that targets the inner element gives the right semantics.

---

## 6. Regression test pattern (small, focused, one judge claim)

**Dev says:** *"add a regression test for the bug I just fixed where pressing
Enter inside the chat textarea while a response was streaming submitted
the next message instead of being a no-op"*

**Inferred:**
- Surface: `chat`.
- Setup: `goto:/`.
- Actions: submit a question (any question that streams) → during streaming
  press Enter → verify the second submission did NOT happen.
- Success: only one user message appears in the thread.

```yaml
# web-app/tests/agentic/flows/chat-enter-during-stream.flow.test.yml
# yaml-language-server: $schema=../../../../json-schemas/flow-test.json
#
# Regression: pressing Enter in the chat textarea while a response is
# streaming used to submit a second message. After the fix, Enter during
# streaming is a no-op until the stream completes.

name: regression — enter during stream is a no-op
target: chat

settings:
  runs: 1
  trace: on-failure
  cache_actions: true
  max_steps: 12

setup:
  - "goto:/"

cases:
  - name: enter during stream does not submit a second message
    tags: [chat, regression]
    steps:
      - act: |
          Submit a question on the home page chat panel:
          1. Click [data-testid=agent-selector-button], then click 'default'.
          2. Type 'list the top 5 stores by revenue' into textarea[name=question].
          3. Click [data-testid=chat-panel-submit-button].
      - wait_for: "selector:[data-testid=agent-message-container]"
      - act: "While the response is still streaming (the [data-testid=message-input-stop-button] is visible), focus textarea[name=question] and press 'Enter'. Do not type anything before pressing Enter."
      - wait_for: streaming_complete
    expect:
      - assert: "selector [data-testid=user-message-container] is visible"
      - judge: "the thread shows exactly ONE user message (the original question), not two — the Enter press during streaming did not submit a second message"
```

**Why this pattern works for regressions:**
- Tight scope: one bug → one case. Don't bundle unrelated regressions into
  one flow; they share a cache entry.
- The `wait_for: selector:[data-testid=agent-message-container]` gates the
  second `act:` on streaming actually being in progress — without it, the
  Enter press could land before streaming starts and not exercise the bug.
- The `judge:` claim names the *specific behaviour* the bug had and the
  fixed behaviour ("exactly ONE user message, not two") so a future
  reader can recognise the regression at a glance.

---

## Patterns to copy across flows (cache reuse)

The action cache key is `sha256(flow_file | case_name | step_index | step_text)`.
Verbatim `act:` text shared between two flows shares the cache entry. When
authoring a new flow whose first action is "land on the chat panel and pick
the default agent", **copy the exact wording from `chat-ask.flow.test.yml`**
rather than paraphrasing — same cache entry, free reuse.

Common sub-sequences worth treating as canonical:

- **Open agent selector + pick agent** — copy from `chat-ask.flow.test.yml`.
- **Submit a chat question** — copy the four-step pattern from
  `chat-ask.flow.test.yml`.
- **Open Monaco file from tree** — copy the first `act:` of
  `ide-save.flow.test.yml`.
- **Type into Monaco** — copy the four-step pattern from `ide-save.flow.test.yml`
  (the `browser_keyboard_type` hint is non-obvious; the verbatim copy
  keeps it correct).

Don't paraphrase to "be more readable" — paraphrase costs ~$0.05–0.20 of
LLM the first time a paraphrased flow runs in CI.
