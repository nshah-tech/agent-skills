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
- **⏸ Plan Amendment Needed**: Pre-flight Plan Review raised a blocking finding; execution halted pending strong-tier adjudication of the plan.
- **🧪 Verifying**: Execution done and pushed; evidence recorded, awaiting the independent Step 6 audit.
- **🔀 PR Open**: Verified and PR opened, waiting for code review / merge.
- **📘 Wiki Done**: Fully completed with product documentation generated.
- **Pending/Todo**: No proposal drafted yet.

### Step 3.5. Bug-Pipeline Bypass Detection (🚨)
Also read the sprint doc's `## Bug Fixes` table. The bug pipeline is mandatory for high-priority bugs but nothing *enforces* it — this step *detects* a bypass so it surfaces on the next status check instead of at the next sprint audit (an unenforced pipeline drifts silently — a whole sprint of bugs can ship with this table empty).

Flag as a `🚨` item, with the exact remediation command, any bug row where:
- **Priority is Highest or High** and the `Plan` column is `—` / empty → *"No bug plan — run `/jira-bugfix-planner <TICKET>`"*.
- **Priority is Highest** and no incident report exists for it → *"Highest-priority bug with no RCA — run `/incident-reporter <TICKET>`"*.

These are advisory (the pipeline has no hard gate), but they must appear in the output whenever present — do not silently omit them.

### Step 3.6. Pre-flight Bypass Detection (🚨)
For any ticket that is `🔨 In Progress` or later, open its `PROGRESS.md`. For each phase that has **completed** implementation tasks (`[x]`), there must be a corresponding `## Pre-flight Plan Review — Phase N` block. Flag as a `🚨` item any phase where implementation tasks are done but the pre-flight block is missing:
- *"ACME-XXXX Phase N executed without a Pre-flight Plan Review — the plan-vs-code gate was skipped. Re-run `/preflight-plan-review ACME-XXXX` and reconcile before the PR opens."*

Also surface any ticket sitting in `⏸ Plan Amendment Needed` — it is **blocked** awaiting strong-tier adjudication of pre-flight findings:
- *"ACME-XXXX is ⏸ Plan Amendment Needed — a strong session must adjudicate the open pre-flight findings (amend the plan or overrule) before execution resumes."*

### Step 4. Determine Next Action
Identify the bottleneck or the most logical next step.

- If tickets are **Pending/Todo** -> Recommend `/jira-feature-architect <TICKET>` or `/jira-bugfix-planner <TICKET>`.
- If tickets are **📋 Planning** -> Recommend `/review-proposal <TICKET>`.
- If tickets are **🔍 In Review** -> Recommend checking the proposal's review log or running `/review-proposal <TICKET> --re-review` if fixed.
- If tickets are **✅ Approved** -> Recommend `/generate-progress-report <TICKET>`.
- If tickets are **🔨 In Progress** -> Recommend resuming execution with `/task-executor <TICKET>`.
- If tickets are **🧪 Verifying** -> Recommend the independent audit: `/verify-implementation <TICKET>` (run it in a fresh session).
- If tickets are **🔀 PR Open** -> Recommend checking the PR and then running `/product-doc-sync <TICKET>` after merge to prod.

### Step 5. Present to User
Output a clean, dashboard-like summary to the user:

```markdown
## Sprint Status: v2.16.0

**Progress**: 2 Completed / 3 In-Flight / 5 Pending

### Current Focus
- **ACME-1823** is `🔍 In Review` (Waiting for architecture blocking issues to be resolved).
- **ACME-1849** is `🔨 In Progress` (Task execution halfway done).
- **ACME-1901** is `📋 Planning` (Drafted, ready for review).

### 🚨 Bug-Pipeline Bypass
- **ACME-2151** (Highest) has no plan — run `/jira-bugfix-planner ACME-2151`.

### Recommended Next Steps
> Option A: Resume building the rate matrix
> Run: `/task-executor ACME-1849`

> Option B: Review the new webhook feature
> Run: `/review-proposal ACME-1901`
```

*(Omit the 🚨 section entirely when there are no bypasses to report.)*
