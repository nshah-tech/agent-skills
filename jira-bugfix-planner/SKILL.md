---
name: jira-bugfix-planner
description: Fetches or consumes a Jira bug/task, summarizes the issue, researches the affected code path, and creates a lightweight implementation plan. Use when the user invokes "/jira-bugfix-planner", asks to investigate a Jira bug, or wants a fix plan before implementation.
---

# Jira Bugfix Planner

Create a focused bugfix implementation plan without the full feature-proposal
workflow. This skill is for defects, regressions, and small corrective tasks
where a heavy architecture proposal is unnecessary unless the user asks for one.

## When to Use

- The user invokes `/jira-bugfix-planner <TICKET>`.
- The user asks to investigate or plan a fix for a Jira bug/task.
- The user provides Jira details manually because MCP access is unavailable.
- The task needs root cause analysis and an implementation plan before code.

## Config

Read `.jira.json` from the documentation repo root:

```json
{
  "cloudId": "acme.atlassian.net",
  "defaultProject": "ACME",
  "displayName": "Acme Web"
}
```

If `.jira.json` is missing, run `/jira-config-init` (or ask the user for the site and project key).

Use Jira as a read-only source unless the user explicitly asks for a Jira write.

## Workflow

### Step 1. Load Local Context

Before planning, read:

- `.jira.json`
- `CLAUDE.md` / `AGENTS.md` / `.agent/instructions.md` (whichever exist)
- `CONTRIBUTING.md`
- The project's workflow guide, if any (e.g. `JIRA_WORKFLOW_GUIDE.md`)
- Any existing plan/progress file for the ticket under `Sprints/<version>/bugs/`
  (or the legacy `pipeline/1_plans/`, or a feature proposal folder
  `Sprints/<version>/<TICKET>-<ShortName>/`)

If the ticket affects a code repo, also read that repo's `README.md`,
`docs/CONTRIBUTING.md`, relevant `docs/`, `.agent/rules.md`, and local
Jira-planning skill/workflow if present.

### Step 2. Fetch or Ingest Ticket Details

If Jira MCP is available, fetch the issue with
`mcp_atlassian-mcp-server_getJiraIssue` using:

- `cloudId`: the `cloudId` from `.jira.json`
- `responseContentFormat`: `markdown`

Extract summary, description, issue type, priority, status, reporter, assignee,
labels/components, linked issues, comments, and attachments.

If Jira is unavailable and the user pasted ticket details, use the pasted details
and explicitly note that Jira was not queried.

### Step 3. Summarize the Issue

Write a concise summary that answers:

1. What is the user-facing problem?
2. What should happen instead?
3. What is the impact and affected workflow?
4. What reproduction context or environment is known?

Do not copy the Jira description verbatim. Distill it.

### Step 4. Research the Code Path

Read at least 2-3 relevant files in the affected repo(s). Trace the path from
entry point to failure point:

- UI render/click/state path for frontend bugs.
- API/controller/service/repository path for backend bugs.
- Queue/worker/file-processing path for background-job bugs.
- Shared DTO/payload/export/import consumers when the fix touches shared data.

When payload data exists but UI behavior is wrong, verify render/update wiring
before assuming a backend issue.

### Step 5. Create the Plan

First determine whether this is a **normal bug** (ships through the version branch) or a **hotfix** (pushed directly to prod, out-of-band from `version/vX.Y.Z`). Ask the user if it's not clear from the ticket. This decides the folder and the dashboard table.

Plans live in the sprint as **one file** by default (promote to a sub-folder only if extra reference files are needed):

```text
Normal bug → Sprints/<version>/bugs/<TICKET>-<ShortName>.md
Hotfix     → Sprints/<version>/hotfixes/<TICKET>-<ShortName>.md
```

Determine `<version>` from the ticket's Jira sprint/fixVersion. Create `Sprints/<version>/bugs/` or `Sprints/<version>/hotfixes/` if it doesn't exist. Do **not** use `pipeline/1_plans/` for new plans (legacy location).

