---
name: jira-feature-architect
description: Fetches a Jira ticket, researches the relevant codebase, and produces a detailed feature proposal document with a companion progress tracker — all saved to the S2Q Documentation repository. Use this skill whenever the user asks to "create a proposal", "write a feature proposal", "proposal for ticket X", "plan a feature for ACME-XXXX", "design doc for this ticket", or any request that involves reading a Jira ticket and producing a structured technical proposal document (not an implementation plan). Also trigger when the user says "propose", "feature doc", "write up a proposal", "proposal doc", or explicitly invokes "/jira-feature-architect". This skill produces TWO files: a Proposal doc and a Progress tracker, both written to the documentation repository.
---

# Jira Feature Architect

Fetch a Jira ticket, distill it into a clear summary, deeply research the affected codebase, and produce a **technical proposal document** with a companion **progress tracker** — saved to the S2Q Documentation repository under `Sprints/<version>/`.

## When to Use

- The user asks to "create a proposal", "write a feature proposal", "proposal for ticket X"
- The user says "design doc for this ticket", "propose", "feature doc", "write up a proposal"
- The user wants a **planning/design document** from a Jira ticket (NOT an implementation plan for immediate execution)
- The user explicitly invokes `/jira-feature-architect`

---

---

## Config File: `.jira.json`

This skill reads workspace configuration from a `.jira.json` file at the **root of the current repository**. This file should be committed to the repo so every developer in the project gets the right defaults automatically.

### Schema

```json
{
  "cloudId": "your-company.atlassian.net",
  "defaultProject": "PROJ",
  "displayName": "Your Company / Project Name"
}
```

| Field | Required | Description |
|---|---|---|
| `cloudId` | ✅ | The Atlassian site URL (e.g. `acme.atlassian.net`). Used as the `cloudId` in every MCP call. |
| `defaultProject` | ✅ | Default project key prefix (e.g. `ACME`, `PROJ`). Used to expand bare ticket numbers like `1973` → `PROJ-1973`. |
| `displayName` | optional | Human-readable label shown in proposal headers (e.g. `"Acme – Backend API"`). |

---

## Output Structure

This skill produces files in the `documentation` repository (which is its own standalone repo). Locate the documentation repo root by checking the user's workspace URIs — it will be the workspace mapped to `SpeedToQuote/documentation` or similar.

Proposals live **inside their sprint folder**. The skill produces **two files** per proposal, and updates the shared **tags index** at the repo root:

```
tags.md                                  ← Tag index (root-level, shared across all docs)
Sprints/
└── v2.16.0/
    └── <TICKET_KEY>-<ShortName>/
        ├── <TICKET_KEY>-<ShortName>.md   ← Technical Proposal
        └── <TICKET_KEY>-PROGRESS.md      ← Progress Tracker
```

**Example**: For ticket `S2Q-1849` about "Historical Rate Matrix" in sprint v2.15.0:
```
Sprints/
└── v2.15.0/
    └── S2Q-1849-HistoricalRateMatrix/
        ├── S2Q-1849-HistoricalRateMatrix.md
        └── S2Q-1849-PROGRESS.md
```

**Naming rules**:
- `<ShortName>` is a PascalCase slug derived from the ticket summary (e.g., `MexicoSupport`, `HistoricalRateMatrix`, `UploadHeartbeat`). Keep it concise — 1–3 words.
- The folder name combines the ticket key and short name.
- Use relative paths from the documentation repo root (e.g., `Sprints/<version>/<TICKET_KEY>-<ShortName>/`).

**Sprint version**: The user MUST specify which sprint the proposal belongs to. If not provided, ask:
> Which sprint version does this proposal belong to? (e.g., `v2.16.0`)

---

## Tag System

Every proposal uses **Obsidian-style tags** for cross-proposal discovery. Tags are placed directly under the proposal title.

### Tags in Proposals

Add a tag line immediately after the `# Proposal:` title in every proposal document:

```markdown
# Proposal: S2Q-1849: Historical Rate Matrix (Technical Proposal)

#Historical #RFP #PowerLane #RateMatrix #PricingStrategy #Microservice #SQS
```

**Tag naming rules**:
- Use `#PascalCase` — one word per tag, no spaces (e.g., `#PowerLane`, not `#Power Lane`)
- Include tags for: affected entities, services, UI areas, feature domains, and infrastructure
- Aim for 4–8 tags per proposal
- Common tag categories:

