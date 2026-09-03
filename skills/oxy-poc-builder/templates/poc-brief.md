# POC Brief: [PROSPECT_NAME]

> Fill this in from the first-meeting call notes before touching any YAML.
> It is the single source of truth for both apps and the Oxygen org setup.

## Company

- **Name**:
- **Industry**:
- **Size signals** (locations, headcount, volume):
- **Systems mentioned** (POS, accounting, warehouse, etc.):

## Quick Win

- **The ONE pain point to demo**:
- **Before / after in one sentence**:
- **Who feels this pain daily** (the operator persona):
- **Expansion candidates** (other pains mentioned - do NOT build these):

## Seed Data Entities

Real names from the call - these go into the proto app's VALUES CTEs.

- **Locations / stores**:
- **Vendors / suppliers**:
- **Products / SKUs / accounts**:
- **Their vocabulary** (their word -> our word):

## Stakeholders

| Name | Role | Cares about | Invite to Staging? |
| --- | --- | --- | --- |
|  |  |  |  |

## Oxygen Setup

From the workspace URL `app.oxygen-hq.com/<org-slug>/workspaces/<workspace-uuid>`:

- **Org name**:
- **Org slug** (-> `orgSlug` in each `oxy-app.json`):
- **Workspace UUID** (-> `--project` on each app's first `oxy publish`):
- **Workspace**: `Staging` (always)

## Status

- [ ] Org created at app.oxygen-hq.com
- [ ] `Staging` workspace created (Manage tab)
- [ ] Proto app builds (`pnpm build`) and renders locally (`pnpm dev`)
- [ ] Deck app builds and renders locally
- [ ] Both apps published as drafts (`oxy publish --project <workspace-uuid>`)
- [ ] Drafts promoted to live in the admin UI; both render in Staging
- [ ] Prospect contacts invited as viewers
