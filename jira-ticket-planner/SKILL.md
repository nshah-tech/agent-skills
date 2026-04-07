---
name: jira-ticket-planner
description: Fetches a Jira ticket, summarizes the issue in plain language, researches the relevant codebase, and produces an implementation plan for the fix. Use this skill whenever the user asks to "check a ticket", "summarize a Jira issue", "investigate a bug from Jira", "plan a fix for ticket X", "look at S2Q-XXXX", or any request that involves reading a Jira ticket and producing actionable engineering output. Also trigger when the user pastes a Jira URL or mentions a ticket key like S2Q-1234, PROJ-456, etc. and wants to understand or fix the issue described in it.
---

# Jira Ticket Planner

Fetch a Jira ticket, distill it into a clear summary, research the affected code, and produce an implementation plan — all in one pass.

## When to Use

- The user mentions a Jira ticket key (e.g. `S2Q-1973`, `PROJ-42`)
- The user pastes a Jira URL (e.g. `https://company.atlassian.net/browse/PROJ-42`)
- The user says things like "check ticket", "investigate this issue", "plan a fix for", "summarise this bug"

## Workflow

### Step 1. Extract the Ticket Key

Parse the ticket key from the user's message. It may appear as:
- A bare key like `S2Q-1973`
- Embedded in a URL like `https://company.atlassian.net/browse/PROJ-42`
- Referenced casually like "that 1973 ticket" (ask for clarification if ambiguous)

### Step 2. Fetch the Ticket from Jira

Use the `mcp_atlassian-mcp-server_getJiraIssue` tool to retrieve the ticket details.

- Use the Atlassian site URL as the `cloudId` (e.g. `company.atlassian.net`)
- Request markdown as the `responseContentFormat` for readable output
- Extract these key fields:
  - **Summary** (title)
  - **Description** (the full issue body)
  - **Issue Type** (Bug, Story, Task, etc.)
  - **Priority**
  - **Status**
  - **Assignee**
  - **Reporter**
  - **Labels / Components** (if present)
  - **Linked Issues** (if any — these often contain related context)
  - **Comments** (scan for reproduction steps or additional context from teammates)
  - **Attachments** (note any screenshots or files mentioned)

### Step 3. Summarize the Issue

Write a clear, concise summary of the ticket that answers:

1. **What is the problem?** — Describe the user-facing bug or feature gap in plain English.
2. **What is the expected behaviour?** — What should happen instead.
3. **What is the impact?** — Who is affected and how severely.
4. **Reproduction context** — Any specific steps, data, or environment details mentioned in the ticket or comments.

Keep the summary short (3–6 sentences). Avoid copying the Jira description verbatim — distill and clarify it. If the ticket is vague or missing details, explicitly call out what information is missing and ask the user.

### Step 4. Research the Codebase

Investigate the relevant source code to understand the root cause:

1. **Identify entry points** — Use `grep_search` to locate the functions, services, or modules mentioned in the ticket description (error messages, feature names, entity names).
2. **Trace the data flow** — Read the relevant files with `view_file` to understand how data moves through the system. Follow the call chain from the entry point to the suspected failure point.
3. **Identify the root cause** — Based on the code reading, form a hypothesis about why the bug occurs or what needs to change for the feature.
4. **Note dependencies** — List any files, entities, services, or external systems that would be affected by a fix.

Spend adequate time here. Read at least 2–3 relevant files. The quality of the plan depends on understanding the code, not just the ticket.

### Step 5. Create the Implementation Plan

Write an implementation plan as an artifact (`implementation_plan.md`) using the standard planning-mode format:

```markdown
# [Goal — one-line description]

Brief description of the problem and what the fix accomplishes.

## Jira Ticket Summary

| Field | Value |
|---|---|
| Key | PROJ-XXX |
| Type | Bug / Story / Task |
| Priority | High / Medium / Low |
| Status | To Do / In Progress |
| Reporter | Name |

[Your distilled summary from Step 3]

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

### Step 6. Ask the User

After presenting the plan:
- Highlight any open questions or ambiguities from the ticket
- Ask if the user wants to proceed with execution
- If the user approves, follow the standard planning-mode execution workflow (create task.md, implement, verify, create walkthrough.md)

## Tips for Quality

- **Don't rush the code research.** A shallow plan that misses a secondary affected file wastes more time than spending an extra minute reading code.
- **Call out missing information early.** If the ticket is vague about reproduction steps or expected behaviour, ask the user before planning.
- **Link to specific code.** Use file links with line numbers (e.g. `[powerLane.ts:L69](file:///path/to/file#L69)`) so the plan is immediately actionable.
- **Consider test coverage.** Check if existing tests cover the affected area. If not, include adding tests as part of the plan.