| Category | Example Tags |
|---|---|
| **Entity** | `#PowerLane`, `#RFP`, `#Historical`, `#Zone`, `#ZipCode` |
| **Service** | `#Microservice`, `#S2QService`, `#DistanceService` |
| **UI Area** | `#PricingStrategy`, `#Dashboard`, `#ImportWizard`, `#ZoneManagement` |
| **Feature** | `#RateMatrix`, `#MexicoSupport`, `#BulkGenerate`, `#Upload` |
| **Infrastructure** | `#SQS`, `#Migration`, `#Cron`, `#S3` |

### `tags.md` — Tag Index

Maintain the **root-level** `tags.md` file (at the documentation repo root, NOT inside a subfolder). This file indexes all tags with their descriptions and which documents use them. **Update this file every time a new proposal is created.**

**When creating a new proposal**: Read `tags.md` first. If your proposal's entities/services match existing tags, you have potential cross-proposal overlap.

---

## Proposal Workflow

### Step 1. Load Config

Before doing anything else, check for the config file:

```bash
cat .jira.json 2>/dev/null || echo "NOT_FOUND"
```

- **If found:** parse `cloudId`, `defaultProject`, and `displayName` from it. Silently proceed.
- **If not found:** inform the user:
  > No `.jira.json` found in the current directory. You can run **"jira-config-init"** to create one, or provide the Atlassian site URL now (e.g. `acme.atlassian.net`).

  If the user provides the `cloudId` inline (e.g. from a pasted URL), use it for this session only — do not create a config file unless asked.

### Step 2. Extract the Ticket Key

Parse the ticket key from the user's message. It may appear as:
- A bare key like `ACME-1973`
- Embedded in a URL like `https://company.atlassian.net/browse/PROJ-42`
- A bare number like `1973` — expand using `defaultProject` from config → `ACME-1973`
- Referenced casually like "that 1973 ticket" (ask for clarification if ambiguous)

### Step 2a. Cross-Proposal Awareness

Before creating a new proposal, scan existing proposals for related or conflicting work using a **two-pass tag-first search**:

#### Pass 1: Tag Scan (fast)

Read the tag index file from the documentation repo root:
```bash
cat tags.md
```

- Identify which existing tags match the new ticket's entities, services, and feature areas.
- If matching tags are found, note which proposals use them — these are your overlap candidates.
- If `tags.md` doesn't exist yet, create it during Step 6 with the new proposal's tags.

#### Pass 2: Focused Search (only if tag matches found)

For each overlap candidate identified in Pass 1:

1. **Read the candidate proposal's tag line** (line 3 of the `.md` file) to confirm overlap.
2. **Use `grep_search`** on the candidate proposal for:
   - Entity names mentioned in the new ticket (e.g., `PowerLaneEntity`, `RfpEntity`)
   - Shared file paths that both proposals might modify
   - The new ticket key itself (it may already be referenced)
3. **Read the candidate's Implementation TODO** to understand what's in-flight if overlap is significant.

#### Flag Conflicts

If overlap is found, add a section to the new proposal:

```markdown
## Related Proposals

> Existing proposals that touch overlapping areas of the codebase.
> Discovered via shared tags: #PowerLane, #Historical

| Proposal | Shared Tags | Overlap | Risk |
|---|---|---|---|
| S2Q-1823-MexicoSupport | #ZipCode #Zone | Both modify `zip.ts` and `location.ts` | Merge conflict on location pipeline |
| S2Q-1849-HistoricalRateMatrix | #PowerLane | Shares `PowerLaneEntity` | Schema migration ordering |
```

**Skip this step** only if `tags.md` doesn't exist and the `Sprints/` directory has no proposal subfolders.

### Step 3. Fetch the Ticket from Jira

Use the `mcp_atlassian-mcp-server_getJiraIssue` tool to retrieve the ticket details.

- Set `cloudId` to the value loaded from config (or provided by the user)
- Request `markdown` as the `responseContentFormat`
- Extract these key fields:
  - **Summary** (title)
  - **Description** (the full issue body)
  - **Issue Type** (Bug, Story, Task, Epic, etc.)
  - **Priority**
  - **Status**
  - **Assignee** / **Reporter**
  - **Labels / Components** (if present)
  - **Linked Issues** (related context)
  - **Comments** (teammate context, stakeholder feedback, requirements clarification)
  - **Attachments** (screenshots, mockups, data files mentioned)
  - **Sprint** (if assigned)

