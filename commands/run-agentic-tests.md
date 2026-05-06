---
name: run-agentic-tests
description: Run agentic browser tests with HEADED=1 DEBUG=1 and the right env defaults for the dev's detected backend mode (cloud vs local)
activeForm: Running agentic browser tests
argument-hint: "[pattern]"
allowed-tools:
  - Bash
  - Read
---

# Run agentic browser tests

Wraps `pnpm test:agentic` with `HEADED=1 DEBUG=1` (so the dev sees the
browser and the per-iteration LLM reasoning) and with env-var defaults
matched to the dev's already-running backend.

The argument `$ARGUMENTS` is the flow name pattern (or empty for "all
flows"), passed through to `pnpm test:agentic`.

This command must be run from the root of an `oxy-hq/oxygen-internal`
checkout.

## Steps

### 1. Sanity-check the working directory

```bash
test -f web-app/tests/agentic/README.md
```

If the path is missing, exit and tell the dev: "This command must be run
from the root of an oxy-hq/oxygen-internal checkout where the agentic
browser-test layer is present."

### 2. Detect the dev's running backend mode

Probe both well-known ports without spawning anything. Cloud mode and local
mode use different internal ports.

```bash
# Local mode: backend on 3000, vite on 5173.
LOCAL_HEALTH=$(curl -s -m 1 http://localhost:3000/api/health || true)
LOCAL_AUTH=$(echo "$LOCAL_HEALTH" | grep -o '"auth_enabled":[^,}]*' || true)

# Cloud mode: backend on 3001 (internal port).
CLOUD_HEALTH=$(curl -s -m 1 http://localhost:3001/api/health || true)
CLOUD_AUTH=$(echo "$CLOUD_HEALTH" | grep -o '"auth_enabled":[^,}]*' || true)
```

Branching:

- **Cloud mode running** (3001 healthy, `auth_enabled` true):
  ```
  OXY_HEALTH_URL=http://localhost:3001/api/health
  OXY_BASE_URL=http://localhost:3001
  ```
- **Local mode running** (3000 healthy, `auth_enabled` false or absent):
  ```
  OXY_HEALTH_URL=http://localhost:3000/api/health
  OXY_BASE_URL=http://localhost:5173      # Vite dev server
  ```
- **Neither responds.** Don't try to spawn anything. Tell the dev:

  > Neither backend mode is responding. Start one before running tests:
  >
  > **Local mode** (recommended for first runs):
  > ```bash
  > cd demo_project && oxy start --local --enterprise
  > # in another terminal:
  > cd web-app && pnpm dev
  > ```
  >
  > **Cloud mode**: follow `internal-docs/DEVELOPMENT.md` for the auth-enabled setup.
  >
  > Then re-run `/run-agentic-tests`.

  Exit. The runner *can* auto-spawn the local backend if both
  `--no-auto-backend` and `--no-auto-frontend` are off, but the cold-spawn
  path is slow and brittle in interactive sessions; prompting the dev to
  pre-start is the right call.

- **Both responding.** That's an unusual setup (probably two backends
  fighting). Default to cloud mode (the more recently-shipped path) and
  warn the dev.

### 3. Run the tests

From `web-app/`:

```bash
cd web-app
HEADED=1 DEBUG=1 \
  OXY_HEALTH_URL="$OXY_HEALTH_URL" \
  OXY_BASE_URL="$OXY_BASE_URL" \
  pnpm test:agentic $ARGUMENTS --no-auto-backend --no-auto-frontend
```

`--no-auto-backend` and `--no-auto-frontend` skip the runner's own
spawn-and-wait paths since we already verified the backend is up. This
makes the run start faster and avoids a second backend racing against the
dev's running one.

### 4. Report

After the run completes (or fails), surface:

1. The path of the markdown report:
   ```
   web-app/tests/agentic/.results/<ts>.md
   ```
2. The JSON next to it (same data programmatically).
3. If any case failed, the path to its trace:
   ```
   web-app/tests/agentic/.traces/<flow>-<case>.zip
   ```
   And the command to view it:
   ```bash
   pnpm exec playwright show-trace web-app/tests/agentic/.traces/<flow>-<case>.zip
   ```
4. The grand cost printed at the top of the run output (the runner reports
   `cost_usd` per step, per run, and a total).

## Error handling

- **`oxy: --enterprise: unrecognized argument`** when the dev manually
  started the backend: the system `oxy` on PATH is older than the
  workspace build. Tell the dev to set `OXY_BIN=$PWD/target/debug/oxy` or
  rebuild.
- **`backend did not become healthy`**: the backend was up when we probed
  but went down before the tests started. Tail
  `web-app/tests/agentic/.logs/backend.log` and read the last 20 lines.
- **All cases pass on cold but flake on warm**: the action cache replayed
  a stale selector. Either delete
  `web-app/tests/agentic/.cache/bespoke-actions.json` to force re-derive,
  or bump `CACHE_VERSION` in `runner/action-cache.ts`.

## Notes

- Never strip `HEADED=1 DEBUG=1` — those are the defaults that make this
  command useful for interactive runs. Devs who want a quiet run can
  invoke `pnpm test:agentic` directly.
- Don't auto-spawn the backend. The runner's own auto-spawn paths exist
  for CI; in an interactive session, an explicit pre-start is faster and
  the dev can read the backend logs in another terminal.
- If the dev wants to run *without* `HEADED`, suggest they invoke
  `pnpm test:agentic` directly with their own env vars rather than
  shoehorning a `--no-headed` flag into this command.