For a **hotfix**, the plan must also cover: the **back-merge** into `version/vX.Y.Z` (so the release doesn't revert it) and, if behavior-changing, an **immediate `/product-doc-sync` on deploy** (not at release).

Use this structure:

```markdown
# <TICKET>: <Fix Title>

> **Ticket:** [<TICKET>](https://<cloudId>/browse/<TICKET>)  
> **Source:** Jira MCP / User-provided Jira details  
> **Plan Date:** YYYY-MM-DD

## Jira Ticket Summary

| Field | Value |
|---|---|
| Key | <TICKET> |
| Type | Bug / Task |
| Impact | behavior (user-visible change → needs Wiki update at ship) / internal |
| Priority | High / Medium / Low |
| Status | <Status> |
| Reporter | <Name> |

<Distilled summary.>

## Risk Classification

> Score every dimension at planning time. **Overall risk = the highest single dimension.** Gate depth scales with this (see the project's workflow guide → risk tiers, if defined).

| Dimension | Score (Low/Med/High) | Reason |
|---|---|---|
| Code surface | | One file → Low · one repo/several modules → Med · multiple repos or shared package → High |
| Data contract | | Internal only → Low · API/DTO changed → Med · shared payload/persisted JSON/import-export shape → High |
| UI impact | | Hidden/internal → Low · one screen → Med · grid/upload/export/bulk/core workflow → High |
| Tenant/data risk | | No customer data → Low · reads customer/tenant data → Med · writes/migrates tenant-scoped data → High |
| Regression history | | Stable area → Low · some bugs → Med · repeated cluster (per `Operations/KNOWN-FAILURE-MODES.md`) → High |

**Overall Risk**: <Low / Medium / High>

## Repro

> **Required.** A fix cannot be verified without a repro to re-run. Keep it exact enough that a different session (or a cheaper model) can reproduce the bug mechanically.

- **Steps**: numbered, exact click/API path to trigger the bug.
- **Input**: the file/data that triggers it — reference an existing test fixture (e.g. `Operations/fixtures/`) where one applies; if this is a parser/import bug, a fixture **must** be added as part of the fix.
- **Expected vs Actual**: what should happen vs what happens today.

## Root Cause Analysis

Explain the likely cause with concrete file paths and line references.

## Proposed Changes

### <Repo or Component>

#### [MODIFY] <absolute path>
- What will change and why.

#### [NEW] <absolute path>
- What the new file does, if needed.

## Compatibility and Regression Surfaces

List impacted workflows separately, such as import/rating, reprocess/reload,
Bulk Update, export, grid display, popup behavior, reports, background jobs, or
shared payload consumers.

## Open Questions

- Use `None` if no blocker remains.

## Verification Plan

### Automated Tests
- **Regression unit test first**: a unit test that fails on the buggy code and passes after the fix — `<file>.spec.ts` / `<file>.test.ts::<case>` plus its scoped run command. If the buggy logic is inline in a React component, extract it into a pure `*.utils.ts` function as part of the fix and test that.
- Other specific test files or commands. Integration (real DB) or E2E smoke only if the bug can't be reproduced at unit level — say why, run them once at the end, and keep any E2E read-only.

### Manual Verification
- Exact workflow checks.

## Bug Escape Classification

> **Required for Medium+ priority bugs.** Turns the bug into pipeline telemetry: root cause says *what broke*; escaped gate says *which pipeline step should have caught it*. Aggregated by `/incident-reporter --aggregate` into the sprint's Gate-Leak Histogram.

| Field | Value |
|---|---|
| Affected workflow | <e.g. orders grid filters — maps to a regression-matrix row> |
| Root cause category | <missing requirement · ambiguous requirement · missed downstream consumer · missing unit/integration test · missing UI/manual smoke · fixture gap · environment/migration gap · tenant scoping · third-party behavior · performance · merge/back-merge> |
| Escaped gate | <proposal missed it · CIR missed it · task too broad · build/tests didn't cover it · smoke skipped · fixture unrepresentative · matrix lacked the row · hotfix not back-merged> |
| Should become regression? | <Yes → name the fixture / matrix row / contract point added · No → why not> |
| Prevention added | <e.g. "grid-contract point 5 now covers derived numeric columns"> |

If the root cause is a *new* class not already in `Operations/KNOWN-FAILURE-MODES.md`, `/incident-reporter` appends it there.

## Implementation Boundary

- State what is explicitly out of scope.
- State whether Jira writes, production deployment, migrations, or branch/commit
  work are out of scope for this plan.
```

### Step 6. Update the Sprint Dashboard

1. Open `Sprints/<version>/<version>.md`.
2. **Normal bug** → add/update a row in the `## Bug Fixes` table: `Key | Summary | Impact | Status | Plan`, where **Impact** is `behavior` or `internal` and **Plan** links to `bugs/<TICKET>-<ShortName>.md`.
3. **Hotfix** → add/update a row in the `## Hotfixes` table: `Key | Summary | Impact | Prod Deploy | Back-merged? | Wiki synced?`, with **Plan** linking to `hotfixes/<TICKET>-<ShortName>.md`. Set **Back-merged?** and **Wiki synced?** to ❌ until each is actually done.
4. If the relevant table doesn't exist yet, create it (or run `/sprint-manager` to regenerate a dashboard that predates this convention).

> This is what lets the post-ship `/product-doc-sync` step find behavior-changing changes. A fix that never lands in the dashboard is invisible to the Wiki sync — and for a hotfix, the `## Hotfixes` row is also the audit trail for the mandatory back-merge.

### Step 7. Handoff

Present the plan path, summarize open questions, and ask for approval before
implementation unless the user already explicitly asked to implement after
planning.

After approval, implementation should follow the repo-local code conventions and
validation rules in `AGENTS.md` and the target repo's `docs/CONTRIBUTING.md`.