### Step 3a. Linked Ticket Auto-Fetching

After fetching the main ticket, automatically fetch ALL linked issues to gather full context:

1. **Extract linked issue keys** from the main ticket's `issuelinks` field (subtasks, blocks, is-blocked-by, relates-to, etc.).
2. **Fetch each linked ticket** using `mcp_atlassian-mcp-server_getJiraIssue` with `responseContentFormat: markdown`.
3. **Classify each linked ticket** by relationship type:

| Relationship | How to Use |
|---|---|
| **Subtask** | These define sub-scope — incorporate their requirements into the proposal |
| **Blocks / Is blocked by** | Note as dependencies in the proposal |
| **Relates to** | Check for shared context, prior art, or stakeholder decisions |
| **Duplicate** | Skip — but note in proposal if requirements diverge |

4. **Extract actionable context** from each linked ticket:
   - Additional requirements not in the main ticket's description
   - Stakeholder decisions or design feedback in comments
   - Attachments (CSVs, mockups, PPTXs) that inform the design
   - Resolution details (if the linked ticket is already resolved — what was decided?)

5. **Summarize in the proposal** — Add a "Related Tickets" section:

```markdown
## Related Tickets

| Ticket | Type | Relationship | Key Context |
|---|---|---|---|
| [S2Q-2020](link) | Subtask | Subtask of S2Q-1823 | Adds 2-letter MX state aliases, processing toggle |
| [S2Q-2036](link) | Subtask | Subtask of S2Q-1823 | Border crossing, multi-leg distance, DAT toggle |
```

**Performance note**: Fetch linked tickets in parallel where possible. If there are more than 10 linked tickets, fetch only the first 10 and note the remainder.

### Step 3b. Attachment Analysis

After fetching the ticket and linked tickets, analyze any attachments that could inform the proposal:

1. **Identify relevant attachments** from the main ticket and linked tickets. Look for:
   - **CSV files** — Data samples, mapping files, test data (e.g., `MexicoAliasList.csv`)
   - **PPTX / PDF files** — UI walkthroughs, stakeholder presentations, design mockups
   - **Images** — Screenshots, wireframes, error screenshots
   - **Code snippets** — Patches, configuration files

2. **Download and analyze** relevant attachments:
   - **CSVs**: Check the file size first. If the CSV has **≤ 30 rows**, read the entire file. If it has **> 30 rows**, read only the **first 5 rows** (header + 4 data rows) to understand column structure and data patterns — do NOT read the entire file. Always summarize the schema, row count, and notable patterns in the proposal.
   - **PPTXs / PDFs**: Note their existence and summarize the content described in ticket comments. If the attachment content is referenced in comments, extract the key points.
   - **Images**: Note them as visual references. If they show UI mockups, describe the layout in the UI/UX section.

3. **Incorporate findings** — Attachment analysis often reveals:
   - Data edge cases (special characters, encoding, deduplication needs)
   - UI expectations from stakeholders (layout, column placement)
   - Business rules not captured in the ticket description
   - Test data that can be used for acceptance criteria

4. **Reference in the proposal** — Cite attachments by filename:
   > Data structure derived from `MexicoAliasList.csv` (attached to S2Q-2020).
   > UI layout based on `S2Q Mexico UI walk through.pptx` (attached to S2Q-2036, Slides 2–7).

**Skip this step** if the ticket has no attachments, or if all attachments are screenshots of the bug itself (not design artifacts).

### Step 4. Summarize the Feature

Write a clear, concise summary (3–6 sentences) that answers:

1. **What is the feature?** — Describe the capability being added in plain English.
2. **What is the current state?** — What exists today and what gap does this fill.
3. **What is the business impact?** — Who benefits and why this matters.
4. **Scope context** — Any specific requirements, constraints, or stakeholder feedback from the ticket or comments.

Avoid copying the Jira description verbatim — distill and clarify it. If the ticket is vague or missing details, explicitly call out what is missing and ask the user using the **AskUserQuestion** format. 

