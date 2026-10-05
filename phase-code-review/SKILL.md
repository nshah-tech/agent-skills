---
name: phase-code-review
description: Reviews the code a phase actually produced, before the user commits it. Verifies the execution record's claims against the diff, hunts over-engineering and duplication, checks tests actually discriminate, then fixes only what the user approves and syncs the tracker. Use when the user says "review Phase N", "the task executor has executed Phase N", "review my changes before I commit", or invokes "/phase-code-review".
---

# Phase Code Review

The gate between `task-executor` finishing a phase and the user committing it. The executor reports its own work, so the execution record is a **claim, not evidence**. This skill re-derives the truth from the diff, names what is over-engineered for a V1, and leaves the tracker honest.

> The user reviews every diff themselves. Your job is to make that review cheap: a short, ranked list of real findings with file paths and concrete fixes — not a restatement of the diff.

This skill is the canonical protocol; `task-executor` references it at each phase end, and `/phase-code-review` invokes it standalone.

## When to Use

- **The common path**: right after `task-executor` reports a phase complete, before any commit.
- **Standalone**: "review my changes before I commit" on any uncommitted work.
- Do not commit or push unless the project's rules say the agent commits. Present findings, fix on approval, stop.

---

## Step 1 — Establish the real boundary

Do not trust the phase number in the prompt. Derive what changed:

- `git status --short` and `git diff --stat` **in every affected repo** (docs repo plus each code repo the ticket touches). Work is often already staged, or the previous phase is already committed.
- `git log --oneline -3` per repo to see what landed since the last review.
- Read the phase's task rows **and** its execution record in `PROGRESS.md`. Those are the claims you are about to test.

## Step 2 — Verify the claims yourself

- **Run the whole affected folder, not the executor's focused list** (e.g. `npx jest src/modules/<module>`). A broken spec can hide for several phases behind hand-picked runs because its mock never got a new method. Stay scoped to the module — never an unscoped suite unless the project says it is safe.
- Use the pinned runtime for each repo (`nvm use`, or whatever the repo pins).
- `tsc --noEmit` catches what jest does not. Check what the repo's `tsconfig.json` `include`s — if test files are excluded, they are only type-checked when the suite runs.
- Any failure: decide **pre-existing or introduced** before reporting it, and prove which (`git show HEAD:<file>` and compare the failing line).
- Never write "tests pass" for something you did not run. An unexecuted spec is "written, not executed".

## Step 3 — The review lenses, in priority order

1. **Contract drift.** Does the code still obey the adjudicated decisions in the proposal? Code that drifts from a decision is wrong code — report the drift, do not re-open the decision.
2. **Over-engineering for a V1.** Usually the highest-yield lens. See the catalogue below.
3. **Duplication of something that already exists.** Before accepting a new helper, grep for one (response unwrappers, state contracts, enum literals are common repeats).
4. **Built-but-never-wired.** Values fetched and discarded, options nothing passes, state set and never read. Audit both directions: wire it or delete it.
5. **Test quality.** Does each new test *discriminate*? A test with no negative or baseline case passes even when the feature is deleted. Watch for assertions weakened to make a test green, and for a mock loosened (`mockImplementationOnce` → `mockImplementation`) to absorb an extra call the code should not be making — that is a design smell wearing a test costume.
6. **Scope creep and churn.** Unrelated reformatting, drive-by import removals, renames outside the ticket. Unrelated gaps become their own ticket.
7. **Stale comments.** Comments describing removed UI or the old design. Add the *why* where a future reader would re-introduce the bug.
8. **Release coupling.** Does this phase break the app until a later phase ships? Say so loudly and name the repos that must land together.

### Over-engineering catalogue

| Smell | Ask |
|---|---|
| Row locks, `FOR UPDATE`, extra transactions | Does V1 need serialization, or is last-write-wins acceptable and documented? |
| A second transaction to "stage" a write | Can it commit with the work it belongs to? |
| A transaction manager passed from service into repository | Can the repository's own (scoped) finder do it? |
| A global pipe/guard/interceptor for one module's rule | Is it already handled (e.g. validation `whitelist: true` strips unknown fields), and does it belong on the route instead? |
| Duplicate reads: a store/redux dispatch **and** a direct API call | One of them is usually dead. Which result is actually consumed? |
| Full-matrix test permutations | Are the dimensions independent? Two cases usually cover every branch. |
| A defensive branch for a state the type system forbids | Delete it, or fix the type. |

### Query and call-pattern pass

When the phase touches data access: independent reads awaited back-to-back in a **read-only** path should run under `Promise.all`. **Never** inside a transaction — that manager is bound to one connection, where parallel queries serialize or fail. Also check for N+1 in per-row loops, confirm existing caches still key correctly, and confirm every query keeps the project's tenant/ownership scoping.

## Step 4 — Report

Rank by consequence, not by file order. Four buckets, each finding with `file:line` and a concrete fix:

- **Verified** — what you actually ran and what passed.
- **Should fix** — correctness, contract drift, evidence gaps. Include the failure scenario.
- **Worth simplifying** — over-engineering and duplication, with the smaller alternative.
- **Fine as is** — things that look wrong but are not, so the user does not re-check them.

End with one question offering to make the fixes. Do not fix first and report after.

## Step 5 — Fix on approval, then re-verify

- Make only the approved fixes. Use the editor tool, never shell rewrites (`sed`, heredocs), so the diff is reviewable. Bulk row deletion in a tracker is the one exception — say plainly that you used a filter.
- Re-run the folder suite, `tsc --noEmit`, scoped `prettier --write` on changed files only, `eslint` on changed files, and `git diff --check`.
- Report remaining lint errors as **pre-existing** only after proving it against HEAD.

## Step 6 — Leave the tracker honest

- Add a **`#### Phase N Review Record (<date>, <model>)`** block to `PROGRESS.md`: what was fixed and why, what was withdrawn, what is still open, and the checks with their real numbers.
- **Reopen tasks whose evidence does not exist.** If a task claims tests that were never written, flip it to `[ ]` with the reason and correct the completion count. Counts must reconcile: `grep -c "^- \[x\]"` + `grep -c "^- \[ \]"` = the header total.
- If the review changed a decision, sync the **proposal** (governing amendment + revision-history entry), and the **epic** and sprint doc where they restate the decision — epics carry decisions, not history.
- Present the diff and stop.

---

## Evidence rules (non-negotiable)

- A checkbox is not evidence. Record the command, the runtime and the counts.
- "Focused suite passed" is not "the suite passed".
- Running existing tests is not the same as adding the case a task asked for.
- If you could not run something (no DB authority, no fixture), say so in the same sentence as the artifact: *"written, not executed"*.
- Pre-existing breakage gets reported as pre-existing, with the proof — and fixed only if the user asks.
