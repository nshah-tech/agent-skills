---
name: review-proposal
description: Consolidates Idea, Architecture, Design, Code Impact, and QA reviews into a single orchestrated gauntlet for feature proposals. Evaluates the proposal, flags blocking issues, auto-versions the document upon re-review, and handles handoff to task execution. Use when the user says "review proposal ACME-1823", "review design doc", or invokes "/review-proposal".
---

# Review Proposal

Run a comprehensive, multi-lens review over a technical proposal. This skill catches scope creep, missed edge cases, UI slop, code impact blind spots, and test gaps *before* any code is written.

## When to Use

- The user asks to "review proposal", "review ACME-1823"
- The user asks for an "architecture review" or "design review" of a plan
- The user explicitly invokes `/review-proposal`

---

## Workflow

### Step 1. Parse Command & Flags
Extract the ticket key (e.g., `ACME-1823`). Risk Classification (Lens 0) always runs regardless of flags — it's a cheap presence/plausibility check, not a heavy lens. Determine which of the remaining lenses to run based on the user's flags:
- `--full`: Run all 5 (Idea, Architecture, Design, Code Impact, QA). (Default if proposal is FULL template).
- `--quick`: Run only Architecture + Code Impact + QA. (Default if proposal is LITE template).
- `--skip-design`: Skip the Design lens (e.g., backend-only tasks).
- `--skip-idea`: Skip the Idea lens.
- `--re-review`: Only run lenses that had `BLOCKING` issues in the previous run.

### Step 2. Load the Proposal
1. Find the proposal file: `Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md`.
2. Read the entire document.

### Step 3. Pre-Review Evidence Pass
Before judging the proposal, gather enough source evidence to verify the stated impact. Do not rely only on the proposal author's list of affected systems.

1. Read any proposal sections named `Code Impact Review`, `Affected Code Surfaces`, `Reference Files & Patterns`, `Technical Architecture`, and `Implementation TODO`.
2. Search the relevant code repos for named entities, services, payload fields, endpoints, UI components, exports, background jobs, bulk actions, and shared utilities.
3. Inspect enough referenced files to map the data flow and downstream consumers. Prefer concrete paths over broad guesses.
4. Note shared contracts and compatibility risks, including API payloads, DTOs, entity fields, config keys, upload/import details, exported columns, cached state, and persisted JSON blobs.
5. Note explicit out-of-scope systems that must remain unchanged.

**Evidence standard**:
- For FULL proposals, review at least the primary source path plus likely downstream consumers across every repo the change can reach (backend, workers/background services, UI, plugins) when applicable.
- For LITE proposals, review the focused source path and at least one caller/consumer when applicable.
- If code is unavailable or not relevant, state that in the review log and judge the proposal against documented interfaces.

### Step 4. Update Sprint Doc Status (In Review)
1. Read `Sprints/<version>/<version>.md`.
2. Update the Status of `<TICKET_KEY>` to `🔍 In Review`.
3. Save the sprint doc.

### Step 5. Run Review Lenses
Evaluate the proposal against the active lenses.

#### Lens 1: Idea Review
- **Focus**: Scope, ambition, product wedge.
- **Criteria**: Is the scope too narrow? Does this deliver a "wow" moment? Is it an MVP that should actually be a V2? Is it gold-plating something that should be simple?
- **Flag**: Over-engineered components or missed opportunities for product impact.

