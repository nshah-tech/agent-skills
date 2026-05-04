---
name: review-proposal
description: Consolidates Idea, Architecture, Design, and QA reviews into a single orchestrated gauntlet for feature proposals. Evaluates the proposal, flags blocking issues, auto-versions the document upon re-review, and handles handoff to task execution. Use when the user says "review proposal ACME-1823", "review design doc", or invokes "/review-proposal".
---

# Review Proposal

Run a comprehensive, multi-lens review over a technical proposal. This skill catches scope creep, missed edge cases, UI slop, and test gaps *before* any code is written.

## When to Use

- The user asks to "review proposal", "review ACME-1823"
- The user asks for an "architecture review" or "design review" of a plan
- The user explicitly invokes `/review-proposal`

---

## Workflow

### Step 1. Parse Command & Flags
Extract the ticket key (e.g., `ACME-1823`). Determine which lenses to run based on the user's flags:
- `--full`: Run all 4 lenses (Idea, Architecture, Design, QA). (Default if proposal is FULL template).
- `--quick`: Run only Architecture + QA. (Default if proposal is LITE template).
- `--skip-design`: Skip the Design lens (e.g., backend-only tasks).
- `--skip-idea`: Skip the Idea lens.
- `--re-review`: Only run lenses that had `BLOCKING` issues in the previous run.

### Step 2. Load the Proposal
1. Find the proposal file: `Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md`.
2. Read the entire document.

### Step 3. Update Sprint Doc Status (In Review)
1. Read `Sprints/<version>/<version>.md`.
2. Update the Status of `<TICKET_KEY>` to `🔍 In Review`.
3. Save the sprint doc.

### Step 4. Run Review Lenses
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

#### Lens 4: QA Review
- **Focus**: Test matrix, negative testing, Completeness Principle.
- **Criteria**: Are unit, integration, and E2E tests specified? Are the edge cases testable? Does the plan include 100% test coverage or does it defer testing to later?
- **Flag**: "Happy path only" testing, missing edge case scenarios.

### Step 5. Append Review Log to Proposal
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
| QA Review | ✅ PASS | 0 | ... |

**Overall Verdict**: ❌ BLOCKING / ✅ PASS

### Detailed Findings

#### A-1: [BLOCKING] <Issue Title>
> <Detailed description of the problem and the exact code/architecture risk>.
> **Fix**: <Specific instruction on how the user or agent must fix it>.

#### D-1: [NOTE] <Issue Title>
> <Minor feedback that doesn't block execution>.
```

### Step 6. Auto-Versioning (For `--re-review` fixes)
If this is a `--re-review` and the user/agent has modified the proposal to fix previous `BLOCKING` issues:
1. Ensure the proposal's `Appendix B: Revision History` is updated.
2. Add a new `Rev` entry documenting what was changed to pass the review.

### Step 7. Final Sprint Status Update
- If the Overall Verdict is **✅ PASS**:
  1. Read `Sprints/<version>/<version>.md`.
  2. Update the Status of `<TICKET_KEY>` to `✅ Approved`.
  3. Save the sprint doc.

### Step 8. Handoff to User
- If **BLOCKING**:
  > *"Review complete. Found N blocking issues. Please resolve them in the proposal (or ask me to fix them), then run `/review-proposal <TICKET> --re-review`."*
- If **PASS**:
  > *"All reviews passed and status updated to Approved! Run `/generate-progress-report <TICKET>` to create the execution checklist."*
- **Session Bookmark**:
  > *"Session complete. To resume later, run `/workflow-status <version>`."*
