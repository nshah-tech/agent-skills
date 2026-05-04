---
name: product-doc-generator
description: Translates completed technical proposals into user-facing product documentation (wikis). Runs after execution to ensure internal product guides are always up-to-date with shipped features. Use when the user says "create product doc", "update wiki", or invokes "/product-doc-generator".
---

# Product Doc Generator

Closes the loop on feature delivery by translating deep technical architecture documents into user-friendly Wiki / Product guides.

## When to Use

- The user asks to "create wiki for ACME-1823", "update product doc"
- The user explicitly invokes `/product-doc-generator`
- Triggered as the final documentation step after a feature is merged

---

## Workflow

### Step 1. Load the Proposal
Find the proposal file: `Sprints/<version>/<TICKET_KEY>-<ShortName>/<TICKET_KEY>-<ShortName>.md`.
Read the entire document to extract the business logic, UI changes, and feature capabilities.

### Step 2. Update Sprint Doc Status (Wiki Done)
1. Read `Sprints/<version>/<version>.md` in the documentation repo.
2. Find the row for `<TICKET_KEY>` in the `## Tickets` table.
3. Update its Status to `📘 Wiki Done`.
4. Save the sprint doc.

### Step 3. Generate the Wiki Page
Translate the technical proposal into a user-facing guide.
**Location**: `Product_Docs/Features/<ShortName>.md` (create the directory if it doesn't exist).

**Structure**:
```markdown
# <Feature Name>

## Overview
<Plain English summary of what the feature does and why it exists. Do not include technical architecture like SQS or TypeORM.>

## How to Use
<Step-by-step guide based on the User Journey section of the proposal. E.g., "1. Go to Pricing Strategy > 2. Select..." >

## Capabilities & Limitations
<List what the feature CAN do, and what its known edge cases/limitations are (from Appendix A in the proposal).>

## Troubleshooting
<What happens in error states and how the user should resolve them.>

---
*Generated from technical proposal [[<TICKET_KEY>-<ShortName>]] on <YYYY-MM-DD>.*
```

### Step 4. Present to User
Output the following explicit message:
> *"Product documentation generated at `Product_Docs/Features/<ShortName>.md`. The sprint document has been updated to 📘 Wiki Done."*

**Session Bookmark**:
> *"Session complete. To resume later, run `/workflow-status <version>`."*
