---
name: jira-ticket-planner
description: Fetches a Jira ticket, summarizes the issue in plain language, researches the relevant codebase, and produces an implementation plan for the fix. Use this skill whenever the user asks to "check a ticket", "summarize a Jira issue", "investigate a bug from Jira", "plan a fix for ticket X", "look at ACME-XXXX", or any request that involves reading a Jira ticket and producing actionable engineering output. Also trigger when the user pastes a Jira URL or mentions a ticket key like ACME-1234, PROJ-456, etc. and wants to understand or fix the issue described in it. Also triggers when the user says "init jira", "setup jira", or "create jira config" to initialize a new `.jira-planner.json` config file.
---

# Jira Ticket Planner

Fetch a Jira ticket, distill it into a clear summary, research the affected code, and produce an implementation plan — all in one pass.

## When to Use

- The user mentions a Jira ticket key (e.g. `ACME-1973`, `PROJ-42`)
- The user pastes a Jira URL (e.g. `https://company.atlassian.net/browse/PROJ-42`)
- The user says things like "check ticket", "investigate this issue", "plan a fix for", "summarise this bug"
- The user says "init jira", "setup jira config", or "create jira config" — trigger the **Init Workflow** below

---

## Config File: `.jira-planner.json`

This skill reads workspace configuration from a `.jira-planner.json` file at the **root of the current repository**. This file should be committed to the repo so every developer in the project gets the right defaults automatically.

### Schema

```json
{
  "cloudId": "your-company.atlassian.net",
  "defaultProject": "PROJ",
  "displayName": "Your Company / Project Name"
}
```

| Field | Required | Description |
|---|---|---|
| `cloudId` | ✅ | The Atlassian site URL (e.g. `acme.atlassian.net`). Used as the `cloudId` in every MCP call. |
| `defaultProject` | ✅ | Default project key prefix (e.g. `ACME`, `PROJ`). Used to expand bare ticket numbers like `1973` → `PROJ-1973`. |
| `displayName` | optional | Human-readable label shown in plan headers (e.g. `"Acme – Backend API"`). |

### `.gitignore` note

The config file contains **no secrets** (no tokens, no passwords — auth is handled by the MCP server). It is safe and intended to be committed.

---

## Init Workflow

Trigger this when the user asks to set up or initialise Jira config for a project.

### Step I-1. Check for existing config

```bash
cat .jira-planner.json 2>/dev/null || echo "NOT_FOUND"
```

If the file already exists, show its contents and ask the user whether to overwrite or update it.

### Step I-2. Ask the user for config values

Ask (in a single message):
1. **Atlassian site URL** — e.g. `acme.atlassian.net`
2. **Default project key** — e.g. `ACME`
3. **Display name** (optional) — e.g. `Acme – Backend API`

### Step I-3. Write the config file

```bash
cat > .jira-planner.json << 'EOF'
{
  "cloudId": "<cloudId>",
  "defaultProject": "<defaultProject>",
  "displayName": "<displayName>"
}
EOF
```

### Step I-4. Scaffold the local workflow and skill

Create the Antigravity agent directories and write two files:

```bash
mkdir -p .agent/workflows .agent/skills
```

**`.agent/workflows/jira.md`** — the entry point teammates invoke:

```markdown
---
description: Fetch a Jira ticket and produce an implementation plan for it.
---

# Jira Ticket Planner — Workflow

**Project:** <displayName>  
**Atlassian site:** <cloudId>  
**Default project key:** <defaultProject>

## How to use

Invoke with a ticket key or number:
- `jira <defaultProject>-1973`
- `jira 1973`  (expands to `<defaultProject>-1973`)
- `jira https://<cloudId>/browse/<defaultProject>-1973`

## Steps

