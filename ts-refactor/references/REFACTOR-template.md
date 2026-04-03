# REFACTOR.md — Project Refactoring Rules

> This is a living document. Updated by Claude after every refactoring session.
> Last updated: [DATE]

---

## Project Overview

**Stack:** [e.g., Next.js 14, React 18, TypeScript 5.x, Vitest]
**State management:** [e.g., Zustand / Redux Toolkit / React Context]
**Styling:** [e.g., Tailwind CSS / CSS Modules / styled-components]
**Test framework:** [e.g., Vitest + Testing Library / Jest + RTL]
**Key constraints:** [e.g., "No class components", "All hooks in /hooks folder"]

---

## Refactoring Rules

These rules are agreed upon and must not be broken without team discussion.

### TypeScript Rules

1. **No `any` types.** Use `unknown` with type guards, or define specific types.
2. **All exported functions have explicit return types.**
3. **Interfaces for object shapes, `type` for unions and computed types.**
4. **Use `satisfies` for config objects** to keep inference + catch mismatches.
5. [ADD PROJECT-SPECIFIC RULES]

### Component Rules (TSX)

1. **Max component size: [150] lines.** Exceed this → extract sub-components.
2. **Max `useState` per component: [4].** Exceed this → extract custom hook.
3. **No inline objects/arrays in JSX props** (use `useMemo` or extract to variable).
4. **Early returns for loading/error states** before main render body.
5. [ADD PROJECT-SPECIFIC RULES]

### File Structure Rules

```
[FILL IN observed directory structure, e.g.:]
src/
  components/     # Presentational components only
  features/       # Feature-sliced directories
  hooks/          # Shared custom hooks (use*.ts)
  services/       # API layer (no React imports)
  types/          # Shared TypeScript types
  utils/          # Pure functions (no hooks, no React)
```

### Import Order Convention

```typescript
// 1. External libraries
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. Internal aliases (@/ or ~/)
import { Button } from '@/components/ui';

// 3. Relative imports (closest first)
import { useUserData } from './hooks/useUserData';
import type { UserProps } from './types';
```

### Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Component files | PascalCase | `UserCard.tsx` |
| Hook files | camelCase with `use` prefix | `useUserCard.ts` |
| Utility files | camelCase | `formatDate.ts` |
| Type files | camelCase + `.types.ts` suffix | `user.types.ts` |
| Test files | Same name + `.test.tsx` | `UserCard.test.tsx` |
| Props interface | `<Component>Props` | `UserCardProps` |
| Hook return type | `Use<Hook>Return` | `UseUserCardReturn` |

---

## Testing Conventions

**Test runner:** [e.g., Vitest / Jest]
**Component testing:** [e.g., @testing-library/react]
**Mock strategy:** [e.g., vi.mock() / jest.mock() / MSW for API]

### What to test

- ✅ Component renders correct output given props
- ✅ User interactions (click, input, form submit)
- ✅ Conditional rendering (loading, error, empty states)
- ✅ Custom hook return values and state transitions
- ✅ Utility functions (all branches)
- ❌ Implementation details (internal state variable names)
- ❌ Library internals (React's own diffing, etc.)

### Test file co-location

```
UserCard/
  UserCard.tsx
  UserCard.test.tsx       ← co-located, preferred
  useUserCard.ts
  useUserCard.test.ts
```

OR

```
__tests__/
  UserCard.test.tsx       ← if project uses centralized test dirs
```

[FILL IN which pattern this project uses]

---

## Known Patterns & Decisions

### State Management Pattern

[FILL IN e.g.:
- Global state: Zustand stores in `src/stores/`
- Server state: React Query in feature hooks
- Local UI state: useState in the component]

### API Layer Pattern

[FILL IN e.g.:
- All fetch calls in `src/services/*.ts`
- Never call fetch/axios directly in a component
- Use React Query mutations for POST/PUT/DELETE]

### Error Handling Pattern

[FILL IN e.g.:
- Errors thrown in services as typed error classes
- Components consume via React Query's `isError` / Error Boundary]

---

## Anti-Patterns We've Agreed to Remove

Track technical debt items here:

| Anti-pattern | Where | Priority | Assigned to |
|---|---|---|---|
| `any` in API response types | `src/services/` | High | — |
| God component in `Dashboard.tsx` | `src/pages/` | Medium | — |
| [ADD MORE] | | | |

---

## Changelog

Track every refactoring decision here so the team knows what changed and why.

| Date | File(s) | What Changed | Why |
|------|---------|-------------|-----|
| [DATE] | [file] | [change] | [reason] |
