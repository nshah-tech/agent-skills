---
name: sprint-manager
description: Initializes and updates sprint documentation. Fetches Jira tickets for a given sprint and creates or updates the Sprint overview document (e.g., Sprints/v2.16.0/v2.16.0.md). Use when the user says "create sprint v2.16.0", "init sprint", "update sprint doc", or invokes "/sprint-manager".
---

# Sprint Manager

Initialize a new sprint folder and document, or update an existing sprint document with the latest ticket statuses from Jira.

## When to Use

- The user asks to "create sprint", "init sprint v2.16.0"
- The user asks to "update sprint doc"
- The user explicitly invokes `/sprint-manager`

---

## Config File: `.jira.json`
Read workspace configuration from `.jira.json` at the root of the repository.
Parse `cloudId` and `defaultProject`. If not found, ask the user to run `jira-config-init`.

## Workflow

### Step 1. Parse Command
Determine if the user is running `init` or `update`, and extract the sprint version (e.g., `v2.16.0`).
**CRITICAL**: Ask the user: *"Would you like to include bug-type tickets in this sprint document, or ignore them?"* (Only ask this on `init`).

### Step 2. Fetch Sprint Data
Use the Jira MCP server's search tool (e.g., `mcp_atlassian-mcp-server_searchIssues` or `searchJiraIssues`) to fetch tickets in the sprint.
**JQL**: `sprint = "<version>" ORDER BY issuetype, priority`

Extract for each ticket (skipping Bug types if the user chose to ignore them):
- Key (e.g., ACME-1823)
- Summary
- Type (Story, Task, Bug)
- Status
- Assignee

### Step 3. Init or Update Sprint Doc
**Location**: `Sprints/<version>/<version>.md`

Features, bugs, and hotfixes are tracked in **separate tables** so the post-ship doc sync can find behavior-changing changes:
- `## Tickets` — Story/Task feature tickets.
- `## Bug Fixes` — Bug tickets shipped through the version branch. Columns: `Key | Summary | Impact | Status | Plan`. **Impact** is `behavior` (user-visible change → needs a Wiki update at ship) or `internal`. Plan links to `bugs/<TICKET>-<ShortName>.md`.
- `## Hotfixes` — fixes pushed **directly to prod** (out-of-band from the version branch). Columns: `Key | Summary | Impact | Prod Deploy | Verified (staging)? | Back-merged? | Wiki synced?`. Plan links to `hotfixes/<TICKET>-<ShortName>.md`. **Verified (staging)?**, **Back-merged?**, and **Wiki synced?** default to ❌ until confirmed done (hotfixes are verified on staging *before* the prod push — see the project's workflow guide, if it has one).

**If INIT**:
1. Create the `Sprints/<version>/` directory if it doesn't exist.
2. Read the template from `Sprints/_sprint-template.md` (or create a standard sprint structure with Overview, Goals, Tickets, **Bug Fixes**, **Hotfixes**, Deployment Checklist if it doesn't exist). The status legend must include `🧪 Verifying` (execution done + evidence recorded, awaiting the Step 6 `/verify-implementation` audit) between `🏗️ Executing`/`🔨 In Progress` and `🔀 PR Open`.
3. Populate the `## Tickets` table with Story/Task tickets and the `## Bug Fixes` table with Bug tickets. Default new bugs' Impact to `behavior` unless clearly internal — the user can adjust. Leave `## Hotfixes` empty at init (rows are added by `/jira-bugfix-planner` when a fix is flagged as a direct-to-prod hotfix).
4. If there are matching proposal documents already in `Sprints/<version>/` (or bug plans in `Sprints/<version>/bugs/`), link to them using standard markdown.
5. Update `Sprints/_index.md` (the Map of Content) to include the new sprint, if the index exists.
6. **Carry forward the regression matrix**: if the project keeps a `REGRESSION-MATRIX.md` (one row per user workflow), copy the previous sprint's to `Sprints/<version>/REGRESSION-MATRIX.md`, resetting the `Claimed by` column to `_unclaimed_` (the workflow rows are stable and carried forward; the claims are per-sprint). If the project has none, skip this step. The `## Release Hardening` section comes from `_sprint-template.md`.
7. **Scope advisory (advisory, not a cap)**: count the sprint's flagship features (new-feature epics/stories, not tasks/bugs). If **more than 2**, add a note under `## Goals`: *"⚠️ N flagship features integrate in this release — several large features landing together is the usual source of feature-interaction bugs; consider flags or staggered releases."* This is advisory only — the dev controls the code, not which tickets land in a sprint. Never block on it.

**If UPDATE**:
1. Read the existing `Sprints/<version>/<version>.md` document.
2. Refresh the `## Tickets`, `## Bug Fixes`, and `## Hotfixes` tables from Jira. **MANDATORY**: preserve existing Proposal/Plan links, the Impact classification, and the Hotfix `Back-merged?` / `Wiki synced?` states if they were set previously — never reset them to ❌ on refresh.

### Step 4. Present to User
- Provide an absolute file link to the created/updated sprint document.
- Summarize the sprint: *"Fetched N tickets (X Stories, Y Bugs — Z marked behavior-changing)."*
- **Handoff / Session Bookmark**: Output the following explicitly: 
  > *"Session complete. To begin planning a feature, run `/jira-feature-architect <TICKET>`. To resume later, run `/workflow-status <version>`."*