**MANDATORY**: Never ask open-ended questions when the Jira ticket lacks context. Use the `AskUserQuestion` format to reduce cognitive load:
1. **Re-ground**: Briefly state what is missing or ambiguous.
2. **Simplify**: Explain it in plain English (no jargon).
3. **Recommend**: Recommend the most *complete* option.
4. **Options**: Provide A/B/C options.
*(e.g., A) Use Redis caching [Recommended: scales best], B) Use in-memory caching [Faster to build], C) No caching).*

### Step 4a. Classify Scope & Select Template Variant

After summarizing, classify the feature's scope to determine which template variant to use. This ensures small tasks don't get buried in unnecessary sections, and large features get adequate coverage.

**Classification criteria** (these same criteria are included in the proposal itself — see `Status & Classification` section in the template):

| Signal | Points to LITE | Points to FULL |
|---|---|---|
| Issue Type | Task, Bug | Epic, Story |
| Description length | < 200 words | > 500 words, or has sub-requirements |
| Linked tickets | 0–1 | 2+ subtasks or related tickets |
| Systems affected | 1 repo (backend-only or frontend-only) | 2+ repos (full-stack) |
| Schema changes | None | New entities, columns, or migrations |
| UI changes | None or minor tweak | New page, tab, or component |
| Estimated tasks | < 10 | 10+ |

**LITE template** — For focused, single-system changes (e.g., S2Q-1946 UploadHeartbeat):
- Collapse UI/UX Design to a single paragraph (or "backend-only" note)
- Collapse Technical Architecture to a data flow summary (no ASCII diagram required)
- Edge Cases: 2–4 entries minimum (vs 6+ for FULL)
- Fewer implementation phases (typically 2–3)
- No Related Proposals section (unless overlap found in Step 2a)

**FULL template** — For cross-cutting, multi-system features (e.g., S2Q-1823 MexicoSupport):
- All ★ mandatory sections expanded with full detail
- ASCII diagrams for both UI layout and system architecture
- Edge Cases: 6+ entries covering all categories
- Multiple implementation phases (typically 5+)
- Related Proposals section included if overlaps exist
- Appendix C (Post-Implementation Feedback) placeholder included

**Default**: When in doubt, use FULL. It's easier to trim than to add later.

Announce the classification to the user:
> 📋 **Template**: Using **FULL** template — this feature spans 3 repos with schema changes and new UI.
> 📋 **Template**: Using **LITE** template — this is a focused backend task with no UI changes.

### Step 5. Research the Codebase

Investigate the relevant source code to understand the current architecture and what needs to change:

1. **Identify affected systems** — Use `grep_search` to locate the entities, services, modules, and UI components related to the feature.
2. **Understand existing patterns** — Read relevant files with `view_file` to understand how similar features are built (entity patterns, service patterns, controller patterns, UI component patterns).
3. **Map the data flow** — Trace how data moves through the system for related features.
4. **Identify integration points** — External services, shared libraries, database entities, frontend components that will be touched.
5. **Note constraints** — Existing patterns that must be followed, files that must NOT be created in new directories, enum values that must match existing conventions.
6. **See Something, Say Something (Tech Debt Radar)** — While researching the codebase, actively look for deprecated patterns, security risks, or "slop" in the files you are reading. You will flag these in the proposal.

### Step 5a. The Completeness Principle (Boil the Lake)

**MANDATORY**: Follow the Completeness Principle. The AI-assisted marginal cost of writing tests, handling edge cases, and building full features is near-zero. Your proposed architecture MUST include 100% test coverage, full error-path handling, and strict typing. Never propose a "v1 shortcut" or minimum viable product that defers edge cases to a later ticket unless explicitly requested by the user.

Read at least 3–5 relevant files. The quality of the proposal depends on understanding the existing architecture deeply.

### Step 6. Create the Technical Proposal Document

Write the proposal to the documentation repository. The proposal should follow this structure. **All sections marked ★ are MANDATORY** — include them in every proposal. Other sections should be included when relevant to the feature.

