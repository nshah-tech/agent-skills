---
name: verify-implementation
description: Independently audits a completed implementation against its approved proposal before a PR can open. Reads the proposal (CIR table, workflow contracts, checklists) and the final diff — NOT the executor's session — and verifies every claimed surface is actually evidenced. Use when a ticket is in 🧪 Verifying status, the user says "verify ACME-1823", or invokes "/verify-implementation".
---

# Verify Implementation

The Step 6 verification gate. This skill is the **judgment half** of verification: an independent, fresh strong-model session that audits what `task-executor` produced against what the proposal promised. It generates **no code** — it reads artifacts and writes a verdict, the same shape as `review-proposal`, applied to the diff instead of the proposal.

> **Why this runs as its own skill in a fresh session**: the evidence tables in `PROGRESS.md` are produced by the executor; they must be *audited* by a different session on the strong tier. An executor that self-certifies inherits its own blind spots — the correlated-errors problem. Evidence content and evidence judgment stay in different hands (**author ≠ reviewer**).

## When to Use

- A ticket is in `🧪 Verifying` status (set by `task-executor` when it finishes and pushes).
- The user says "verify ACME-1823", "audit the implementation", or invokes `/verify-implementation ACME-1823`.
- Triggered as Step 6 of the main workflow, after execution and before `🔀 PR Open`.

**Run this in a fresh session on the strong model tier.** Do NOT continue from the `task-executor` session — that would inherit the executor's assumptions along with its context.

---

## Workflow

### Step 1. Load the Artifacts (not the executor's session)
1. Find the ticket's proposal (`Sprints/<version>/<TICKET>-<ShortName>/<TICKET>-<ShortName>.md`) or bug plan (`Sprints/<version>/bugs/<TICKET>-<ShortName>.md`).
2. Find its `PROGRESS.md` and read the `## Verification` section the executor populated.
3. Read the **final diff** from the pushed branch (`git fetch && git log`/`git diff origin/<base>...origin/<branch>`), not the working tree of any live session.
4. Note the ticket's `## Risk Classification` (overall risk) — it sets how deep this audit goes (Step 4).

### Step 2. Build the Audit Checklist from the Proposal
Extract every claim the implementation must satisfy:
- **Every `CIR-*` item** from the review log — each has an executable verification coverage (a named test or a numbered QA script).
- **Every workflow-contract point** the proposal included in its `## Workflow Contracts` section (per-item contracts: per item).
- **Every `## Verification` row** the executor recorded.
- For a **bug**: the `## Repro` re-run result.

### Step 3. Audit — Is Each Claim *Demonstrated*, Not Just Asserted?
For each item on the checklist, confirm the evidence exists and is real:
- **Evidence format**: every `## Verification` row must be dated and environment-stamped, naming the data used — `check · pass/fail · date · env · data` (e.g. "Filtered export includes Due Date · pass · 2026-07-03 · staging · record `<id>`"). A bare `[x]` is **not** evidence.
- **Coverage**: every CIR item and every contract point maps to a green, dated row.
- **The diff backs the claim**: if a row says "filter wired up", the diff must actually touch the filter path. Absence-detection is the whole job — the typical escaped bug is an absence (the filter never wired, the export path never touched) that passed review because it was *considered*, not *verified*.
- **Anti-drift**: `PROGRESS.md` must not report 100% complete while any manual smoke or staging verification is still pending. Pending evidence is an open task.

### Step 4. Scale Audit Depth to Risk
| Overall risk | This audit |
|---|---|
| **Low** | Quick pass — build/typecheck + the focused test green; confirm no CIR item is unevidenced. |
| **Medium** | Full audit — every CIR row + contract point dated/stamped/green + touched regression-matrix rows run. |
| **High** | Medium + staging smoke with representative data confirmed + the ticket is in Release Hardening scope. |

### Step 5. Verdict

**If anything is claimed but not demonstrated** (missing evidence, undated row, CIR item with no green row, contract point unchecked, diff doesn't back a claim):
1. Write each gap back to `PROGRESS.md` as a new, atomic task.
2. Set status to `🏗️ Executing` and hand back to `task-executor`.
3. Output which specific claims failed the audit and why.

**If the audit is clean:**
1. Record the sign-off in `PROGRESS.md`: `Verified by <model> · <date> · fresh session · <TICKET>`.
2. **Draft** a Jira comment (sign-off date, model/session, evidence summary, link to `PROGRESS.md`), show it to the dev, and **post it only after the dev approves the content** — never post to Jira unprompted.
3. Run `gh pr create` (this skill's only non-artifact side effect; embed the sign-off in the PR description).
4. Update the sprint doc: set `<TICKET>` status to `🔀 PR Open`.

### Step 6. Bug and Hotfix Variants
- **Bug**: the audit centers on the `## Repro` re-run being green with evidence, plus any touched contract points. Depth still scales by risk.
- **Hotfix**: hotfixes deploy to **staging before prod**, so this audit runs against **staging, before the prod push**. On a clean audit, flip the `## Hotfixes` table's **`Verified (staging)?`** column to ✅ (it stays ❌ until then). The prod push must not happen with that column open.

### Step 7. Handoff
- If **gaps found**:
  > *"Verification found N unevidenced claims. I've written them back to `PROGRESS.md` and set status to 🏗️ Executing. Run `/task-executor <TICKET>` to close them, then `/verify-implementation <TICKET>` again."*
- If **clean**:
  > *"Verification passed. Sign-off recorded, PR opened, status → 🔀 PR Open."* (and, for hotfixes, *"`Verified (staging)?` flipped to ✅."*)
- **Session Bookmark**:
  > *"Session complete. To resume later, run `/workflow-status <version>`."*
