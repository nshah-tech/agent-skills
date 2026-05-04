---
name: workflow-status
description: Displays the current state of a sprint by parsing the sprint document and providing actionable next steps for the agent or user. Acts as the "Where did we leave off?" session resumption point. Use when the user says "status of v2.16.0", "where are we", "workflow status", or invokes "/workflow-status".
---

# Workflow Status

Since the Jira automation workflow is fully asynchronous and spans multiple days, this skill serves as the "resume button". It reads the Sprint Document, summarizes what's currently in flight, and recommends the exact command to run next.

## When to Use

- The user asks "what's the status of the sprint", "where did we leave off"
- The user resumes work on a new day and wants to know what to do next
- The user explicitly invokes `/workflow-status v2.16.0`

---

## Workflow

### Step 1. Parse Command
Extract the sprint version (e.g., `v2.16.0`). If not provided, ask the user.

### Step 2. Load Sprint Document
Read the sprint document: `Sprints/<version>/<version>.md` in the documentation repo.
Locate the `## Tickets` markdown table.

### Step 3. Summarize Status
Parse the table and group the tickets by their Status column:

- **📋 Planning**: Draft proposal exists, waiting for review.
- **🔍 In Review**: Currently in the review gauntlet or has blocking issues.
- **✅ Approved**: Reviewed and passed, ready for execution.
- **🔨 In Progress**: Currently being executed by `/task-executor`.
- **🔀 PR Open**: Execution done, waiting for code review / merge.
- **📘 Wiki Done**: Fully completed with product documentation generated.
- **Pending/Todo**: No proposal drafted yet.

### Step 4. Determine Next Action
Identify the bottleneck or the most logical next step.

- If tickets are **Pending/Todo** -> Recommend `/jira-feature-architect <TICKET>` or `/jira-bugfix-planner <TICKET>`.
- If tickets are **📋 Planning** -> Recommend `/review-proposal <TICKET>`.
- If tickets are **🔍 In Review** -> Recommend checking the proposal's review log or running `/review-proposal <TICKET> --re-review` if fixed.
- If tickets are **✅ Approved** -> Recommend `/generate-progress-report <TICKET>`.
- If tickets are **🔨 In Progress** -> Recommend resuming execution with `/task-executor <TICKET>`.
- If tickets are **🔀 PR Open** -> Recommend checking the PR and then running `/product-doc-generator <TICKET>` after merge.

### Step 5. Present to User
Output a clean, dashboard-like summary to the user:

```markdown
## Sprint Status: v2.16.0

**Progress**: 2 Completed / 3 In-Flight / 5 Pending

### Current Focus
- **ACME-1823** is `🔍 In Review` (Waiting for architecture blocking issues to be resolved).
- **ACME-1849** is `🔨 In Progress` (Task execution halfway done).
- **ACME-1901** is `📋 Planning` (Drafted, ready for review).

### Recommended Next Steps
> Option A: Resume building the rate matrix
> Run: `/task-executor ACME-1849`

> Option B: Review the new webhook feature
> Run: `/review-proposal ACME-1901`
```