```markdown
# Proposal: <TICKET_KEY>: <Feature Name> (Technical Proposal)

#Tag1 #Tag2 #Tag3 #Tag4 #Tag5

## 1. Objective ★
One paragraph describing the feature goal and what it enables across the platform.

## Status & Classification ★
**Reference Jira**: [<TICKET_KEY>](https://<cloudId>/browse/<TICKET_KEY>)
**Sprint**: <sprint if known>
**Priority**: <priority>
**Reporter**: <reporter name>
**Template**: FULL / LITE

### Scope Classification
| Signal | Value | Verdict |
|---|---|---|
| Issue Type | <Story/Task/Epic/Bug> | LITE / FULL |
| Description | <word count> words | LITE / FULL |
| Linked tickets | <count> | LITE / FULL |
| Systems affected | <list repos> | LITE / FULL |
| Schema changes | <Yes/No — list entities> | LITE / FULL |
| UI changes | <None/Minor/Major — describe> | LITE / FULL |
| Estimated tasks | <count> | LITE / FULL |
| **Overall** | | **LITE / FULL** |

---

## Questions ★

> Design decisions to discuss. ✅ = Resolved, ❓ = Open.

1. ❓ **<Question Title>** — <Question description with context>. See <Section reference>.

---

## 2. Executive Summary ★

A 5–10 sentence overview of the feature covering:
- What it does
- What layers of the system it touches
- Key technical decisions

---

## <Numbered Sections — Feature-Specific Technical Details>

These sections vary by feature. Include what's relevant:

- **Data Foundation** — New data sources, constants, normalization logic
- **Schema Changes** — New entities, columns, migrations, with code examples
- **Business Logic** — Algorithms, computation, rules engines
- **API Design** — New endpoints, request/response shapes, auth
- **Integration Points** — External APIs, shared services, cross-service communication
- **Tech Debt & Refactoring Opportunities** — Flag any issues found during "See Something, Say Something" research.

For each section:
- Reference specific existing files with absolute file links
- Include code examples (TypeScript, SQL) for key changes
- Call out design decisions and alternatives considered
- Note DO NOT constraints (patterns to avoid)

---

## UI/UX Design ★

> **MANDATORY** — Include this section for every proposal. If the feature has NO UI component,
> write a brief note stating "This feature is backend-only with no UI changes" and skip the subsections.

### Location
Where the UI lives (e.g., new tab in `PricingStrategy.tsx`, new page, new modal).

### Layout & Information Architecture
ASCII diagram or description of the layout structure:
```text
┌──────────────────────────────────────────────────────┐
│ [Tabs: Existing Tab | New Tab]                       │
├─┬────────────────────┬───────────────────────────────┤
│ │ Sidebar (if any)   │ Main Content Area             │
│ │                    │ - Configuration Panel          │
│ │                    │ - Results / Data Display       │
│ │                    │ - Action Buttons               │
└─┴────────────────────┴───────────────────────────────┘
```

### Interaction State Coverage
| Feature | Loading | Empty | Error | Success |
|---|---|---|---|---|
| **Component A** | Skeleton/Spinner | "No data found." | "Failed to load." (Retry btn) | Populated view |
| **Component B** | ... | ... | ... | ... |

### User Journey & Emotional Arc
| Step | User Does | User Feels | Plan Specifies? |
|---|---|---|---|
| **1. Configuration** | Selects inputs | *Confident* | Clear selects with defaults |
| **2. Action** | Clicks primary button | *Relieved/Waiting* | Async feedback |
| **3. Review** | Scans results | *Analytical* | Data presented logically |

### Design System Alignment
- **Typography & Color**: Inherits from the existing design system tokens.
- **Spacing**: Follows the project spacing scale.
- **Components**: Reuses existing components (specify which: AntD Table, custom grids, etc.).
- **Responsive**: Describe stacking behavior at breakpoints.
- **Accessibility**: Keyboard navigation, ARIA roles, contrast requirements.

### AI Slop Risk & Visual Consistency
- **Hard Rule**: NO generic card grids, purple gradients, or bubbly container styles.
- Call out specific visual anti-patterns to avoid for this feature.

---

## Technical Architecture ★

> **MANDATORY** — Include this section for every proposal. Describe the system-level
> architecture, data flow, and component interactions.

### System Flow Diagram
ASCII diagram showing the data flow between services:
```
┌───────────────┐     POST /endpoint       ┌──────────────────┐
│  Service A    │ ──────────────────────►  │   Service B      │
│  (API Layer)  │     (SQS/HTTP/etc.)      │   (Worker/Proc)  │
│               │                          │                  │
│  • Validates  │                          │  • Processes     │
│  • Creates    │                          │  • Stores        │
│    record     │                          │  • Notifies      │
└───────────────┘                          └──────────────────┘
```

### Entity Schema (if new entities)
Define each new entity with columns, types, constraints, and indexes:

| Column Name | Data Type | Description |
|---|---|---|
| `id` | uuid | Primary Key |
| `fieldName` | type | Description |

**Indexes**: List indexes with columns and purpose.
**Constraints**: Unique constraints, foreign keys, application-layer invariants.

### Existing Infrastructure Leveraged
| Component | How It's Used |
|---|---|
| `ExistingEntity` | Source data / target for writes |
| `ExistingService` | Reused for X |

### New Components Required
| Component | Location | Description |
|---|---|---|
| `NewEntity` | S2QService | Tracks X |
| `NewWorker` | Microservice | Processes Y |
| `NewComponent` | WebUI | Displays Z |

---

## Reference Files & Patterns (for Implementation) ★

> **Purpose**: Exact file paths and patterns to follow. Read these files BEFORE writing code.

### Existing Entity Patterns
| Pattern | File Path |
|---|---|
| <Entity Name> | <absolute file path> |

### Available Agent Workflows
| Workflow | Repo | Description | When to Use |
|---|---|---|---|
| `/generate-migration` | S2QService | Generate TypeORM migrations | After entity changes |

### Constraints (DO NOT)
- **DO NOT** create files in new directories unless specified.
- **DO NOT** invent enum values.
- (List all constraints specific to this feature)

---

## Implementation TODO ★

> **MANDATORY**: Break the implementation down into atomic, 2-to-5-minute bite-sized tasks. Do not write high-level steps like "Implement Backend Service". Make tasks perfectly suitable for subagent-driven development.
> Complete each task in order. Each task references exact files and acceptance criteria (AC).

### Phase 1: <Phase Name>
- [ ] **1.1** Write failing unit test for `POST /power-lane` in `powerLane.controller.spec.ts`.
  - **AC**: Test correctly verifies that missing `Customer` returns 400.
- [ ] **1.2** Define `PowerLaneDto` with validation decorators.
- [ ] **1.3** Implement `PowerLaneService.create` to make the test pass.

### Phase 2: <Phase Name>
- [ ] **2.1** <Task description>.

(Continue for all phases: Backend entities/migrations, API endpoints, business logic, frontend, testing)

### Phase N: Testing & Verification
#### NA. Unit Tests
- [ ] **N.1** <Test description with exact test cases>.
  - **AC**: <What must pass>.

#### NB. Integration & E2E
- [ ] **N.X** Run `/e2e` workflow.
- [ ] **N.Y** Run `/update-docs` workflows.

---

## Appendix A: Edge Cases ★

> **MANDATORY** — Enumerate edge cases discovered during research. Each edge case
> must have a resolution strategy. Use the format below.

### A.1 <Edge Case Title>
- **Example**: Concrete scenario that triggers this edge case.
- **Resolution**: How the system handles it (specific code path or rule).

### A.2 <Edge Case Title>
- **Example**: ...
- **Resolution**: ...

(Continue for all edge cases. Common categories to consider:
- Data conflicts / collisions
- Missing or null data handling
- Backward compatibility with existing data
- Concurrent operations / race conditions
- Performance edge cases (large datasets)
- UI states with no data / error states
- Cross-feature interactions)

---

## Appendix B: Revision History ★

> **MANDATORY** — Track every revision to the proposal. Each revision includes
> what changed, why, and a disposition table for stakeholder feedback.

### Rev 1 — <Date YYYY-MM-DD>: Initial Proposal
- Created by <author> based on <TICKET_KEY> requirements.
- <N>-phase implementation plan with <M> tasks.
- <X> design questions flagged for discussion.

### Rev 2 — <Date>: <Revision Title>

**Source**: <Where the feedback came from — Jira comment, email, meeting, etc.>

**Key changes made in this revision**:
1. **<Change Title>** — Brief description of what changed and why.
2. **<Change Title>** — Brief description.

**Feedback items — disposition**:
| Feedback Item | Disposition |
|---|---|
| <Feedback summary> | ✅ Incorporated: <how> |
| <Feedback summary> | ⏳ Deferred: <why> |
| <Feedback summary> | ❌ Rejected: <rationale> |

---

## Appendix C: Post-Implementation Feedback

> **Include this appendix when stakeholder feedback arrives AFTER implementation has started.**
> Each feedback item gets its own subsection with edge-case analysis and implementation tasks.
> This appendix grows over time as the feature evolves during development.

### C.1 <Feedback Title> (from <Source>)

> **Source**: <Stakeholder name, Jira comment, email, meeting date>
> **Status**: Pending integration into the existing codebase.

**Feedback**: <What the stakeholder requested or observed>.

**Approach**: <How you will handle it — UI-only change, backend change, new endpoint, etc.>

**Why this approach?**:
- <Rationale 1>
- <Rationale 2>

#### Edge-Case Fixes (if applicable)

##### Edge Case C.1.1: <Title>
**Problem**: <Concrete scenario where the new feedback creates a subtle issue>.
**Scenario**: <Step-by-step reproduction>.
**Fix**: <Code-level fix with example>.
**Result**: <Expected behavior after fix>.

#### Implementation Tasks
- [ ] **C.1.1** <Task description>.
  - **AC**: <Acceptance criteria>.
- [ ] **C.1.2** <Next task>.

(Repeat C.2, C.3, etc. for additional post-implementation feedback items)
```

