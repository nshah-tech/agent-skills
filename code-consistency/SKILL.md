---
name: code-consistency
description: >
  Enforces codebase consistency before writing any code. Use this skill on EVERY
  coding task — new files, edits, refactors, bug fixes — without exception. Triggers
  when the user asks to write code, create a file, add a feature, fix a bug, refactor,
  or do anything that produces TypeScript/JavaScript/React output. The skill instructs
  Claude to observe existing patterns first, consult /docs/CONTRIBUTION.md, and write
  code that is indistinguishable from the rest of the codebase. Also triggers when the
  user says "follow existing patterns", "match the codebase", "update guidelines",
  "update CONTRIBUTION.md", "document our patterns", or "create CONTRIBUTION.md".
---

# Code Consistency Skill

## Purpose

Before writing a single line of code, you MUST understand the existing codebase patterns.
This project uses **TypeScript + Node.js/Express + React (Web)**. The goal is for every
file you produce to look like it was written by the same developer.

The canonical pattern reference lives at `/docs/CONTRIBUTION.md`. Always read it first.
Always update it when a new pattern is established.

---

## Workflow — Follow This Every Time

### Step 1: Read the Guidelines
```
READ /docs/CONTRIBUTION.md
```
If it doesn't exist yet, run the **CONTRIBUTION.md Workflow** below instead.

### Step 2: Observe the Relevant Area
Before writing, read 2–3 existing files in the same layer/domain as the task:

| Task type | Files to observe |
|---|---|
| New API route | An existing route + its controller + its service |
| New React component | 2 existing components in the same folder |
| New TypeORM entity | 2 existing entities + a repository that queries them |
| New service/utility | 2 existing services in the same domain |
| New TypeScript type/interface | The existing `types/` or `interfaces/` files nearby |

Read them in full. Do not skim.

### Step 3: Extract the Active Patterns
After reading, mentally confirm the following before writing. See `references/observation-checklist.md` for the full checklist.

- [ ] File naming convention (kebab-case? camelCase? PascalCase?)
- [ ] Folder structure (where does this type of file live?)
- [ ] Function/class structure (how are methods ordered? are there regions?)
- [ ] TypeScript style (explicit return types? `interface` vs `type`? generics style?)
- [ ] Express patterns (middleware order, error handling, response shape)
- [ ] TypeORM patterns (QueryBuilder vs `.find()`, transaction style, relation loading)
- [ ] React patterns (component structure, hook order, prop typing, export style)
- [ ] State management (how is state structured, named, and updated?)
- [ ] Naming conventions (variables, functions, classes, files — see checklist)
- [ ] Import ordering (external → internal → relative? aliased paths?)
- [ ] Error handling (try/catch shape, error types thrown, logging style)
- [ ] Comment style (JSDoc? inline? none?)

### Step 4: Write Code
Write the code. Follow patterns exactly. Do not introduce new conventions unless:
- The user explicitly requests a new approach, AND
- You update `/docs/CONTRIBUTION.md` to document it immediately after.

### Step 5: Self-Review Before Presenting
Before presenting your output, run this mental check:
- Could a developer mistake this for existing code in the repo? If no → revise.
- Does it use the same TypeORM query style as existing repositories?
- Does it follow the same Express middleware and response patterns?
- Does it match the React component structure in the same folder?
- Are all naming conventions consistent with observed files?

### Step 6: Update /docs/CONTRIBUTION.md (when needed)
If the task introduced a new pattern or clarified an existing one, append it to the
relevant section of `/docs/CONTRIBUTION.md`. Keep it concise — one example per pattern is enough.

---

## CONTRIBUTION.md Workflow — Creating & Updating

This section covers two scenarios: **creating** `CONTRIBUTION.md` from scratch, and
**updating** it when patterns change. Both are triggered by the same skill.

---

### Scenario A — Create (run when /docs/CONTRIBUTION.md doesn't exist)

**Trigger phrases**: "bootstrap CONTRIBUTION.md", "create CONTRIBUTION.md",
"document our patterns", or when Step 1 finds the file missing.

1. **Scan the project structure**
   List all top-level directories and key files to understand the overall layout.

2. **Sample files from each layer** — read one representative file from each:
   - Express routes
   - Controllers
   - Services
   - TypeORM entities
   - TypeORM repositories / query files
   - React components (at least 2 from different folders if possible)
   - React hooks (if present)
   - TypeScript types / interfaces
   - State management (store, slices, or context files)
   - Utility / helper files

3. **Fill in the template** at `references/patterns-template.md`
   Replace every `[FILL IN]` placeholder with what you actually observed.
   Do not leave placeholders. Do not guess — if a section is unclear, say so.

4. **Write the file** to `/docs/CONTRIBUTION.md`

5. **Report to the user**
   List every section you filled in and flag any areas where you were uncertain
   or observed conflicting patterns. Ask them to review before you write any code.

---

### Scenario B — Update (run when patterns change)

**Trigger phrases**: "update CONTRIBUTION.md", "update our guidelines",
"document this pattern", "add this to CONTRIBUTION.md", or automatically after
Step 6 of the coding workflow when a new pattern was introduced.

1. **Read the current `/docs/CONTRIBUTION.md`** in full.

2. **Identify the correct section** for the new or changed pattern.

3. **Update that section only** — do not rewrite unrelated sections.
   - If the pattern is new → add it under the relevant heading with a code example.
   - If the pattern replaces an old one → update the example and add a note:
     `> ⚠️ Changed [DATE]: [brief reason]`
   - If the pattern resolves a contradiction → remove the conflicting example
     and document the decision.

4. **Append a row to the Changelog** at the bottom of the file:
   `| [DATE] | [What changed] | AI |`

5. **Show the diff to the user** — display exactly what was added/changed
   before saving, and ask for confirmation if the change is significant.

---

## Rules — Non-Negotiable

1. **Never write code before reading `/docs/CONTRIBUTION.md` and at least 2 existing files.**
2. **Never introduce a pattern that doesn't exist in the codebase** without explicit instruction.
3. **Always update `/docs/CONTRIBUTION.md`** when a new or changed pattern is established.
4. **If two existing files contradict each other**, flag the inconsistency to the user and
   ask which pattern to follow — then document the decision in `/docs/CONTRIBUTION.md`.
5. **TypeORM queries** must exactly match the style in existing repositories:
   - If the codebase uses `QueryBuilder` → use `QueryBuilder`
   - If it uses `.find()` with options → match that style
   - Never mix both styles in one file
6. **React components** must match the structure of components in the same folder —
   not the structure of components in other folders (different folders may use different patterns).

---

## Reference Files

- `references/observation-checklist.md` — Detailed checklist for Step 3
- `references/patterns-template.md` — Template used to generate `/docs/CONTRIBUTION.md`

Read these when you need more detail than the summary above provides.