#### Lens 0: Risk Classification Validation (runs before the lenses)
- **Criteria**: The proposal's `## Status & Classification` → `### Risk Classification` block (or the bug plan's `## Risk Classification`) must be present, and every dimension must be scored with a plausible reason — not left blank, not copy-pasted boilerplate that doesn't match the actual change.
- Cross-check one dimension against the evidence pass: if the proposal touches a workflow listed in the docs repo's `Operations/KNOWN-FAILURE-MODES.md` register, **Regression history** must be scored High (not left Low/Medium) for that reason.
- **Blocking conditions**: risk classification block missing entirely → `[BLOCKING]`. A dimension unscored → `[BLOCKING]`. A score that contradicts the evidence pass (e.g. Code surface scored Low while the proposal admits multi-repo changes) → `[BLOCKING]`.
- The **Overall Risk** (highest dimension) determines which gates apply downstream (see the project's workflow guide → risk tiers, if defined) — an unreliable score silently under-gates a risky change, so this must pass before the other lenses run.

#### Lens 2: Architecture Review
- **Focus**: Data flow, schema, edge cases, contracts.
- **Criteria**: Does the schema avoid cross-customer leakage? Are relationships correct (Nullable vs Non-nullable)? Is there a missing schema migration? Does the API payload match the UI needs? Are race conditions handled?
- **Flag**: Database lock risks, unhandled nulls, tight coupling.

#### Lens 3: Design Review
- **Focus**: UI/UX, interaction states, visual consistency.
- **Criteria**: Are Loading, Empty, and Error states explicitly designed? Does the component hierarchy match project standards? Is there any "AI Slop" (generic purple gradients, bubbly containers)?
- **Flag**: Missing empty states, ambiguous button actions, accessibility gaps.

#### Lens 4: Code Impact Review
- **Focus**: Blast radius, downstream consumers, shared contracts, compatibility, and out-of-scope protection.
- **Criteria**: Does the proposal identify all affected code paths discovered in the evidence pass? Are import/reprocess/reload flows, bulk actions, exports, reports, filters, popups, background jobs, and shared payload consumers considered when relevant? Does every affected compatibility feature have its own planned implementation decision and matching verification coverage? Are non-scope systems explicitly protected?
- **Flag**: Missing or shallow impact sections, hidden shared-payload consumers, unplanned downstream behavior changes, missing regression coverage, and ambiguous out-of-scope boundaries.

**Compatibility feature itemization rule**:
- Treat each affected user-visible or workflow-visible compatibility surface as its own Code Impact Compatibility Feature.
- Do **not** collapse multiple surfaces into one generic CIR item. If the evidence pass finds `initial import/rating`, `reprocess/reload`, `Bulk Update`, `export`, and `popup` impacts, each must receive its own `CIR-*` finding or note.
- Each `CIR-*` item must include:
  1. The compatibility feature name.
  2. Concrete source path(s) or documented interface(s).
  3. The compatibility risk or behavioral question.
  4. The required implementation decision.
  5. The required verification/regression coverage — **executable, not prose**. This field must name **either** an automated test (file path + case name) that `task-executor` is required to create, **or** an explicit manual QA script (numbered steps + expected result). Vague coverage like "covered by regression testing" or "will be tested" is a `[BLOCKING]` finding — the whole point is that `generate-progress-report` turns this field into a concrete atomic task, which it can't do from prose.
- If a surface is reviewed and no blocker remains, write it as `CIR-N: [NOTE]` or `CIR-N: [PASS]`; if coverage is missing, write it as `CIR-N: [BLOCKING]`.
- The Code Impact summary row may aggregate the result, but the Detailed Findings section must still contain one separate `CIR-*` item per compatibility feature.

**Blocking conditions**:
- FULL proposal has no `Code Impact Review` / `Affected Code Surfaces` equivalent section.
- Proposal changes a shared payload, DTO, entity, config, API, import/export flow, or UI state without identifying downstream consumers.
- An impacted compatibility feature is identified but does not have its own `CIR-*` item in the review log.
- An impacted compatibility feature is identified but has no corresponding Implementation TODO or verification case.
- Existing behavior can regress and the proposal does not include a regression test or explicit no-change verification.
- Out-of-scope systems are likely affected but not explicitly protected.
- A `CIR-*` item's verification coverage (field 5) is prose rather than a named automated test (path + case) or a numbered manual QA script.

**Finding IDs**:
- Use `CIR-1`, `CIR-2`, etc. for Code Impact Review findings.
- Code Impact blockers must prevent `✅ Approved` until resolved.

#### Lens 5: QA Review
- **Focus**: Test matrix, negative testing, Completeness Principle.
- **Criteria** (unit tests first): Is every logic change covered by a **unit test**, written in the same phase as the change? Where logic is inline in a React component, does the plan extract it into a pure `*.utils.ts` function first? Are the edge cases testable at unit level? Does the plan defer testing to later?
- **Integration / E2E**: Backend integration runs are allowed only when a real DB is genuinely required, and run **once as the ticket's final step**. Any E2E test must be justified as smoke-only (can't be proven by a unit test) and **read-only** (never writes to shared dev/staging data).
- **Flag**: "Happy path only" testing, missing edge case scenarios, **new E2E tests for logic that a unit test could prove** (finding, not blocker, unless the E2E writes to shared data — then `[BLOCKING]`), and any Jest test that would connect to a real database.

