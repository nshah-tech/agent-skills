---
name: ts-refactor
description: >
  Expert TypeScript and TSX (React TypeScript) refactoring skill. Triggers whenever
  the user wants to refactor, clean up, improve, restructure, modernize, or reduce
  tech debt in any .ts or .tsx file. Also triggers for: "this component is too big",
  "clean up this file", "improve types", "remove any types", "extract this logic",
  "split this component", "add tests before refactoring", "make this more maintainable",
  "refactor hooks", "improve type safety", or any request involving code quality
  improvements in TypeScript or React TypeScript codebases. Always use this skill
  before making structural changes to .ts or .tsx files — even if the user just says
  "fix this" or "make this better".
---

# TypeScript & TSX Refactoring Skill

A structured, safe, and repeatable workflow for refactoring `.ts` and `.tsx` files —
from a single utility function to a multi-file React feature.

---

## ⚡ Quick Decision: What Are You Refactoring?

| File type | Go to |
|---|---|
| Pure `.ts` (service, hook, util, type) | [TS Refactoring Workflow](#ts-workflow) |
| `.tsx` React component | [TSX Refactoring Workflow](#tsx-workflow) |
| Both / unsure | Start with [Pre-Flight Checklist](#pre-flight) |

---

## Step 0 — Always Do This First: Read Living Docs {#pre-flight}

Before touching a single line of code:

1. **Check for living docs** — read all that exist:
   - `REFACTOR.md` — project refactoring rules and patterns
   - `CONTRIBUTING.md` — contribution standards
   - `DESIGN.md` — architecture decisions and constraints
   - `docs/CONTRIBUTION.md` — if the code-consistency skill is installed

   > If none of these exist → run the **[Living Docs Bootstrap](#living-docs)** workflow first.

2. **Read the file(s) to be refactored** in full. Do not skim.

3. **Check for tests:**
   - Look for `*.test.ts`, `*.test.tsx`, `*.spec.ts`, `*.spec.tsx` in the same folder or a `__tests__/` directory.
   - If tests exist → go to **[With Tests Path](#with-tests)**
   - If no tests exist → go to **[No Tests Path](#no-tests)**

4. **Run the type-checker** before changing anything:
   ```bash
   npx tsc --noEmit
   ```
   Note any pre-existing errors — do not fix unrelated errors during refactor.

5. **Run existing tests** to establish a baseline:
   ```bash
   npx jest --testPathPattern="<filename>"
   # or
   npx vitest run <filename>
   ```

---

## Path A — Refactoring With Tests Existing {#with-tests}

> Tests are your safety net. Use them aggressively.

### Phase 1: Understand Before Changing
- Read the test file to understand the *contract* the code must honor
- Identify what the tests cover and what they don't
- Do NOT change test logic unless the tests themselves are wrong

### Phase 2: Refactor in Small, Verifiable Steps
Each step = one logical change + one passing test run.

```
Change → tsc --noEmit → run tests → commit (or checkpoint)
```

Never let more than one failing test exist at a time.

### Phase 3: Apply the Refactoring Checklist
See [TS Checklist](#ts-checklist) or [TSX Checklist](#tsx-checklist) below.

### Phase 4: Expand Test Coverage (if gaps found)
If during refactoring you discover untested behaviors, add tests **after** the
refactoring is stable. Document coverage gaps in `REFACTOR.md`.

---

## Path B — Refactoring Without Tests {#no-tests}

> No tests = no safety net. Your first job is to create one.

### Phase 1: Write Characterization Tests First
Before refactoring, capture current behavior:

```tsx
// Example: UserCard.test.tsx — characterization tests
describe('UserCard (pre-refactor behavior)', () => {
  it('renders user name', () => { ... });
  it('calls onEdit when edit button clicked', () => { ... });
  it('hides admin badge for non-admin users', () => { ... });
});
```

Rules for characterization tests:
- Test the **black-box interface** (props in, rendered output + callbacks out)
- Do NOT test implementation details (internal state names, private functions)
- These tests protect you — they fail if the refactor changes behavior

### Phase 2: Run and Lock the Tests
```bash
npx jest --testPathPattern="<filename>" --coverage
```
All characterization tests must pass before any refactoring begins.

### Phase 3: Refactor
Follow the same small-step process as Path A.

### Phase 4: Upgrade Test Quality
After refactoring, improve tests from characterization to proper unit/integration
tests that cover edge cases.

---

## TypeScript (.ts) Refactoring Checklist {#ts-checklist}

Work through this top to bottom. Check each item.

### 🔴 Type Safety (Fix First)
- [ ] Eliminate all `any` — use `unknown`, specific types, or generics
- [ ] Remove type assertions (`as SomeType`) where type can be narrowed properly
- [ ] Replace implicit `any` in function params with explicit types
- [ ] Add return types to all exported functions
- [ ] Strengthen union types: `string | undefined` → use `NonNullable<T>` where appropriate
- [ ] Replace `object` with specific interfaces
- [ ] Use `satisfies` operator for config objects (TS 4.9+)

### 🟡 Structure (Refactor Second)
- [ ] Single Responsibility: does this file do one thing? If not, split it
- [ ] File size > 250 lines? Extract sub-modules
- [ ] Group related exports — types, constants, functions, classes
- [ ] Move pure calculation logic out of hooks/components into plain functions
- [ ] Extract shared types into a `types.ts` or `<domain>.types.ts` file
- [ ] Remove dead code (unused variables, functions, imports)

### 🟢 Quality (Polish Last)
- [ ] Import order: external libs → internal modules → relative imports
- [ ] Replace magic numbers/strings with named constants
- [ ] Add JSDoc to all public API functions (exported from the module)
- [ ] Replace `console.log` with proper error handling or logging abstraction
- [ ] Check for missing `async/await` or unhandled Promise rejections
- [ ] Run `eslint --fix` after structural changes

---

## TSX React Component Refactoring Checklist {#tsx-checklist}

### 🔴 Type Safety (Fix First)
- [ ] All props typed with `interface` or `type` — never `any`
- [ ] Event handlers typed: `React.ChangeEvent<HTMLInputElement>` not `any`
- [ ] `useState` with complex types explicitly annotated: `useState<User | null>(null)`
- [ ] `useRef` typed: `useRef<HTMLDivElement>(null)`
- [ ] `forwardRef` typed with two generics: `forwardRef<RefType, PropsType>`
- [ ] Context typed: never `createContext(undefined)` without a type guard hook
- [ ] Children typed: `React.ReactNode` for flexible, `React.ReactElement` if specific

### 🟡 Component Structure (Refactor Second)
- [ ] Component > 150 lines? Break into smaller components
- [ ] More than 3–4 `useState` calls? Extract to a custom hook (`use<Domain>`)
- [ ] Business logic mixed into JSX? Extract to hook or utility
- [ ] Deeply nested JSX (5+ levels)? Extract sub-components
- [ ] Functions defined inside render? Move above return or extract
- [ ] Prop drilling 2+ levels deep? Consider context or composition
- [ ] Render functions (functions returning JSX) in component? Convert to components
- [ ] Heavy computation in render? Wrap with `useMemo`
- [ ] Callback recreated every render? Wrap with `useCallback`

### 🟡 Hooks Quality
- [ ] Custom hook named with `use` prefix
- [ ] Hook dependencies correct in `useEffect`, `useMemo`, `useCallback`
- [ ] No `useEffect` for data derivable from existing state/props — compute directly
- [ ] Cleanup functions in `useEffect` for subscriptions, timers, event listeners
- [ ] Hooks not called conditionally or inside loops

### 🟢 JSX & Rendering Quality (Polish Last)
- [ ] Early returns for loading/error states (before main render)
- [ ] No unnecessary `<div>` wrappers — use `<>` fragments
- [ ] `key` prop present and stable (not array index) for lists
- [ ] No inline object/array literals in JSX props (causes re-renders)
- [ ] `React.lazy` + `Suspense` for heavy conditional components
- [ ] Accessible: `aria-*` attrs, semantic HTML, `alt` on images

---

## TS Refactoring Workflow {#ts-workflow}

```
1. Pre-Flight (read docs + run tsc + run tests)
2. Choose Path A or B
3. Apply TS Checklist (top → bottom, one item at a time)
4. After each logical group: tsc --noEmit + run tests
5. Update REFACTOR.md with decisions made
6. Final: lint, format, review imports
```

---

## TSX Refactoring Workflow {#tsx-workflow}

```
1. Pre-Flight (read docs + run tsc + run tests)
2. Choose Path A or B (write characterization tests if none exist)
3. Type Safety fixes first (red items)
4. Component structure refactoring (yellow items) — test after each extraction
5. Hook quality improvements (yellow items)
6. Polish pass (green items)
7. Update REFACTOR.md with decisions made
8. Final: lint, format, Storybook/visual check if applicable
```

---

## Extraction Decision Guide

Use this when deciding whether to extract something:

| Signal | Action |
|---|---|
| Logic used in 2+ components | Extract to `hooks/use<Name>.ts` or `utils/<name>.ts` |
| JSX block > 15 lines with its own state/behavior | Extract to a new component |
| 4+ related `useState` calls | Extract to a custom hook |
| Pure data transformation | Extract to a utility function (no hooks) |
| Shared TypeScript type | Move to `types.ts` or `<domain>.types.ts` |
| API call logic | Extract to a service layer `services/<name>.ts` |
| Constants used in 2+ places | Move to `constants.ts` |

---

## Common TypeScript Anti-Patterns to Fix

```typescript
// ❌ ANTI-PATTERN: any everywhere
const handleData = (data: any) => { ... }

// ✅ FIX: use unknown + type guard, or specific type
const handleData = (data: unknown) => {
  if (isUserData(data)) { ... }
}

// ❌ ANTI-PATTERN: type assertion hiding bugs
const user = response as User;

// ✅ FIX: validate before asserting
function isUser(x: unknown): x is User {
  return typeof x === 'object' && x !== null && 'id' in x;
}

// ❌ ANTI-PATTERN: no return types on exported functions
export function processItems(items) { ... }

// ✅ FIX: explicit return types
export function processItems(items: Item[]): ProcessedItem[] { ... }

// ❌ ANTI-PATTERN: giant god hook
function useApp() { /* 300 lines of state + effects */ }

// ✅ FIX: split by domain
function useAuth() { ... }
function useUserProfile() { ... }
function useNotifications() { ... }
```

---

## Living Documents System {#living-docs}

These files are the "brain" of your project's refactoring knowledge. This skill
reads them at the start of every session and writes to them after decisions are made.

### Required Living Docs

**`REFACTOR.md`** — The primary refactoring rulebook.
See `references/REFACTOR-template.md` for the template.

**`CONTRIBUTING.md`** — Contribution patterns (code style, PR process).
**`DESIGN.md`** — Architecture decisions and constraints.

### When to Create Living Docs

If none exist: run the **[Living Docs Bootstrap](#bootstrap)** workflow.

### Living Docs Bootstrap Workflow {#bootstrap}

1. **Scan the project structure:**
   ```bash
   find . -name "*.ts" -o -name "*.tsx" | head -30
   ls src/
   ```

2. **Sample representative files** (2–3 from each layer):
   - Components → extract prop patterns, component size norms
   - Hooks → extract state management patterns
   - Services/utils → extract function signature patterns
   - Types → extract naming conventions

3. **Generate `REFACTOR.md`** using `references/REFACTOR-template.md`
   Fill in every section from what you observed.

4. **Generate `DESIGN.md`** using `references/DESIGN-template.md`

5. **Report to the user:**
   - What patterns you found
   - Any inconsistencies or conflicting patterns observed
   - Ask for confirmation before refactoring

### Keeping Living Docs Updated

After every refactoring session, append to `REFACTOR.md`:
```markdown
## Changelog
| Date | File(s) | Decision | Reason |
|------|---------|----------|--------|
| 2024-01-15 | UserCard.tsx | Extracted useUserCard hook | Component exceeded 150 lines |
```

---

## Sharable Workflow Script

When the user wants a shareable refactoring workflow, generate the file at:
`scripts/refactor-check.sh`

See `references/workflow-script-template.sh` for the template.

Run it before every refactoring session:
```bash
bash scripts/refactor-check.sh src/components/UserCard.tsx
```

---

## Reference Files

Read these when you need more detail:

- `references/REFACTOR-template.md` — Template for the project's `REFACTOR.md`
- `references/DESIGN-template.md` — Template for the project's `DESIGN.md`
- `references/ts-patterns.md` — Advanced TypeScript patterns for refactoring
- `references/tsx-patterns.md` — Advanced TSX/React patterns for refactoring
- `references/workflow-script-template.sh` — Shareable pre-refactor shell script

---

## Questions to Ask Before Refactoring

If the user's request is ambiguous, ask **one** of these (not all):

1. "Is there a test suite for this file, or should I write characterization tests first?"
2. "Are there project-specific conventions in CONTRIBUTING.md or DESIGN.md I should read?"
3. "Is the goal type safety, performance, readability, or splitting into smaller pieces?"

---

## Self-Check Before Presenting Refactored Code

- [ ] `tsc --noEmit` passes with 0 new errors
- [ ] All pre-existing tests still pass
- [ ] `REFACTOR.md` updated with decisions made
- [ ] No `any` types introduced
- [ ] No behavior was changed — only structure
- [ ] File(s) are under 250 lines (TS) / 150 lines (TSX component)
