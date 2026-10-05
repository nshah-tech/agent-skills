---
name: preflight-plan-review
description: Verifies a plan's task anchors and stated assumptions against the codebase as it exists at execution time, BEFORE any code is written. Catches stale anchors, missing dependencies, false assumptions, and structure-vs-data conflicts. Use when the user invokes "/preflight-plan-review", asks to "check the plan against the code", "pre-flight this plan", or "validate a plan before building". Also the canonical protocol referenced by task-executor at every phase boundary.
---

# Pre-flight Plan Review

The pipeline's plan-vs-reality gate. A plan is written by a strong model against the code *as it was at planning time*; the code drifts, earlier phases move anchors, and the plan's author has blind spots about its own assumptions. Pre-flight verifies every task against **HEAD as it exists right now**, before a line of code is written — so mismatches cost a grep, not a shipped bug or a Step 6 bounce-back.

> This skill is the canonical protocol; `task-executor` references it at each phase boundary, and `/preflight-plan-review` invokes it standalone.

## When to Use

- **Embedded (the common path)**: `task-executor` runs this protocol at the top of **every phase**, before executing that phase's implementation tasks. Not just phase 1 — earlier phases' edits rot later phases' anchors.
- **Standalone**: `/preflight-plan-review <TICKET | plan-doc-path>` for (a) an ad-hoc plan doc that never went through `generate-progress-report`, or (b) a **freshness re-check** after a gap or a rebase, without starting execution.

---

## The Protocol

Run these checks against every task in the phase about to be executed. **Model tier: cheap** (this is mechanical, evidence-based work). Depth scales with the ticket's `## Risk Classification`.

### Check 1 — Anchors (all risk tiers)
For each task: the named file exists; the quoted before-code (or the tag/identifier the task anchors on) is found in it. Line numbers are drift-tolerant — **anchor on the code snippet or symbol, never a bare line number**. Record the grep/read that confirms it.

### Check 2 — Assumptions (Medium+ risk, and any task marked `recon-critical`)
Every assumption the task states — "X is atomic", "Y is not per-fetch churn", "Z has exactly N call sites", "flag F is stable before mount" — is re-verified with a command whose output you **paste as evidence**. No evidence, no ✅ (same discipline as `/verify-implementation`).

### Check 3 — Implicit-dependency hunt (High risk, and any `recon-critical` task)
Every enumeration in the plan — deps lists, call-site lists, column sets, field lists — is **independently re-derived by grep** and diffed against the plan's list. This is the check that catches the highest-value class (`INCOMPLETE-ENUMERATION`): a `useMemo` deps list missing 8 flags, a "remove all 8 call sites" that is actually 9.

### Check 4 — Classify each mismatch (two-tier)

> **Rubric: if the fix requires knowing *why* the plan wanted it — stop.**

- **`adjust-and-log`** — pure mechanical drift: line moved, identifier renamed unambiguously, the same snippet found a few lines away. The executor self-corrects and records a one-line note in the recon block. No round-trip.
- **`stop-and-adjudicate`** — anything semantic: an assumption is false, an enumeration is incomplete, the plan's design conflicts with the code's runtime structure, or a genuine ambiguity. Write it up (below), flip status, halt this phase.

### Check 5 — Design-level dissent (invited, not just permitted)
Beyond the mechanical checks, if the plan's approach looks wrong for a reason you can articulate — raise it as a `stop-and-adjudicate` finding. Raising a wrong concern costs one adjudication round; suppressing a right one costs a shipped bug. (High-value catches — e.g. a memo deps list missing half its flags — are often design-level, not mechanical.)

---

## Recording Findings

Write a **`## Pre-flight Plan Review — Phase N`** block in the ticket's `PROGRESS.md` (create if absent). Structure:

```markdown
## Pre-flight Plan Review — Phase N  (<date>, <model>)

**Anchors/assumptions checked** (evidence):
- Task N.1 — anchor `handleOrdersSuccess` @ OrdersList.tsx:2513 ✅ (grep matched)
- Task N.3 — assumption "8 call sites" → grep found **9** ⚠️ FINDING F1

**adjust-and-log** (self-corrected, no round-trip):
- Task N.6 anchor was at :4265 not :4296 (P7.2 edits shifted it) — corrected in place.

**stop-and-adjudicate findings:**

### F1 — [class] one-line title
- **Claim (plan):** <what the plan asserted>
- **Observed (evidence):** <grep output / file:line>
- **Why it matters:** <the failure it would cause>
- **Suggested resolution:** <optional>
```

Also put a `✅`/`⚠️` verdict mark on each reviewed task line in the checklist.

If there are any `stop-and-adjudicate` findings:
1. Set the `PROGRESS.md` status to **`⏸ Plan Amendment Needed`**.
2. Halt this phase. Independent later phases may **not** proceed past their own recon either.
3. Output the findings and the exact next step: *"Pre-flight found N blocking findings on Phase X. A strong-tier session must adjudicate them (amend the plan doc with a dated note, or overrule with rationale) before execution resumes."*

If everything passes (or only `adjust-and-log`): record the block, mark tasks ✅, proceed to execution.

---

## Adjudication (strong tier)

When resolving findings (in the planning session or any available strong session — this is plan *repair*, not certification; `/verify-implementation` still audits the trail):

1. For each finding: **amend the plan doc** with a dated note (`*(corrected YYYY-MM-DD per pre-flight review)*`), or **overrule** with a dated rationale.
2. **Append one line per finding to the docs repo's `Operations/PREFLIGHT-FINDINGS-LOG.md`** (create it if absent) — `date · ticket · class · origin-skill · one-liner · resolution`. This is part of resolving the finding, not a separate chore. (Do **not** log `adjust-and-log` drift individually — its rate is reported per ticket in the retro.)
3. Flip status back to `🔨 In Progress`; the executor resumes against the amended plan.

**Finding classes** (open taxonomy — add new ones as they appear): `ANCHOR-DRIFT`, `WRONG-ANCHOR`, `INCOMPLETE-ENUMERATION`, `FALSE-ASSUMPTION`, `STRUCTURE-VS-DATA`, `ENV-MISMATCH`. See the register header for definitions and the generator-first countermeasure rule.