**Workflow-contract rule** (skip if the project has no `Operations/contracts/`):
- If the proposal touches a workflow that has a contract in the docs repo's `Operations/contracts/` (e.g. grid columns, export, imports, pricing rules), the proposal's `## Workflow Contracts` section must include that contract's checklist **verbatim and complete** (every point **per item** for per-item contracts such as a grid-column contract).
- Touched workflow with the contract **absent or incomplete** → `[BLOCKING]` (use finding IDs `QA-1`, `QA-2`, …).

**Known-failure-modes rule** (skip if the project has no register):
- Read the docs repo's `Operations/KNOWN-FAILURE-MODES.md`. For every registered class (KFM-*) whose workflow this proposal touches, confirm the proposal addresses it (via the relevant contract, fixture, or an explicit CIR item).
- A touched, registered failure class the proposal does **not** address → `[BLOCKING]`, citing the KFM row. This is how the register stops the pipeline re-learning the same class every sprint.

**Regression-matrix claim rule** (skip if the sprint has no matrix):
- Read the sprint's `Sprints/<version>/REGRESSION-MATRIX.md`. Determine which workflow **rows** this proposal touches (the matrix lists the product's user workflows — e.g. upload/parse, grid display, filters & record counts, edit/reprocess, bulk actions, export, integrations).
- Every touched row must be **claimed** by a `CIR-*` item in this proposal (or explicitly waived with a reason). A touched but **unclaimed** row is a declared untested seam → `[BLOCKING]`. On pass, note the claim so it can be stamped into the matrix's `Claimed by` column (`<TICKET> CIR-n`).

### Step 6. Append Review Log to Proposal
At the very bottom of the proposal document, append a `## Review Log` section. If one exists from a previous run, replace it or append a new dated run.

**Output Structure**:
```markdown
## Review Log (<Date>)

### Review Summary
| Lens | Status | Blocking Issues | Notes |
|---|---|---|---|
| Risk Classification | ✅ PASS | 0 | Overall: Low/Medium/High |
| Idea Review | ✅ PASS | 0 | ... |
| Architecture Review | ❌ BLOCKING | 1 | See A-1 |
| Design Review | ⚠️ PASS WITH NOTES | 0 | Minor UI tweak |
| Code Impact Review | ❌ BLOCKING | 1 | See CIR-1 |
| QA Review | ✅ PASS | 0 | ... |

**Overall Verdict**: ❌ BLOCKING / ✅ PASS

### Detailed Findings

#### A-1: [BLOCKING] <Issue Title>
> <Detailed description of the problem and the exact code/architecture risk>.
> **Fix**: <Specific instruction on how the user or agent must fix it>.

#### CIR-1: [BLOCKING] <Issue Title>
> <Detailed description of the impacted source path, downstream consumer, or compatibility risk>.
> **Fix**: <Specific instruction for adding/adjusting the code-impact section, implementation task, or regression coverage>.

#### CIR-2: [NOTE] <Compatibility Feature Title>
> **Source path(s)**: `<repo/path/file.ts>`.
> **Compatibility consideration**: <What existing behavior or consumer must remain correct>.
> **Implementation decision**: <What the proposal requires for this surface>.
> **Verification coverage**: <Which TODO/test case proves this surface is safe>.

#### D-1: [NOTE] <Issue Title>
> <Minor feedback that doesn't block execution>.
```

### Step 7. Auto-Versioning (For `--re-review` fixes)
If this is a `--re-review` and the user/agent has modified the proposal to fix previous `BLOCKING` issues:
1. Ensure the proposal's `Appendix B: Revision History` is updated.
2. Add a new `Rev` entry documenting what was changed to pass the review.

### Step 8. Final Sprint Status Update
- If the Overall Verdict is **✅ PASS**:
  1. Read `Sprints/<version>/<version>.md`.
  2. Update the Status of `<TICKET_KEY>` to `✅ Approved`.
  3. Save the sprint doc.
- If any Code Impact Review finding is still `BLOCKING`, do **not** update the status to `✅ Approved`.

### Step 9. Handoff to User
- If **BLOCKING**:
  > *"Review complete. Found N blocking issues. Please resolve them in the proposal (or ask me to fix them), then run `/review-proposal <TICKET> --re-review`."*
- If **PASS**:
  > *"All reviews passed and status updated to Approved! Run `/generate-progress-report <TICKET>` to create the execution checklist."*
- **Session Bookmark**:
  > *"Session complete. To resume later, run `/workflow-status <version>`."*
