---
name: product-doc-sync
description: After a feature ships to prod, syncs its living current-state doc in Wiki/Features/. Feature-oriented (not per-ticket) and update-in-place (merge, not regenerate). Keeps rationale/history in the Sprint. Use when the user says "update wiki", "sync product doc", or invokes "/product-doc-sync".
---

# Product Doc Sync

Keeps `Wiki/Features/<Feature>.md` a faithful description of what a feature does **today**, after it ships. This is the Wiki side of the **Wiki = current state, Sprint = evolution** rule (see `CONTRIBUTING.md` → "Wiki vs Sprint"). It does **not** copy decision history or rationale into the Wiki — that stays in the Sprint, reachable via backlinks.

## Core Principles

1. **Feature-oriented, not ticket-oriented.** Many tickets build one feature (e.g. eight sub-tickets → "Billing Workspace"). There is **one** living doc per feature. Map the ticket to its feature via its epic/parent or shared tag before doing anything.
2. **Update-in-place, not regenerate.** Merge the shipped change into the existing doc — add new behavior, revise changed behavior, remove retired behavior. Never blow away hand-written content.
3. **Current-state only.** The Wiki says what the feature does now. No "we used to…", no alternatives considered, no AD rationale. That lives in the Sprint.
4. **Ship-gated.** Only sync behavior that has merged to prod. If the ticket has not shipped, warn and stop.

## When to Use

- The user asks to "update the wiki for ACME-1823" / "sync product docs"
- The user invokes `/product-doc-sync`
- Final documentation step after a feature (or a meaningful slice of one) reaches prod

---

## Workflow

### Step 1. Resolve the feature (not just the ticket)
1. Read the ticket's source doc:
   - Feature ticket → proposal `Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md`.
   - Bug ticket → plan `Sprints/<version>/bugs/<TICKET_KEY>-<ShortName>.md`. Only proceed for bugs classified **`behavior`** in the dashboard `## Bug Fixes` table; `internal` bugs need no Wiki update — stop and say so.
   - Hotfix → plan `Sprints/<version>/hotfixes/<TICKET_KEY>-<ShortName>.md`, tracked in the dashboard `## Hotfixes` table. Same rule: only `behavior` hotfixes need a Wiki update.
2. Determine the **feature** the ticket belongs to — via its Jira epic/parent, the proposal's `Epic:` header, or shared tag. For an epic decomposed into sub-tickets, the feature is the epic (e.g. ACME-1532 → `Wiki/Features/BillingWorkspace.md`). A bug or hotfix maps to whichever existing feature doc it corrects.
3. Confirm the change has **merged to prod** (ask the user if unclear). If not shipped, stop and report: current-state docs are only written for shipped behavior.
   - **Timing note**: a normal ticket ships when the version merges to prod. A **hotfix is in prod immediately** — sync it right after its deploy, don't wait for the version release. After syncing a hotfix, flip **Wiki synced?** to ✅ in the dashboard `## Hotfixes` row.

> Tip: to sweep a whole shipped sprint, read the dashboard's `## Tickets`, `## Bug Fixes` (behavior-only), and `## Hotfixes` (behavior-only) tables and sync each affected feature doc once.

### Step 2. Gather current-state sources
1. Read the existing `Wiki/Features/<Feature>.md` if it exists (this is what you'll update).
2. Read the shipped proposal(s) and the epic's `DECISION-LOG.md` to identify **what behavior changed** — but extract only the resulting behavior, not the reasoning.
3. When behavior is ambiguous, inspect the actual shipped code in the relevant repo rather than trusting the proposal's pre-build intent.

### Step 3. Merge the change into the living doc
Update the existing doc in place, current-state only, following the `Wiki/Features/` template in `CONTRIBUTING.md`:
- `## Description`, `## User Flow`, `## Business Logic`, `## Technical Details` — revise the affected sections to match current behavior; add sections for genuinely new capability; delete descriptions of removed behavior.
- Do **not** paste rationale, alternatives, or review findings. Do **not** narrate the change inside the body.
- If the doc does not exist yet (first ship of a new feature), create it from the template.

### Step 4. Add the Changed In row + backlinks
1. Append one row to the doc's `## Changed In` table: `| <version> | <TICKET_KEY> | <one-line what changed> | [proposal](../../Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md) |`.
2. Ensure `## Backlinks` links the sprint proposal, epic tracker, and any relevant ADRs.

### Step 5. Tags & indexes
1. Ensure the doc has a PascalCase tag line under the title (`CONTRIBUTING.md` rules).
2. If this is a new feature doc, add it to `Wiki/_index.md` Features table.
3. If you introduce a new tag, update `tags.md`.

### Step 6. Update sprint status
1. Read `Sprints/<version>/<version>.md`.
2. Feature/bug → set the `<TICKET_KEY>` row status to `📘 Wiki Done` in `## Tickets` / `## Bug Fixes`.
3. Hotfix → flip **Wiki synced?** to ✅ in the `## Hotfixes` row (and confirm **Back-merged?** is not still ❌ — if it is, warn the user the fix will be reverted at release).

### Step 7. Present to user
> *"Synced `Wiki/Features/<Feature>.md` with the current behavior from `<TICKET_KEY>` and added a Changed In row. Rationale/history remain in the sprint. Sprint status → 📘 Wiki Done."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*

---

## Notes

- Keep this skill and `feature-docs` consistent — both write `Wiki/Features/`. Both must honor current-state-only + Changed In + feature-oriented mapping.
- For rigorous changes to this skill (evals/benchmarks), use the global `skill-creator` skill.
