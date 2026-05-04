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

**If INIT**:
1. Create the `Sprints/<version>/` directory if it doesn't exist.
2. Read the template from `Sprints/_sprint-template.md` (or create a standard sprint structure with Overview, Goals, Tickets, Deployment Checklist if it doesn't exist).
3. Populate the `## Tickets` markdown table using the fetched data.
4. If there are matching proposal documents already in `Sprints/<version>/`, link to them in the Proposal column using `[[TICKET-ShortName]]` format.
5. Update `Sprints/_index.md` (the Map of Content) to include the new sprint, if the index exists.

**If UPDATE**:
1. Read the existing `Sprints/<version>/<version>.md` document.
2. Replace the rows in the `## Tickets` table with the fresh data from Jira. **MANDATORY**: Preserve existing Proposal links if they were manually added previously.

### Step 4. Present to User
- Provide an absolute file link to the created/updated sprint document.
- Summarize the sprint: *"Fetched N tickets (X Stories, Y Bugs)."*
- **Handoff / Session Bookmark**: Output the following explicitly: 
  > *"Session complete. To begin planning a feature, run `/jira-feature-architect <TICKET>`. To resume later, run `/workflow-status <version>`."*
