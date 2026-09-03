# Oxy POC Builder

Turn first-meeting call notes into a clickable proof-of-concept: an Oxygen org with a `Staging` workspace containing a quick-win proto app and a two-slide timeline/pricing deck.

## What It Does

The **oxy-poc-builder** skill standardizes the sales POC package. From a set of discovery-call notes it:

1. Extracts a POC brief (company, quick win, seed-data entities, stakeholders)
2. Guides creation of the prospect's org at [app.oxygen-hq.com](https://app.oxygen-hq.com) with a workspace named **Staging**
3. Builds a **proto app** — a custom-code React module (module-designs stack + chrome) demoing the quick-win value prop — inventory replenishment, warehouse stock tracking, bookkeeping automation, etc. — on synthetic data seeded with the prospect's real entity names
4. Builds a **deck app** — a second React module with exactly two slides:
   - **Timeline** — data infrastructure in month 1, functional app by month 3, full app 6 months after that
   - **Pricing** — $11k/month ($6k services + $5k platform, includes one module)
5. Publishes both to the org via `oxy publish` (drafts, promoted in the admin UI) and verifies they render in the Staging workspace

The timeline and pricing content is canonical — the skill only personalizes framing text, never the numbers.

## Required Inputs

- Call notes (or a transcript, or a Slack summary of the meeting) from the first meeting with the prospect

That's it. The proto app ships its synthetic data inside the bundle (`src/data.ts`), so no warehouse connection is needed for the POC.

## Example Invocations

```
"Here are my notes from the Poke House call. Build the POC."
```

```
"Spin up a demo org for Acme Books — the quick win is bookkeeping
automation. Notes attached."
```

## What's in This Skill

| File | Purpose |
| --- | --- |
| `SKILL.md` | Workflow instructions for Claude |
| `templates/poc-brief.md` | Call-notes extraction template |

Reference implementations live outside the skill: `~/repos/module-designs/` (React scaffold + chrome atoms) and `~/repos/gia-foods/` (a completed POC package).

## Related Skills

- **oxy-app-builder** — the custom-code (`oxy-app.json` / `oxy publish`) deploy path used for both POC apps
- **oxy-semantic-layer** / **oxy-etl-builder** — used after the POC converts, during the month-1 data-infrastructure phase
