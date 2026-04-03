# DESIGN.md — Architecture Decisions & Constraints

> This is a living document. Track all significant architectural decisions here.
> Refactoring must not violate decisions recorded in this file.
> Last updated: [DATE]

---

## System Overview

**Purpose:** [What does this application do?]
**Primary users:** [Who uses it?]
**Scale:** [Rough user/data scale]

---

## Technology Choices & Why

| Technology | Version | Why Chosen | Constraint |
|---|---|---|---|
| React | [e.g., 18.x] | [reason] | [e.g., no class components] |
| TypeScript | [e.g., 5.x] | [reason] | [e.g., strict mode ON] |
| [FRAMEWORK] | | | |
| [STATE LIB] | | | |
| [TEST FRAMEWORK] | | | |

---

## Architecture Decisions (ADRs)

### ADR-001: [Decision Title]
**Status:** Accepted
**Date:** [DATE]
**Context:** [Why was this decision needed?]
**Decision:** [What was decided?]
**Consequences:** [What does this mean for refactoring?]

### ADR-002: [Decision Title]
[Follow same format]

> When refactoring, Claude must not violate any `Accepted` ADR.
> If a refactoring would require changing an ADR, flag this to the user first.

---

## Module Boundaries

> These boundaries define what is allowed to import what.
> Violating these in a refactor is a breaking change.

```
[FILL IN, e.g.:]

components/     → can import from: hooks, utils, types
                → cannot import from: services, stores directly

hooks/          → can import from: services, utils, types
                → cannot import from: components

services/       → can import from: types, utils
                → cannot import from: components, hooks, stores

stores/         → can import from: services, types, utils
                → cannot import from: components
```

---

## Performance Constraints

- [e.g., "Initial page load must be < 3s on 4G"]
- [e.g., "No synchronous operations > 16ms (60fps budget)"]
- [e.g., "Bundle size limit: 200KB gzipped per route"]

### Code Splitting Rules
[FILL IN e.g.:
- Every route is lazy-loaded
- Feature slices are dynamically imported
- Heavy third-party libs (charts, editors) are always lazy-loaded]

---

## TypeScript Configuration

```json
// tsconfig.json key settings (explain the non-obvious ones)
{
  "compilerOptions": {
    "strict": true,         // full strict mode
    "noUncheckedIndexedAccess": true,  // array access returns T | undefined
    "exactOptionalPropertyTypes": true  // ? means absent, not | undefined
  }
}
```

> If a refactoring makes `tsc` stricter (e.g., enabling a new flag), document it here.

---

## Forbidden Patterns

These are explicitly banned in this codebase. Refactoring must never introduce them.

- [ ] `any` type (use `unknown` with guards)
- [ ] Class components (functional components only)
- [ ] Direct DOM manipulation (`document.getElementById` etc.) outside designated utils
- [ ] [ADD PROJECT-SPECIFIC BANS]

---

## Approved Libraries

When refactoring, only introduce dependencies from this approved list (or get approval):

| Category | Approved Library | Notes |
|---|---|---|
| Data fetching | [e.g., React Query / SWR] | |
| Forms | [e.g., React Hook Form / Formik] | |
| State | [e.g., Zustand / Redux Toolkit] | |
| Animation | [e.g., Framer Motion] | |
| Testing | [e.g., Vitest + Testing Library] | |
| [ADD MORE] | | |

---

## Changelog

| Date | Section | Change | Author |
|------|---------|--------|--------|
| [DATE] | [section] | [what changed] | AI |