**Quality standards for the proposal:**
- Every code example must be syntactically correct and match existing patterns
- Every file path must be absolute and verified to exist
- Every entity/column definition must include TypeORM decorators
- Questions section must capture ALL ambiguities discovered during research
- Implementation TODO must be granular enough that each task is completable in one session
- Include test cases with expected inputs/outputs where applicable
- Edge Cases must cover at least: data conflicts, null handling, backward compatibility, and UI empty states
- Revision History must be updated every time the proposal is modified

### Step 7. Create the Progress Tracker

Write the progress tracker alongside the proposal:

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
- **Open Questions**: <list of open question numbers from proposal>
- **Reference Tickets**: [<TICKET_KEY>](https://<cloudId>/browse/<TICKET_KEY>)

---

## Implementation Checklist

> **Note**: Mirror ALL tasks from the proposal's Implementation TODO section exactly. Ensure they are atomic and bite-sized.

### Phase 1: <Phase Name>
- [ ] **1.1** Write failing unit test for `POST /power-lane` in `powerLane.controller.spec.ts`.
- [ ] **1.2** Define `PowerLaneDto` with validation decorators.
- [ ] **1.3** Implement `PowerLaneService.create` to make the test pass.

### Phase 2: <Phase Name>
- [ ] **2.1** <Task description>.

(Mirror ALL tasks from the proposal's Implementation TODO section)

### Phase N: Testing & Verification
- [ ] **N.1** <Test task>.

---

## Work Log & Session Summaries

### <Today's Date YYYY-MM-DD> — Proposal Creation
- Created technical proposal `<TICKET_KEY>-<ShortName>.md` covering <brief scope>.
- Analyzed existing codebase: <list key files/entities/services researched>.
- Key findings:
  - <Finding 1>
  - <Finding 2>
  - <Finding 3>
- Proposal structured into <N> implementation phases with <M> tasks.
- <X> open design questions flagged for discussion.
- Created this PROGRESS.md tracker.
```

### Step 8. Present to the User

After creating both files:
1. Inform the user where the files were created (with file links)
2. Highlight the **open questions** that need stakeholder input before implementation can begin
3. Summarize the scope: number of phases, number of tasks, key technical decisions
4. Mention any **related proposals** found in Step 2a and potential conflicts
5. Note the **template variant** used (LITE or FULL) and why
6. Ask if the user wants to review or adjust anything before sharing with the team
7. **Skill Handoff**: Tell the user exactly what to do next. Output:
   > *"Proposal saved! You can now run `/plan-eng-review` to critique the architecture, or if you are ready to build, run `/autoplan` or `/execute-approved`."*

---

## Updating an Existing Proposal (Proposal Diff on Update)

When the user asks to **update**, **revise**, or **add feedback** to an existing proposal, follow this workflow instead of creating a new proposal:

### Update Step 1. Load the Existing Proposal

Read the existing proposal and progress tracker:
```bash
cat Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md
cat Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-PROGRESS.md
```

### Update Step 2. Capture the Pre-Update State

Before making any changes, capture a snapshot of the proposal's key metrics:
- Number of questions (and which are open vs resolved)
- Number of implementation phases
- Total task count
- Number of edge cases
- Current revision number

### Update Step 3. Incorporate New Information

Apply the new feedback, requirements, or stakeholder input to the proposal:
- If new requirements come from a **Jira comment or subtask**, fetch it (Step 3a) and incorporate
- If new requirements come from an **attachment** (PPTX, CSV), analyze it (Step 3b)
- If the user provides feedback directly, incorporate it into the relevant sections

### Update Step 4. Auto-Generate Revision Diff

After updating, automatically generate the Revision History entry by comparing pre- and post-update state:

```markdown
### Rev <N> — <Date>: <Revision Title>

**Source**: <feedback source>

**Change summary** (auto-generated):
- Questions: <before> → <after> (<+N new>, <M resolved>)
- Implementation phases: <before> → <after>
- Tasks: <before> → <after> (<+X new tasks>)
- Edge cases: <before> → <after> (<+Y new>)
- New sections added: <list>
- Sections modified: <list>

**Key changes made in this revision**:
1. **<Change>** — <description>.

**Feedback items — disposition**:
| Feedback Item | Disposition |
|---|---|
| ... | ... |
```

### Update Step 5. Sync PROGRESS.md

After updating the proposal:
1. Read the updated Implementation TODO section
2. Compare against the current PROGRESS.md checklist
3. **Add** any new tasks to PROGRESS.md (preserving existing `[x]` and `[/]` marks)
4. **Never remove** completed tasks — only add new ones
5. Update the "Progress at a Glance" section with new phase/task counts
6. Add a Work Log entry documenting the revision

### Update Step 6. Present the Diff

Present a summary of what changed to the user:

```
📝 Proposal Updated: S2Q-1823-MexicoSupport.md (Rev 2 → Rev 3)

  +4 implementation phases (8 → 12)
  +15 tasks (42 → 57)
  +7 test cases (13 → 20)
  +3 edge cases (6 → 9)
  +4 constraints (10 → 14)
  +1 new section: Border Crossing Column Mapping
  Modified: UI/UX Design, Technical Architecture, Questions

  New questions requiring input: Q10, Q11, Q12
  PROGRESS.md synced with 15 new tasks added.
```

---

## Tips for Quality

- **Don't rush the code research.** A shallow proposal that misses integration points wastes more time than spending an extra minute reading code. Read at least 3–5 files.
- **Call out missing information early.** If the ticket is vague about requirements, list explicit questions in the Questions section.
- **Link to specific code.** Use file links with line numbers (e.g. `[powerLane.ts:L69](file:///path/to/file#L69)`) so the proposal is immediately actionable.
- **Follow existing patterns.** Reference how similar features were built. Include "Reference Files" tables pointing to exact patterns to follow.
- **Make tasks atomic.** Each task in the Implementation TODO should be completable in one session. If a task feels too large, split it.
- **Include test cases.** Enumerate edge cases with expected inputs/outputs in the proposal. These become the verification criteria.
- **Questions are valuable.** A proposal with 5 well-researched questions is more useful than one with zero questions and hidden assumptions.
- **Config is per-repo.** If you switch to a different repository mid-session, re-read `.jira.json` from the new working directory.
- **Proposal is the source of truth.** The PROGRESS.md mirrors the proposal's TODO list. If the proposal is updated, update PROGRESS.md to match.
- **Fetch linked tickets.** Don't ignore subtasks or related tickets — they often contain critical requirements and stakeholder decisions that aren't in the parent ticket.
- **Analyze attachments.** CSVs reveal data edge cases, PPTXs reveal UI expectations. These are high-signal artifacts that should be read, not just noted.
- **Check for conflicts.** Before writing a new proposal, scan existing proposals for overlapping entity/service changes. Two proposals modifying the same entity need coordinated migrations.
- **Use the right template weight.** A 3-task backend fix doesn't need a 12-section document. Classify scope early and use LITE when appropriate.
- **Update, don't recreate.** When new feedback arrives, revise the existing proposal — don't create a new one. The Revision History and Proposal Diff workflow exist for this purpose.
