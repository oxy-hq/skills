---
name: oxy-poc-builder
description: Build a sales POC package from first-meeting call notes. Use when the user shares discovery-call or first-meeting notes and asks to "build a POC", "spin up a demo", "set up the org in Oxygen", "make the proto app", or "create the deck" for a prospect. Produces an Oxygen (app.oxygen-hq.com) org with a "Staging" workspace containing two apps - a quick-win proto app and a timeline/pricing deck.
---

# Oxy POC Builder

You are an expert at turning first-meeting call notes into a working proof-of-concept that a prospect can click through. Every POC follows the same package structure; the content is personalized from the call notes.

## The POC Package

One POC = one Oxygen org + one workspace + two apps:

1. **Oxygen org** at [app.oxygen-hq.com](https://app.oxygen-hq.com), named after the prospect.
2. **Workspace named `Staging`** inside that org. Always this name - it signals to the prospect that this is a sandbox.
3. **App 1 - the proto app**: a working demo of the quick-win value prop identified in the meeting (commonly inventory replenishment or bookkeeping automation), running on synthetic data seeded with the prospect's own entities (their locations, vendors, product names from the notes).
4. **App 2 - the deck**: exactly two slides - **Timeline** and **Pricing** - with fixed canonical content (below), personalized only in the framing text.

**Both apps are custom-code React apps** (the `oxy-app.json` + `oxy publish` path), NOT declarative `*.app.yml` dashboards. POCs are sales surfaces - they must look like the Oxygen product, and they ship as bespoke UI. Do not build `*.app.yml` files unless the user explicitly asks for the declarative path.

Do the steps in order. Steps 1 and 3-4 are file work you can do directly; step 2 involves browser actions in the Oxygen UI.

## Step 1: Extract the POC Brief from Call Notes

Read the call notes and fill in `templates/poc-brief.md`. Extract:

- **Company**: name, industry, size signals (locations, headcount, transaction volume)
- **Quick win**: the ONE pain point with the fastest path to visible value. If the notes surface several, pick the one with the clearest before/after and note the others as expansion candidates.
- **Entities for seed data**: real names mentioned in the call - store locations, vendors, product lines, account names, systems they use (Toast, QuickBooks, NetSuite, ...). These make the demo feel like *their* data.
- **Stakeholders**: who was on the call and what each cares about (the deck framing targets the economic buyer; the proto app targets the operator).
- **Vocabulary**: their words for things ("shops" vs "stores", "SKUs" vs "items"). Use their vocabulary everywhere in both apps.

If the notes are too thin to identify a quick win, ask the user rather than guessing - the proto app is worthless if it demos the wrong problem. If the notes link a meeting recording behind auth (Google Recorder, Zoom), try to fetch it, but a Slack summary of the meeting is a sufficient source on its own.

## Step 2: Create the Oxygen Org and Staging Workspace

These are browser steps at [app.oxygen-hq.com](https://app.oxygen-hq.com) (org/workspace creation has no CLI). Walk the user through them, or perform them if browser tooling is available:

1. Sign in to app.oxygen-hq.com.
2. Create a new **organization** named after the prospect (e.g. "Gia Foods").
3. In the **Manage** tab, create a **workspace named `Staging`**.
4. Skip data connectors for now - the proto app runs on synthetic in-bundle data. Connect the real warehouse only when the POC converts (that is the "1 month data infrastructure" phase on the timeline slide).
5. Invite the prospect contacts from the brief as viewers once both apps are live, not before.

Record two identifiers from the workspace URL, `app.oxygen-hq.com/<org-slug>/workspaces/<workspace-uuid>`, in the POC brief:

- **org slug** (e.g. `gia-foods`) -> `orgSlug` in each app's `oxy-app.json`
- **workspace UUID** -> the `--project` value for each app's first `oxy publish`

## Step 3: Build the Proto App (Quick Win)

**REQUIRED SUB-SKILL:** oxy-skills:oxy-app-builder, specifically its `## Deploying custom-code apps (oxy-app.json)` section - the manifest fields and the three load-bearing files. Ignore its declarative `*.app.yml` material and its plan-first/user-sign-off gate; the POC package structure IS the approved plan.

### Module scaffold

Each app is a **self-contained React module** in a repo named after the prospect (one repo per prospect, one directory per app, e.g. `stock-tracker/` and `poc-deck/`). Stack: React 19 + TypeScript strict + Vite 6 + Tailwind v4 + pnpm - the `~/repos/module-designs/` stack, no exceptions.

Scaffold by copying from a `module-designs` module (e.g. `bookkeeping/`):

- `src/chrome/` atoms - `Topbar` (OXYGEN header + live clock), `Panel`, `Pill`, `KpiTile`, `LedgerTable` - plus `src/index.css` (`@theme` design tokens) and `src/cn.ts`. Copying the chrome is what makes the POC read as the Oxygen product.
- `tsconfig.json`, `vite.config.ts` (keep `base: process.env.OXY_APP_BASE_PATH || "/"` and the `copyOxyAssets()` plugin; give each module a unique dev port), `pnpm-workspace.yaml` (`allowBuilds: { esbuild: true }`).
- Write per-module: `package.json` (`@<prospect>/<app>`), `index.html`, `oxy-app.json`, `src/App.tsx`, `src/data.ts`.

`oxy-app.json` (see the app-builder skill for all fields):

```json
{
  "schemaVersion": 2,
  "slug": "stock-tracker",
  "orgSlug": "gia-foods",
  "name": "Warehouse Stock Tracker",
  "description": "Receiving log and live warehouse stock position.",
  "status": "12 products · 1 warehouse · illustrative data",
  "build": { "outDir": "dist" }
}
```

### Synthetic data rules

First-meeting POCs never have client data. Seed data lives in `src/data.ts` as typed, hand-computed constants - no database, no query engine:

- Use the **prospect's real entity names** from the brief (their locations, vendors, products). Never `Store A` / `Widget 1`.
- **When the notes don't name an entity tier** (e.g. a bookkeeping call names no vendors): invent industry-plausible names consistent with their business, and flag them in the POC brief as "invented - confirm with prospect". Do not ask the user first; do not use generic placeholders.
- Make the numbers **tell the quick-win story**: 2-3 rows should be in a "needs action" state (stockout risk, unreconciled, overdue) so the demo has something to point at.
- Keep it to 10-25 rows per table - enough to feel real, small enough to eyeball.
- **Narrative numbers must tie out to seed rows.** Any count or total in the copy ("3 items need attention") must match what the data actually produces. Derive, don't duplicate: compute derived rows and KPI values from the seed array (`filter`/`find`/`length`), so an edit to one row can't desynchronize the headline.

### Layout

Whatever the domain, the proto app follows the same narrative arc top to bottom: **headline `KpiTile` row -> the problem list(s) (`Panel` + `LedgerTable` of rows needing action, status `Pill`s) -> one supporting chart (plain SVG or styled divs - do not add a chart library) -> a closing block stating what the full product automates**. Include an "ILLUSTRATIVE DATA" pill in the header.

**Frame at the category, not the anecdote.** A vivid quote from the notes ("my biggest problem is knowing how much jasmine rice I have") is proof the general problem is felt - it is not the app's scope. Title, header, and hero KPI speak to the whole problem (all products, all locations); the quoted entity appears as supporting flavor (a KPI delta line, one phone mock, one highlighted row). Building the app *around* the quote makes the POC read narrower than the deal.

**When the quick win involves data collection** (no tracking exists today - receiving, counts, field logging), a dashboard alone demos only half the problem. Structure the app as a **two-prong story**: prong 1 - mobile mocks of the worker-facing capture flow (`PhoneFrame` + `PhoneCardField` from `module-designs/inventory/src/chrome/`; 2-3 phones: the logging action, a scheduled task that keeps data fresh, and a compliance/confirmation screen), prong 2 - the centralizing dashboard those taps feed, including inbound visibility (open POs / "on order") alongside on-hand. Bridge them with a one-line divider ("every tap above feeds every number below"). The capture prong is what convinces the operator the data will actually get logged; the dashboard is worthless without it.

### Verify

`pnpm build` (strict `tsc` + `vite build`) must pass, and `dist/oxy-app.json` must exist after the build (proves `copyOxyAssets` ran). Eyeball with `pnpm dev`.

## Step 4: Build the Deck App

The deck is a second React module (`poc-deck/`), same scaffold, rendering exactly two slides. Personalize only the prospect name and the quick-win phrase in the framing copy. Everything else is **fixed canonical content** - never change the milestones or numbers:

**Slide 1 - Timeline:**

| Milestone | When |
| --- | --- |
| Data infrastructure live | Month 1 |
| Functional app in your team's hands | Month 3 |
| Full app (complete module scope) | Month 9 (6 months after functional app) |

**Slide 2 - Pricing:**

- **11,000 USD / month** total
- 6,000 USD / month services
- 5,000 USD / month platform - **includes one module**
- No setup fees; month-to-month during the POC phase.

(Amounts are written `11,000 USD` here because a dollar sign followed by a digit is mangled by the skill runner's positional-argument substitution. In the app itself, render them as `$11,000` etc.)

If the user wants different numbers for a specific deal, they will say so; these values are the defaults for every first-meeting POC.

## Optional: Visionary Apps (when the user asks to "show the vision")

Beyond the proto app + deck, strong deals get one or more **visionary apps** - the BMG "Policy Studio" pattern (set a policy -> simulated outcome ±1σ -> sweep to the optimum). These sell phase 2/3 of the timeline, not the wedge. Same module scaffold; three shapes that map to most ops domains:

- **Policy studio**: interactive levers (sliders) + a deterministic toy model + a margin/outcome curve with the optimum marked. "Turn gut feel into a policy you can test."
- **Digital twin**: projected state curves per entity (on hand + inbound - demand) with predicted failure dates and scenario toggles.
- **Approval-loop agent**: machine-drafted actions (POs, journal entries) with visible reasoning and a human APPROVE button - include one "held back because the data is bad" item and one "no action needed" explanation; restraint sells trust.

Rules: mark them SIMULATED/ILLUSTRATIVE, keep the toy model deterministic and hand-written (no chart/ML libraries), reuse the proto app's seed entities so the suite reads as one product, and have each visionary app's closing block reference the capture layer (the vision is only as good as the data collection sold in the proto app).

## Step 5: Publish and Verify

Publish each module as a draft to the org with `oxy publish` (there is no GitHub-integration step for custom-code apps):

1. **Auth**: `oxy login --env production` (browser loopback; caches per host). The logged-in browser session must be the **company app-admin account** - a personal Google session will "succeed" but report you can't publish. The login output tells you which account it grabbed and whether it can publish.
2. **First publish per app** (from the module dir): `oxy publish --project <workspace-uuid>` - the workspace UUID from Step 2. This auto-registers the app on the org. Without `--project`, the first publish fails with "app <org>/<slug> is not registered".
3. **Subsequent publishes**: plain `oxy publish`.
4. Default publishes land as **drafts**, which are invisible in the workspace until promoted. For a POC org you own, skip the ceremony: `oxy publish --promote` goes straight to the live channel (the draft-then-promote flow exists for production CI, not POCs). Confirm both apps render in the workspace before inviting prospect contacts.

## Quality Guidelines

- **Their words, their entities.** Every label, title, and seed row should read like it came from inside the prospect's business.
- **One quick win, demoed deeply** beats three demoed shallowly. Expansion candidates belong in conversation, not in the POC.
- **The deck is boring on purpose.** Two slides, fixed numbers. The proto app carries the excitement; the deck answers "when and how much" in ten seconds.
- **Never fake live data claims.** The proto app should say the data is illustrative; the timeline slide is where real data infrastructure is promised.

## Common Issues

- **`publish rejected (401 Unauthorized)`**: the cached token expired or belongs to a non-admin account. Rerun `oxy login --env production` and read its account/admin report; switch the browser session to the company account if it grabbed a personal one.
- **`app <org>/<slug> is not registered`**: first publish needs `--project <workspace-uuid>`.
- **Published but not visible in the workspace**: the build went to the draft channel. Republish with `--promote` (or promote in the admin UI). The live URL is `app.oxygen-hq.com/customer-apps/<org-slug>/<app-slug>/`.
- **`ERR_PNPM_IGNORED_BUILDS`**: `pnpm-workspace.yaml` is missing `allowBuilds: { esbuild: true }`.
- **App publishes but launcher card is blank**: `oxy-app.json` didn't make it into `dist/` - the `copyOxyAssets()` vite plugin is missing.
- **Wrong workspace name**: it is always `Staging`, capitalized, even if the prospect asks about production - production comes after the POC converts.

## Additional Resources

- **`templates/poc-brief.md`** - call-notes extraction template (Step 1)
- **`~/repos/module-designs/`** - chrome + scaffold source (any module; `bookkeeping/` is a clean minimal one)
- **`~/repos/gia-foods/`** - completed reference POC: `stock-tracker/` (proto app) + `poc-deck/` (deck), built from a Slack meeting summary
- **README.md** - user-facing overview of this skill