1. The config is already known — use `cloudId: <cloudId>` and `defaultProject: <defaultProject>`. Do NOT re-read `.jira-planner.json`; use these values directly.
2. Extract the ticket key from the argument (expand bare numbers using `<defaultProject>`).
3. Fetch the ticket using `mcp_atlassian-mcp-server_getJiraIssue` with `cloudId: <cloudId>`.
4. Follow the full workflow defined in `.agent/skills/jira-ticket-planner.md`.
```

**`.agent/skills/jira-ticket-planner.md`** — the reusable skill logic (copy of the canonical skill with no config values hardcoded, so it stays generic and reusable across projects):

```markdown
# Jira Ticket Planner — Skill

Summarize a Jira ticket, research the affected code, and produce an implementation plan.

## Steps

### Step 1. Summarize the Issue

Write a clear, concise summary (3–6 sentences) that answers:
1. **What is the problem?** — User-facing bug or feature gap in plain English.
2. **What is the expected behaviour?**
3. **What is the impact?** — Who is affected and how severely.
4. **Reproduction context** — Steps, data, or environment details from the ticket or comments.

Avoid copying the Jira description verbatim. If the ticket is vague, call out what is missing and ask the user.

### Step 2. Research the Codebase

1. Use `grep_search` to locate functions, services, or modules mentioned in the ticket.
2. Use `view_file` to trace the call chain from entry point to the suspected failure point.
3. Form a hypothesis about the root cause.
4. Note files, entities, or external systems affected by the fix.

Read at least 2–3 relevant files before writing the plan.

### Step 3. Write the Implementation Plan

Produce `implementation_plan.md`:

\```markdown
# [Goal — one-line description]

Brief description of the problem and what the fix accomplishes.

> **Project:** <displayName>
> **Ticket:** [PROJ-XXX](https://cloudId/browse/PROJ-XXX)

## Jira Ticket Summary

| Field | Value |
|---|---|
| Key | PROJ-XXX |
| Type | Bug / Story / Task |
| Priority | High / Medium / Low |
| Status | To Do / In Progress |
| Reporter | Name |

[Distilled summary from Step 1]

## Root Cause Analysis

Explain why the issue occurs, referencing specific files and line numbers.

## Proposed Changes

### [Component Name]

#### [MODIFY] [filename](file:///absolute/path)
- What will change and why

#### [NEW] [filename](file:///absolute/path)
- What this new file does

## Open Questions

## Verification Plan

### Automated Tests
### Manual Verification
\```

### Step 4. Ask the User

Highlight open questions, ask for approval. If approved, create `task.md`, implement, verify, and produce `walkthrough.md`.
```

> **Why two files?** The workflow is the repo-specific entry point (has `cloudId` and `defaultProject` baked in). The skill is the generic, reusable logic that the workflow delegates to — and that other workflows in the same repo can also reference.

### Step I-5. Confirm and suggest commit

Tell the user all three files are ready and show the commit command:

```bash
git add .jira-planner.json .agent/workflows/jira.md .agent/skills/jira-ticket-planner.md
git commit -m "chore: add jira-planner config and Antigravity agent files"
```

Also mention:
- The `.agent/` directory should **not** be in `.gitignore` — it is intentionally committed.
- Teammates get the full workflow just by pulling the branch — no manual skill installation needed.

---

## Ticket Workflow

### Step 1. Load Config

Before doing anything else, check for the config file:

```bash
cat .jira-planner.json 2>/dev/null || echo "NOT_FOUND"
```

- **If found:** parse `cloudId`, `defaultProject`, and `displayName` from it. Silently proceed.
- **If not found:** inform the user:
  > No `.jira-planner.json` found in the current directory. You can run **"init jira"** to create one, or provide the Atlassian site URL now (e.g. `acme.atlassian.net`).

  If the user provides the `cloudId` inline (e.g. from a pasted URL), use it for this session only — do not create a config file unless asked.

### Step 2. Extract the Ticket Key

Parse the ticket key from the user's message. It may appear as:
- A bare key like `ACME-1973`
- Embedded in a URL like `https://company.atlassian.net/browse/PROJ-42`
- A bare number like `1973` — expand using `defaultProject` from config → `ACME-1973`
- Referenced casually like "that 1973 ticket" (ask for clarification if ambiguous)

