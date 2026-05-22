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
Extract the ticket key (e.g., `ACME-1823`). Determine which lenses to run based on the user's flags:
- `--full`: Run all 5 lenses (Idea, Architecture, Design, Code Impact, QA). (Default if proposal is FULL template).
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
- For FULL proposals, review at least the primary source path plus likely downstream consumers across backend, microservice, and UI when applicable.
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
  5. The required verification/regression coverage.
- If a surface is reviewed and no blocker remains, write it as `CIR-N: [NOTE]` or `CIR-N: [PASS]`; if coverage is missing, write it as `CIR-N: [BLOCKING]`.
- The Code Impact summary row may aggregate the result, but the Detailed Findings section must still contain one separate `CIR-*` item per compatibility feature.

**Blocking conditions**:
- FULL proposal has no `Code Impact Review` / `Affected Code Surfaces` equivalent section.
- Proposal changes a shared payload, DTO, entity, config, API, import/export flow, or UI state without identifying downstream consumers.
- An impacted compatibility feature is identified but does not have its own `CIR-*` item in the review log.
- An impacted compatibility feature is identified but has no corresponding Implementation TODO or verification case.
- Existing behavior can regress and the proposal does not include a regression test or explicit no-change verification.
- Out-of-scope systems are likely affected but not explicitly protected.

**Finding IDs**:
- Use `CIR-1`, `CIR-2`, etc. for Code Impact Review findings.
- Code Impact blockers must prevent `✅ Approved` until resolved.

#### Lens 5: QA Review
- **Focus**: Test matrix, negative testing, Completeness Principle.
- **Criteria**: Are unit, integration, and E2E tests specified? Are the edge cases testable? Does the plan include 100% test coverage or does it defer testing to later?
- **Flag**: "Happy path only" testing, missing edge case scenarios.

### Step 6. Append Review Log to Proposal
At the very bottom of the proposal document, append a `## Review Log` section. If one exists from a previous run, replace it or append a new dated run.

**Output Structure**:
```markdown
## Review Log (<Date>)

### Review Summary
| Lens | Status | Blocking Issues | Notes |
|---|---|---|---|
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
