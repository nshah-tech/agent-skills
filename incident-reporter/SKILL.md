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
Extract the ticket key (e.g., `ACME-2038`), **or** detect the aggregate form: `/incident-reporter <version> --aggregate` (e.g. `/incident-reporter v2.16.0 --aggregate`). If aggregate, skip to **Step 5**.

If the user didn't specify whether they want an Incident Report or an ADR, ask them:
> "Would you like to generate an **Incident Report** (focus on root cause and timeline) or an **ADR** (focus on architectural decisions and trade-offs) for this fix?"

### Step 2. Load the Bugfix Plan
Find the bugfix plan: `Sprints/<version>/bugs/<TICKET_KEY>-<ShortName>.md` (or the legacy `pipeline/1_plans/<TICKET_KEY>-plan.md`), or the PR description/commit history for the fix.

### Step 3. Generate the Document

#### If Incident Report
**Location**: `Operations/Incidents/<YYYY-MM-DD>-<ShortName>.md`

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
**Location**: `Decisions/ADR-<00X>-<ShortName>.md` (increment the ADR number).

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

### Step 4. Register a New Failure Class (required for Highest-priority bugs)
Read the bug plan's `## Bug Escape Classification` block (required for Medium+ bugs per `jira-bugfix-planner`). Read the documentation repo's failure-mode register, `Operations/KNOWN-FAILURE-MODES.md` (create it with a `| # | Failure pattern | Example tickets | Escaped gate | Now guarded by |` table if the project has none yet).

Skip this step for incidents that are not product bugs (security, infrastructure, vendor outages) — the register tracks recurring *bug classes*, not one-off operational events. Say so in the handoff.

- **If the root cause matches an existing register row**: add this ticket to that row's `Example tickets` — do not create a duplicate row.
- **If it's a genuinely new class** (required whenever the bug is Highest priority): append a new row copying the classification's fields — `Failure pattern | Example tickets | Escaped gate | Now guarded by`. "Now guarded by" names the fixture/contract/matrix-row added as prevention, or "none yet" if prevention is still open.
- Never edit or delete an existing row's history; superseded guards are struck through, not removed.

### Step 5. Handoff to User (single-ticket mode)
Output the following explicit message:
> *"Document generated at `Operations/Incidents/...` or `Decisions/ADR-...`. The team can review it for future learnings."* If a register row was added/updated: *"`KNOWN-FAILURE-MODES.md` updated (row KFM-N)."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*

---

## Aggregate Mode: `/incident-reporter <version> --aggregate`

Rolls up a sprint's bug classifications into pipeline-improvement recommendations — the input for the sprint retrospective's "what could improve." Read-only over existing data; writes one section back to the sprint doc.

### Aggregate Step 1. Gather Classifications
Read every bug plan under `Sprints/<version>/bugs/` (and `Sprints/<version>/hotfixes/` for hotfixes) that has a `## Bug Escape Classification` block. Extract, per ticket: Affected workflow, Root cause category, Escaped gate, Should become regression?, Prevention added.

### Aggregate Step 2. Roll Up by Category
Group by **Escaped gate** (primary) and **Root cause category** (secondary). Count occurrences. This is the leak signal: it shows empirically which pipeline step is leaking, instead of guessing.

### Aggregate Step 3. Write the Gate-Leak Histogram
Write (or replace, if re-run) a `### Gate-Leak Histogram` section under the sprint doc's `## Retrospective`:

```markdown
### Gate-Leak Histogram (generated by `/incident-reporter <version> --aggregate`, <date>)

| Escaped gate | Count | Root cause breakdown | Example tickets |
|---|---|---|---|
| Smoke skipped | 5 | missing UI/manual smoke (5) | ACME-2093, 2104, ... |
| CIR missed it | 3 | missed downstream consumer (3) | ACME-2109, 2128, ... |
| Fixture unrepresentative | 2 | fixture gap (2) | ACME-2045, 2090 |

**Recommendation**: <the leaking gate with the highest count is the next pipeline change to prioritize — name it explicitly, e.g. "Smoke skipped leaks most — tighten the fixture-smoke requirement before relying on manual smoke.">
```

### Aggregate Step 4. Present to User
Output:
> *"Aggregated N bug classifications from `<version>`. Gate-Leak Histogram written to the sprint doc's Retrospective. Top leak: `<gate>` (<count>) — recommend: `<recommendation>`."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*
