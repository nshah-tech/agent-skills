---
name: generate-progress-report
description: Generates a PROGRESS.md checklist from a reviewed feature proposal or bugfix plan. Breaks down the implementation into atomic, 2-to-5-minute bite-sized tasks. Use when the user says "generate progress", "break down ACME-1823", or invokes "/generate-progress-report".
---

# Generate Progress Report

Acts as the bridge between planning and execution. Reads a fully reviewed proposal and extracts the "Implementation TODO" section into a standalone, stateful `PROGRESS.md` checklist for the task executor.

## When to Use

- The user asks to "generate progress", "break down tasks for ACME-1823"
- The user explicitly invokes `/generate-progress-report`
- Triggered as the next step after `/review-proposal` passes

---

## Workflow

### Step 1. Parse Command & Load Proposal
Extract the ticket key (e.g., `ACME-1823`).
1. Find the proposal file: `Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md`.
2. (For bugfixes, look in `pipeline/1_plans/<TICKET_KEY>-plan.md` if the proposal is not found).
3. Read the entire document.

### Step 2. Verify Approval State
Check the `## Review Log` at the bottom of the proposal.
- If there are `BLOCKING` issues or no Review Log exists (for features), output a warning:
  > ⚠️ **Warning**: This proposal has not passed review yet. Generating the progress report now may result in executing flawed architecture. Proceed anyway? (Y/n)
  *(If user says N, abort).*

### Step 3. Extract Implementation Tasks
Find the `## Implementation TODO` section in the proposal.
Ensure the tasks are atomic and bite-sized (2-to-5 minutes). If they are too high-level (e.g., "Implement Backend Service"), break them down logically into smaller chunks based on the proposal's technical details before writing the progress file.

### Step 4. Write the PROGRESS.md File
**Location**: `Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-PROGRESS.md` (or alongside the bugfix plan).

Use this exact structure:

```markdown
# <TICKET_KEY>: <Feature Name> — Implementation Progress

> [!IMPORTANT]
> **AGENT INSTRUCTIONS**: 
> 1. This is your **source of truth for state**. 
> 2. At the **START** of every session: Read this file to see what was finished.
> 3. During work: Mark items as `[/]` (in-progress) as you start them.
> 4. At the **END** of every session (or after every major task): Mark items as `[x]` (completed) and update the "Current Session Summary" below.
> 5. **NEVER** delete tasks from this list. Use it to maintain context across days.
> 6. **READ** the proposal document `<TICKET_KEY>-<ShortName>.md` for full technical details on each task.

---

## Progress at a Glance (Update this!)
- **Status**: Planning Complete — Ready for Implementation
- **Current Phase**: Phase 1: <First Phase Name>
- **Feature Completion**: 0%
- **Last Updated**: <today's date YYYY-MM-DD>
- **Reference Tickets**: [<TICKET_KEY>](https://<cloudId>/browse/<TICKET_KEY>)

---

## Implementation Checklist

> **Note**: These tasks are derived from the approved proposal. They must be executed sequentially.

### Phase 1: <Phase Name>
- [ ] **1.1** Write failing unit test for `POST /power-lane` in `powerLane.controller.spec.ts`.
- [ ] **1.2** Define `PowerLaneDto` with validation decorators.
- [ ] **1.3** Implement `PowerLaneService.create` to make the test pass.

### Phase 2: <Phase Name>
- [ ] **2.1** <Task description>.

(Mirror ALL tasks)

---

## Work Log & Session Summaries

### <Today's Date YYYY-MM-DD> — Progress Generation
- Generated `PROGRESS.md` tracker from approved proposal.
- Total tasks: <N> across <M> phases.
```

### Step 5. Handoff to User
Output the following explicit message:
> *"PROGRESS.md generated with N tasks across M phases. Run `/task-executor <TICKET_KEY>` to begin execution."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*
