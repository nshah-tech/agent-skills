---
name: code-review
description: >
  AI-powered pre-commit code review skill for React, NestJS, and Express codebases.
  Triggers whenever the user says "review my code", "check my changes", "pre-commit review",
  "review before I push", "find issues in my code", "check for bugs", "audit my changes",
  "review this PR", "is my code good?", "what's wrong with this", or pastes code and asks
  for feedback. Also triggers for: "review my diff", "check my component", "review my
  controller", "review my service", "check my API", or any request to inspect, validate,
  or sanity-check code before committing, pushing, or submitting for PR. Triggers on
  "/review-diff" to automatically run git diff and review all staged/unstaged changes.
  Triggers on "/review-pr TICKET-123" to fetch a Jira ticket and verify that the code
  changes correctly solve the problem described in the ticket. Always use this skill before
  the user commits or pushes code changes — even for small snippets — because hidden issues
  often lurk in "simple" changes.
---

# Pre-Commit Code Review Skill

A structured, layered review workflow for **React**, **NestJS**, and **Express** codebases.
Catches bugs, security holes, type errors, performance traps, and style violations
before they reach your repo.

---

## ⚡ Commands

| Command | What it does |
|---|---|
| `/review-diff` | Auto-runs `git diff`, captures all changes, full review |
| `/review-pr TICKET-123` | Fetches Jira ticket + diffs code, verifies problem→solution alignment |

## ⚡ Quick Start: What Are You Reviewing?

