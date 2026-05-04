---
name: incident-reporter
description: Generates an Incident Report or Architecture Decision Record (ADR) after a bugfix is completed. Triggered automatically or invoked when the user asks to "write an incident report", "create ADR", or invokes "/incident-reporter".
---

# Incident Reporter

Documents the root cause, fix, and architectural learnings of significant bugfixes. 

## When to Use

- Suggested by `/task-executor` after a bugfix PR is created.
- The user asks to "write an incident report", "create ADR for ACME-2038"
- The user explicitly invokes `/incident-reporter ACME-2038`

---

## Workflow

### Step 1. Parse Command & Options
Extract the ticket key (e.g., `ACME-2038`).
If the user didn't specify whether they want an Incident Report or an ADR, ask them:
> "Would you like to generate an **Incident Report** (focus on root cause and timeline) or an **ADR** (focus on architectural decisions and trade-offs) for this fix?"

### Step 2. Load the Bugfix Plan
Find the bugfix plan: `pipeline/1_plans/<TICKET_KEY>-plan.md` or the PR description/commit history for the fix.

### Step 3. Generate the Document

#### If Incident Report
**Location**: `Wiki/Incidents/<YYYY-MM-DD>-<ShortName>.md`

**Template**:
```markdown
# Incident Report: <Issue Summary>

**Date**: <YYYY-MM-DD>
**Ticket**: [<TICKET_KEY>](https://<cloudId>/browse/<TICKET_KEY>)

## Root Cause Analysis
<5 Whys or plain English description of what caused the bug>

## Impact
<What systems or users were affected and how>

## Resolution
<How the bug was fixed technically>

## Prevention
<What tests, monitors, or safeguards were added to prevent recurrence>
```

#### If ADR (Architecture Decision Record)
**Location**: `Wiki/ADRs/<00X>-<ShortName>.md` (increment the ADR number).

**Template**:
```markdown
# ADR <00X>: <Decision Title>

**Date**: <YYYY-MM-DD>
**Status**: Accepted
**Ticket**: [<TICKET_KEY>](https://<cloudId>/browse/<TICKET_KEY>)

## Context
<What is the issue that forced us to make a decision?>

## Decision
<What change was made to the architecture?>

## Consequences
- **Positive**: <Benefits>
- **Negative**: <Trade-offs or new risks introduced>
```

### Step 4. Present to User
Output the following explicit message:
> *"Document generated at `Wiki/Incidents/...`. The team can review it for future learnings."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*