### Step 3. Fetch the Ticket from Jira

Use the `mcp_atlassian-mcp-server_getJiraIssue` tool to retrieve the ticket details.

- Set `cloudId` to the value loaded from config (or provided by the user)
- Request `markdown` as the `responseContentFormat`
- Extract these key fields:
  - **Summary** (title)
  - **Description** (the full issue body)
  - **Issue Type** (Bug, Story, Task, etc.)
  - **Priority**
  - **Status**
  - **Assignee** / **Reporter**
  - **Labels / Components** (if present)
  - **Linked Issues** (related context)
  - **Comments** (reproduction steps or teammate context)
  - **Attachments** (screenshots or files mentioned)

### Step 4. Summarize the Issue

Write a clear, concise summary (3–6 sentences) that answers:

1. **What is the problem?** — Describe the user-facing bug or feature gap in plain English.
2. **What is the expected behaviour?** — What should happen instead.
3. **What is the impact?** — Who is affected and how severely.
4. **Reproduction context** — Specific steps, data, or environment details from the ticket or comments.

Avoid copying the Jira description verbatim — distill and clarify it. If the ticket is vague or missing details, explicitly call out what is missing and ask the user.

### Step 5. Research the Codebase

Investigate the relevant source code to understand the root cause:

1. **Identify entry points** — Use `grep_search` to locate the functions, services, or modules mentioned in the ticket (error messages, feature names, entity names).
2. **Trace the data flow** — Read relevant files with `view_file` to follow the call chain from entry point to the suspected failure point.
3. **Identify the root cause** — Form a hypothesis about why the bug occurs or what needs to change.
4. **Note dependencies** — Files, entities, services, or external systems affected by the fix.

Read at least 2–3 relevant files. Quality of the plan depends on understanding the code.

### Step 6. Create the Implementation Plan

Write the plan as an artifact (`implementation_plan.md`):

```markdown
# [Goal — one-line description]

Brief description of the problem and what the fix accomplishes.

> **Project:** <displayName from config, or cloudId>  
> **Ticket:** [PROJ-XXX](https://cloudId/browse/PROJ-XXX)

## Jira Ticket Summary

| Field | Value |
|---|---|
| Key | PROJ-XXX |
| Type | Bug / Story / Task |
| Priority | High / Medium / Low |
| Status | To Do / In Progress |
| Reporter | Name |

[Your distilled summary from Step 4]

## Root Cause Analysis

Explain why the issue occurs, referencing specific files and line numbers.

## Proposed Changes

### [Component Name]

#### [MODIFY] [filename](file:///absolute/path)
- What will change and why

#### [NEW] [filename](file:///absolute/path)  (if applicable)
- What this new file does

## Open Questions

Any clarifying questions for the user that affect the implementation.

## Verification Plan

### Automated Tests
- Specific test commands or new test cases needed

### Manual Verification
- Steps the user should take to verify the fix
```

Set `request_feedback = true` on the artifact so the user can approve before execution begins.

### Step 7. Ask the User

After presenting the plan:
- Highlight open questions or ambiguities from the ticket
- Ask if the user wants to proceed with execution
- If approved, follow the standard planning-mode execution workflow (create `task.md`, implement, verify, create `walkthrough.md`)

---

## Tips for Quality

- **Don't rush the code research.** A shallow plan that misses a secondary affected file wastes more time than spending an extra minute reading code.
- **Call out missing information early.** If the ticket is vague about reproduction steps or expected behaviour, ask before planning.
- **Link to specific code.** Use file links with line numbers (e.g. `[powerLane.ts:L69](file:///path/to/file#L69)`) so the plan is immediately actionable.
- **Consider test coverage.** Check if existing tests cover the affected area. If not, include adding tests in the plan.
- **Config is per-repo.** If you switch to a different repository mid-session, re-read `.jira-planner.json` from the new working directory.
