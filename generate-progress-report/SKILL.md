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
2. (For bugfixes, look in `Sprints/<version>/bugs/<TICKET_KEY>-<ShortName>.md` — or the legacy `pipeline/1_plans/<TICKET_KEY>-plan.md` — if the proposal is not found).
3. Read the entire document.

### Step 2. Verify Approval State
Check the `## Review Log` at the bottom of the proposal.
- If there are `BLOCKING` issues or no Review Log exists (for features), output a warning:
  > ⚠️ **Warning**: This proposal has not passed review yet. Generating the progress report now may result in executing flawed architecture. Proceed anyway? (Y/n)
  *(If user says N, abort).*

### Step 3. Extract Implementation Tasks
Find the `## Implementation TODO` section in the proposal.
Ensure the tasks are atomic and bite-sized (2-to-5 minutes). If they are too high-level (e.g., "Implement Backend Service"), break them down logically into smaller chunks based on the proposal's technical details before writing the progress file.

**Make every task pre-flightable** (this is what lets the cheap executor's Pre-flight Plan Review verify the plan before building — see `preflight-plan-review`):
- **Anchor on snippets/symbols, never bare line numbers.** Line numbers drift as earlier phases edit files; quote the before-code or name the function/identifier the task targets. A line number may accompany an anchor but never replace it.
- **Ship every enumeration with its re-derivation grep.** Any list a task depends on — call sites, `useMemo`/`useEffect` deps, column sets, field lists — must be accompanied by the exact `grep`/command that regenerates it, so recon diffs the plan's list against reality instead of trusting it. *(This is the highest-value rule: `INCOMPLETE-ENUMERATION` is the recurring finding class — see `Operations/PREFLIGHT-FINDINGS-LOG.md`.)*
- **Phrase assumptions as runnable checks.** "X is atomic", "flag F is stable before mount", "Z has N callers" → give the command that confirms each, so recon pastes evidence rather than re-judging.
- **Targeting a callback?** First grep all callers of the function that *contains* it — the edit belongs where all callers converge, not at one call site (the `WRONG-ANCHOR` class).
- **Mark `recon-critical` tasks.** Any task whose assumptions are load-bearing (a memo/deps list, a data-vs-structure decision, a shared-payload contract) gets a `recon-critical` tag so pre-flight runs Check 2/3 on it regardless of the ticket's overall risk tier.

#### Step 3a. Map verification coverage into tasks
Coverage must flow Proposal → PROGRESS.md → code with no judgment left to the cheap executor. In addition to the Implementation TODO tasks:

- **CIR verification → task**: for every `CIR-*` item in the proposal's review log, emit its verification coverage (field 5) as its own atomic task. Because review made that field executable, this is a direct copy — an automated test becomes "write test `<path>::<case>`", a manual QA script becomes a numbered task with its expected result. Never collapse multiple CIR verifications into one task.
- **Workflow-contract point → task**: for every contract the proposal includes in its `## Workflow Contracts` section, emit **each checklist point as one atomic task** — and for a per-item contract (e.g. a grid-column or API-field contract), **once per new/changed item** (N points × M items). Each carries the contract point's check as its done-condition.

Place these in the relevant phase, or a dedicated `Phase N: Verification` phase, so every compatibility surface named in review has a concrete, checkable task behind it.

- **Test tasks default to unit tests**: every automated-test task is a scoped unit spec placed **in the same phase as the code it covers** (write-failing-test → implement), with its exact scoped run command in the AC. For frontend logic that lives inline in a component, emit two tasks: "extract `<logic>` into `<Component>.utils.ts`" then "unit-test it". Integration runs and E2E smoke go **only in the final phase, once**, and only if the proposal calls for them. Never emit a task that writes a new E2E test for logic, or a Jest test that connects to a real database.

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

> **Status vocabulary** includes `⏸ Plan Amendment Needed` — set by `task-executor`'s Pre-flight Plan Review when a `stop-and-adjudicate` finding is raised; a strong session amends the plan (dated note) before execution resumes.

---

## Implementation Checklist

> **Note**: These tasks are derived from the approved proposal. They must be executed sequentially.
> **Pre-flight gate**: before executing each phase, `task-executor` runs the `preflight-plan-review` protocol against that phase's tasks and records a `## Pre-flight Plan Review — Phase N` block below. Tasks tagged `[recon-critical]` get assumption + implicit-dependency checks regardless of overall risk tier.

### Phase 1: <Phase Name>
- [ ] **1.1** Write failing unit test for `POST /invoices` in `invoice.controller.spec.ts`.
- [ ] **1.2** Define `InvoiceDto` with validation decorators.
- [ ] **1.3** `[recon-critical]` Implement `InvoiceService.create` to make the test pass. *(assumption: `create` has no existing callers — verify: `grep -rn "InvoiceService" src/`)*

### Phase 2: <Phase Name>
- [ ] **2.1** <Task description>.

(Mirror ALL tasks)

---

## Pre-flight Plan Review

> **Filled by `task-executor` at each phase boundary (Step 3.2), per the `preflight-plan-review` protocol.** One `— Phase N` block per phase, recording anchor/assumption evidence, `adjust-and-log` self-corrections, and any `stop-and-adjudicate` findings. Findings adjudicated by a strong session get a dated amendment in the proposal/plan doc + a row in `Operations/PREFLIGHT-FINDINGS-LOG.md`.

*(No pre-flight blocks yet — the executor appends them here as it reaches each phase.)*

---

## Verification

> **Filled by `task-executor`'s mechanical half (Step 4), audited by `/verify-implementation` (Step 6).** One row per check — every CIR verification and every workflow-contract point from Step 3a. Each row is dated and environment-stamped and names the data used. A bare `[x]` is **not** evidence; a failed check is a new task in the checklist above, not a footnote.
>
> **Anti-drift**: this feature is not 100% complete while any row below is pending. Do not mark `Feature Completion: 100%` with open rows.

| Check (CIR / contract point) | Pass/Fail | Date | Env | Data used |
|---|---|---|---|---|
| <e.g. CIR-3 Filtered export includes the new column> | | | | record `<id>` |
| <e.g. Grid contract pt.5 — record count matches filtered set (Due Date col)> | | | | |

**Sign-off** (written by `/verify-implementation` on a clean audit): `Verified by <model> · <date> · fresh session`

---

## Work Log & Session Summaries

### <Today's Date YYYY-MM-DD> — Progress Generation
- Generated `PROGRESS.md` tracker from approved proposal.
- Total tasks: <N> across <M> phases.
```

### Step 5. Update Sprint Deployment Checklist
Check if the proposal introduces any of the following:
- Changes to environment variables (`.env`)
- Database migrations or schema changes
- New deployment scripts or infrastructure requirements

If so, open the active Sprint document (e.g., `Sprints/<version>/<version>.md`) and automatically append these requirements as checkboxes under the `## Deployment Checklist` section. This ensures deployment requirements are never lost.

### Step 6. Handoff to User
Output the following explicit message:
> *"PROGRESS.md generated with N tasks across M phases. Run `/task-executor <TICKET_KEY>` to begin execution."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*