| Code type | Go to |
|---|---|
| React component / hook / context | [React Review](#react-review) |
| NestJS module / controller / service / guard / pipe | [NestJS Review](#nestjs-review) |
| Express route / middleware / handler | [Express Review](#express-review) |
| Shared utility / type / config | [Universal Checklist](#universal) |
| Full diff / multiple files | [Full Diff Review](#full-diff) |

---

## Step 0 — Always Do First: Gather Context

Before reviewing a single line:

1. **Understand the change scope** — Ask if not clear:
   - What does this change do?
   - Is this a new feature, bug fix, or refactor?
   - Are there related files not shown?

2. **Read living docs if present:**
   - `CONTRIBUTING.md`, `docs/CONTRIBUTION.md`, `DESIGN.md`
   - `.eslintrc`, `tsconfig.json`, `nest-cli.json`, `.env.example`

3. **Check for test files** alongside changed files.

4. **Run static checks first** (if codebase is accessible):
   ```bash
   npx tsc --noEmit
   npx eslint <changed-files>
   ```

---

## Universal Checklist (All Code) {#universal}

Run this on every review before any framework-specific checks.

### 🔴 Critical — Must Fix Before Commit

- [ ] **No hardcoded secrets** — no API keys, passwords, tokens, connection strings in code
- [ ] **No `console.log` with sensitive data** — user data, tokens, internal paths
- [ ] **No `TODO` that blocks correctness** — uncommitted logic, skipped validations
- [ ] **No use of `any` type** without explicit justification comment
- [ ] **No unhandled Promise rejections** — every `async` function has try/catch or `.catch()`
- [ ] **No silent error swallowing** — `catch(e) {}` or `catch(e) { return null }` without logging
- [ ] **No deprecated API usage** — check Node.js, React, NestJS release notes
- [ ] **Imports are real** — no missing modules, typos, circular imports
- [ ] **Env variables validated at startup** — not just accessed inline

### 🟡 Important — Fix Before Merge

- [ ] **Dead code removed** — commented-out blocks, unused variables/imports
- [ ] **Magic numbers named** — `const MAX_RETRIES = 3` not just `3`
- [ ] **Error messages are meaningful** — not `"Something went wrong"` everywhere
- [ ] **Function complexity** — cyclomatic complexity > 10 is a smell; consider splitting
- [ ] **No deeply nested callbacks** — flatten with async/await
- [ ] **Types accurate** — return types match implementation
- [ ] **Edge cases handled** — null, undefined, empty arrays, zero, negative numbers

### 🟢 Quality — Nice to Have

- [ ] **JSDoc on public APIs**
- [ ] **Consistent naming** — matches project conventions
- [ ] **File size reasonable** — < 300 lines for most files
- [ ] **New code has tests** (or test plan noted)

---

## React Review Checklist {#react-review}

Read `references/react-patterns.md` for detailed guidance on any item below.

### 🔴 Critical

- [ ] **No direct state mutation** — `state.items.push(x)` is always wrong
- [ ] **No `useEffect` dependency lies** — missing deps cause stale closures
- [ ] **No memory leaks** — subscriptions, timers, event listeners cleaned up in useEffect return
- [ ] **No keys using array index** for dynamic lists that reorder/filter
- [ ] **No `useEffect` for derived state** — compute from existing state/props directly
- [ ] **Hooks not called conditionally or in loops**
- [ ] **Context not abused for frequently-changing values** — causes full tree re-renders

### 🟡 Important

- [ ] **No unnecessary re-renders** — callbacks memoized with `useCallback`, heavy computations with `useMemo`
- [ ] **No prop drilling > 2 levels** — consider context or component composition
- [ ] **No giant components** — > 150 lines of JSX? Extract sub-components
- [ ] **Async in useEffect handled properly** — no `async` in effect callback directly; use inner function
- [ ] **Forms** — controlled inputs, validation present, loading/error states handled
- [ ] **Accessibility** — interactive elements have `aria-*`, images have `alt`, semantic HTML used
- [ ] **Error boundaries** wrapping async/lazy-loaded sections

### 🟢 Quality

- [ ] **React.lazy + Suspense** for heavy components not needed at initial paint
- [ ] **`key` prop stable** — ID-based, not Math.random()
- [ ] **No inline object/array literals in JSX props** — creates new reference every render

**Reference:** `references/react-patterns.md`

---

## NestJS Review Checklist {#nestjs-review}

Read `references/nestjs-patterns.md` for detailed guidance.

### 🔴 Critical — Security & Correctness

- [ ] **Every route has guards** — `@UseGuards(AuthGuard(...))` or global guard configured
- [ ] **Every route has validation** — `@Body()` with `class-validator` DTO, not raw `req.body`
- [ ] **`ValidationPipe` with `whitelist: true`** — strips unknown properties
- [ ] **`@Roles()` decorator** present on admin/privileged routes
- [ ] **No `@Public()` on sensitive endpoints** without explicit justification
- [ ] **DTOs use `class-transformer`** — `@Expose()`, `@Exclude()` for response shaping
- [ ] **No raw SQL** — use TypeORM QueryBuilder or parameterized queries
- [ ] **File uploads validated** — MIME type, file size limits enforced
- [ ] **Circular dependency check** — `forwardRef()` used where necessary, not as a band-aid

### 🟡 Important

- [ ] **Services are injectable** — no `new MyService()` inside other services
- [ ] **No business logic in controllers** — controllers only orchestrate, delegate to services
- [ ] **Exception filters** used for domain errors — not `throw new Error(...)`
- [ ] **`@Transform()` applied** for date parsing, number coercion in DTOs
- [ ] **Interceptors** for logging, response formatting, not inline in services
- [ ] **Module boundaries respected** — no cross-module imports without proper export
- [ ] **`ConfigService` for env vars** — not `process.env.X` directly in services
- [ ] **Database transactions** for multi-step operations
- [ ] **Pagination** for list endpoints — no unbounded queries

### 🟢 Quality

- [ ] **Swagger decorators** — `@ApiTags`, `@ApiOperation`, `@ApiResponse` present
- [ ] **Consistent HTTP status codes** — `201` for POST create, `204` for DELETE, etc.
- [ ] **Caching strategy** considered for read-heavy endpoints

**Reference:** `references/nestjs-patterns.md`

---

## Express Review Checklist {#express-review}

Read `references/express-patterns.md` for detailed guidance.

### 🔴 Critical — Security

- [ ] **Input sanitization** — every `req.body`, `req.params`, `req.query` validated
- [ ] **Authentication middleware** applied to protected routes
- [ ] **`express-rate-limit`** on auth endpoints and public APIs
- [ ] **CORS configured correctly** — not `origin: '*'` in production
- [ ] **Helmet.js used** — sets security headers
- [ ] **No path traversal** — user input never used in `path.join` without sanitization
- [ ] **SQL/NoSQL injection prevention** — parameterized queries, Mongoose sanitize
- [ ] **Error handler middleware** defined at bottom of app — catches uncaught errors
- [ ] **No secrets in responses** — password hashes, tokens never returned

### 🟡 Important

- [ ] **`next(err)` used** — not `throw` inside Express route handlers
- [ ] **Async routes wrapped** — `asyncHandler(async (req, res) => {...})` or equivalent
- [ ] **Response always sent** — every code path calls `res.send/json/end`
- [ ] **No prototype pollution** — `req.body` never merged into objects directly
- [ ] **File uploads** — `multer` with file type/size limits
- [ ] **Logging middleware** — Morgan or custom, logs request/response
- [ ] **No blocking operations** in route handlers — DB calls are async, CPU work offloaded

### 🟢 Quality

- [ ] **Routes organized by resource** — not one giant router file
- [ ] **Middleware order correct** — auth before routes, error handler last
- [ ] **HTTP status codes correct**

**Reference:** `references/express-patterns.md`

---

## Full Diff Review Workflow {#full-diff}

When reviewing a git diff or multiple changed files at once:

### Phase 1: Structural Scan (5 min)
```bash
# If repo is accessible:
git diff --stat HEAD
git diff HEAD -- <files>
```
- Count files changed
- Identify change type (feature / fix / refactor / config)
- Flag any files that weren't expected to change

### Phase 2: Security Pass (always first)
Run the security items from whichever framework checklists apply.
Security issues are blockers — flag them immediately, don't wait for full review.

### Phase 3: Correctness Pass
- Logic errors, wrong assumptions, edge cases missed
- Data flow: does data transform correctly through the layers?
- Error handling: every failure mode handled?

### Phase 4: Type Safety Pass
```bash
npx tsc --noEmit
```
- New `any` types introduced?
- Type assertions hiding real problems?
- Missing null checks?

### Phase 5: Test Coverage Check
- Are new behaviors tested?
- Are changed behaviors' tests updated?
- Are edge cases in tests?

### Phase 6: Performance & Scalability
Read `references/performance-checklist.md` for the full audit. Key signals:
- N+1 query risk (loops with DB calls inside)?
- Missing indexes on new query patterns?
- Heavy computation in a hot render path or request handler?
- React bundle size impact — new heavy dependency added?
- Missing pagination on a list endpoint?

---

## Review Output Format

Always structure feedback in this order:

```
## Code Review: [file or feature name]

### 🚨 Critical (Must Fix Before Commit)
- [Issue] — [Why it's a problem] — [Suggested fix]

### ⚠️ Important (Fix Before Merge)
- [Issue] — [Why it matters] — [Suggested fix]

### 💡 Suggestions (Optional Improvements)
- [Suggestion] — [Benefit]

### ✅ What's Done Well
- [Positive observation]

### 📋 Summary
[2–3 sentence overall assessment]
[Verdict: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
```

---

## Common Hidden Issues by Stack

### React Hidden Issues
- `useEffect` with object/array deps causes infinite loops — always memoize or use primitives
- `useState` setter with stale closure — use functional update `setState(prev => ...)`
- Concurrent mode unsafe patterns — mutating state during render
- `useLayoutEffect` on SSR breaks server rendering
- Context value not memoized — rebuilds every parent render

### NestJS Hidden Issues
- `forwardRef` circular dependency hiding architectural problems
- `@Inject()` token mismatches — silently injects `undefined`
- Missing `async` on lifecycle hooks (`onModuleInit`, `onModuleDestroy`)
- TypeORM lazy relations loading N+1 in disguise
- Interceptors modifying response after streaming started

### Express Hidden Issues
- `req.body` is `undefined` when `express.json()` middleware missing
- Async errors not caught by Express 4 default error handler — needs `next(err)`
- Route order matters — more specific routes must come before wildcard routes
- `res.json()` after `res.send()` causes "Cannot set headers" error
- Missing `await` on DB calls returns `Promise` object as response body

---

---

## /review-diff Workflow {#review-diff}

Triggered by: `/review-diff`

Automatically captures all local changes and runs a full structured review — no need to paste code manually.

### Step 1: Capture the Diff
```bash
# Show what's staged + unstaged
git diff HEAD

# If nothing (all committed), check last commit
git diff HEAD~1 HEAD

# Get list of changed files
git diff --name-only HEAD
```

### Step 2: Check Compilation
```bash
npx tsc --noEmit 2>&1 | head -40
npx eslint $(git diff --name-only HEAD | grep -E '\.(ts|tsx|js|jsx)$' | tr '\n' ' ') 2>&1 | head -60
```

### Step 3: Run Full Review
With the diff captured, run the [Full Diff Review](#full-diff) workflow — all 6 phases.

### Step 4: Output
Use the [Review Output Format](#output-format) — show file-by-file findings, then an overall summary.

> **If the repo is not accessible** (no git), ask the user to paste the output of `git diff HEAD` instead.

---

## /review-pr Workflow {#review-pr}

Triggered by: `/review-pr TICKET-123` or `/review-pr` (will ask for ticket key)

Fetches the Jira ticket, captures the current code diff, then cross-examines whether **the code change actually solves the problem described in the ticket**.

### Step 1: Load Jira Config
```bash
cat .jira.json 2>/dev/null || echo "NOT_FOUND"
```
- If found: use `cloudId` and `defaultProject` from file.
- If not found: ask the user for their Atlassian site URL (e.g. `acme.atlassian.net`).

### Step 2: Fetch the Jira Ticket
Use `mcp_atlassian-mcp-server_getJiraIssue` with `responseContentFormat: "markdown"`.

Extract and parse:
- **Summary** — the one-line title
- **Problem statement** — what is broken or missing (from Description)
- **Acceptance criteria** — the explicit "done" conditions (look for ACs in the description or comments)
- **Issue type** — Bug / Story / Task / Improvement
- **Priority** — Critical / High / Medium / Low
- **Affected areas** — components, services, or pages mentioned

If the ticket lacks a clear problem statement or ACs, **flag this immediately** before proceeding. A vague ticket produces a vague review.

### Step 3: Capture the Code Diff
```bash
git diff HEAD
git diff --name-only HEAD
```

If there is no diff (changes are committed), use:
```bash
git diff HEAD~1 HEAD
git diff --name-only HEAD~1 HEAD
```

### Step 4: Problem → Solution Alignment Audit

This is the core of `/review-pr`. For every item in the ticket's problem statement and ACs, answer:

| Ticket Claim | Evidence in Code | Verdict |
|---|---|---|
| "Fix the login timeout bug" | Confirm: is there a session/timeout change in diff? | ✅ / ❌ / ⚠️ |
| "Add email validation" | Confirm: is validation logic added to the relevant DTO/form? | ✅ / ❌ / ⚠️ |
| "AC: Error shown to user" | Confirm: is error UI rendered? Is error state handled? | ✅ / ❌ / ⚠️ |

**Verdict legend:**
- ✅ **Addressed** — code clearly implements this
- ❌ **Missing** — ticket requirement has no corresponding code change
- ⚠️ **Partial** — code change exists but doesn't fully satisfy the requirement
- ❓ **Can't tell** — not enough context from diff alone

### Step 5: Standard Code Quality Review
After the alignment audit, run the normal review:
- [Universal Checklist](#universal)
- Whichever of React / NestJS / Express checklists apply to the changed files
- Security pass from `references/security-checklist.md`
- Performance pass from `references/performance-checklist.md`

### Step 6: PR Review Output Format

```
## PR Review: [TICKET-KEY] — [Ticket Summary]

> **Type:** Bug / Story / Task
> **Priority:** High / Medium / Low
> **Ticket:** [link]

---

### 🎯 Problem → Solution Alignment

| Ticket Requirement | Code Evidence | Verdict |
|---|---|---|
| [requirement 1] | [file:line or "not found"] | ✅/❌/⚠️/❓ |
| [requirement 2] | [file:line or "not found"] | ✅/❌/⚠️/❓ |

**Alignment Score: X/Y requirements addressed**

---

### 🚨 Critical Issues (Must Fix Before Merge)
- [issue] — [why] — [fix]

### ⚠️ Important Issues (Fix Before Merge)
- [issue] — [why] — [fix]

### 💡 Suggestions
- [suggestion] — [benefit]

### ✅ What's Done Well
- [observation]

---

### 📋 Final Verdict

**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

[2–3 sentence summary covering: does the code solve the ticket? any blockers? overall quality?]
```

---

## Reference Files

Read these for in-depth patterns:

- `references/react-patterns.md` — React-specific anti-patterns with code examples
- `references/nestjs-patterns.md` — NestJS security, DI, validation patterns
- `references/express-patterns.md` — Express middleware, security, async patterns
- `references/security-checklist.md` — OWASP Top 10 mapped to Node.js/React code
- `references/performance-checklist.md` — React bundle, NestJS/Express DB, and Node.js runtime performance
