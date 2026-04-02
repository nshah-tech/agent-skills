# Code Observation Checklist

Use this when completing Step 3 of the Code Consistency Workflow.
Read 2–3 existing files in the same layer as your task, then verify each item below.

---

## 1. File & Folder Structure

- [ ] **File naming**: Is it `kebab-case.ts`, `camelCase.ts`, `PascalCase.ts`, or `PascalCase.tsx`?
  - Controllers: `user.controller.ts` or `UserController.ts`?
  - Services: `user.service.ts` or `UserService.ts`?
  - React components: `UserCard.tsx` or `user-card.tsx`?
- [ ] **Folder placement**: Which folder does this type of file live in?
  - Is there a `controllers/`, `services/`, `repositories/`, `entities/` structure?
  - Are React components in `components/`, `pages/`, `views/`, or domain-based folders?
- [ ] **Barrel files**: Does the folder use `index.ts` to re-export? Match that.
- [ ] **Co-location**: Are tests, styles, or types co-located with the file or in separate folders?

---

## 2. TypeScript Conventions

- [ ] **`interface` vs `type`**: Which does the codebase prefer for object shapes? For unions?
- [ ] **Explicit return types**: Do functions declare their return type explicitly (`: Promise<User>`) or rely on inference?
- [ ] **Generic style**: `Array<string>` or `string[]`? `Promise<void>` or inferred?
- [ ] **Null handling**: `undefined` vs `null` — which is used and where?
- [ ] **Optional chaining**: Is `?.` used liberally or only where necessary?
- [ ] **Type assertion**: `as Type` or `<Type>` casting? Or avoided entirely?
- [ ] **Enums vs union types**: Does the codebase use `enum` or `'value1' | 'value2'`?
- [ ] **DTO/Entity separation**: Are DTOs explicitly typed and separate from entities?

---

## 3. Express Patterns

- [ ] **Router structure**: How are routes registered? (`router.get(...)` in a separate file, or in the controller?)
- [ ] **Controller shape**: Are controllers classes with methods, or plain exported functions?
- [ ] **Middleware order**: What middleware is applied at the router level vs route level?
- [ ] **Request/Response typing**: Is `req: Request<Params, Body, Query>` typed explicitly?
- [ ] **Response shape**: What does a success response look like? `res.json({ data, message })` or `res.json(data)`?
- [ ] **Error handling**: Are errors thrown and caught by a central error handler, or handled inline?
- [ ] **Status codes**: Are HTTP status codes set explicitly or defaulted?
- [ ] **Validation**: Where is input validation done? (class-validator, zod, joi, manual?)

---

## 4. TypeORM Query Patterns

This is critical — the most common source of inconsistency.

- [ ] **Query style**: Does this repository use `QueryBuilder`, `.find()/.findOne()`, or raw SQL?
  - **Never mix styles** within a single repository file.
- [ ] **QueryBuilder chaining**: What alias naming convention is used? (`.from(User, 'user')` or `'u'`?)
- [ ] **Relation loading**: `leftJoinAndSelect` vs `relations: ['relation']` option?
- [ ] **Transaction style**: `queryRunner`, `@Transactional()`, or `dataSource.transaction()`?
- [ ] **Repository injection**: Is it `@InjectRepository(Entity)` or `dataSource.getRepository(Entity)`?
- [ ] **Where clauses**: Object literal `{ where: { id } }` or `.where('user.id = :id', { id })`?
- [ ] **Pagination**: How is limit/offset applied? `.take()/.skip()` or raw SQL?
- [ ] **Soft deletes**: Is `@DeleteDateColumn()` / `softDelete()` used?

---

## 5. React Component Patterns

- [ ] **Component declaration**: `function MyComponent()` or `const MyComponent = () =>`?
- [ ] **Props typing**: `interface Props {}` or `type Props = {}` — declared inline or above the component?
- [ ] **Export style**: Named export (`export function`) or default export (`export default`)?
- [ ] **Hook order**: What is the conventional order of hooks inside a component?
  - (e.g., `useState` → `useEffect` → custom hooks → event handlers → render)
- [ ] **Conditional rendering**: Ternary, `&&` short-circuit, or early return?
- [ ] **Children prop**: Explicitly typed as `React.ReactNode` or inferred?
- [ ] **Event handlers**: Named `handleX` (e.g., `handleSubmit`) or `onX` (e.g., `onClick`)?
- [ ] **Ref usage**: `useRef<HTMLElement>(null)` style?
- [ ] **Styling**: CSS modules? Tailwind? styled-components? Inline styles?
- [ ] **Fragment usage**: `<>...</>` or `<React.Fragment>...</React.Fragment>`?

---

## 6. State Management

- [ ] **State library**: Redux Toolkit? Zustand? React Context? Jotai? Something else?
- [ ] **Store structure**: How is state organized — by domain, by feature, by page?
- [ ] **Action naming**: camelCase, SCREAMING_SNAKE_CASE, or `domain/actionName`?
- [ ] **Selector pattern**: Inline selectors or named selector functions?
- [ ] **Async actions**: `createAsyncThunk`? Custom middleware? TanStack Query?
- [ ] **Local vs global state**: What rule determines what goes in global vs local state?
- [ ] **State update style**: Mutating draft (Immer)? Spreading? Replace entirely?

---

## 7. Naming Conventions

| Thing | Convention to check |
|---|---|
| Files | kebab-case / PascalCase / camelCase? |
| Classes | PascalCase (always) |
| Interfaces/Types | `IUser` prefix? `UserDto` suffix? No prefix/suffix? |
| Constants | `SCREAMING_SNAKE_CASE` or `camelCase`? |
| Enums | PascalCase for enum name, what for values? |
| Functions | camelCase verb-first (`getUser`, `createOrder`)? |
| Variables | camelCase, descriptive? Abbreviations allowed? |
| Boolean vars | `isLoading`, `hasError`, `canEdit` — `is/has/can` prefix? |
| Event handlers | `handleX` or `onX`? |
| React hooks | `useX` always |
| API endpoints | `/kebab-case`, `/camelCase`, or `/snake_case`? |

---

## 8. Import Ordering

Check what order imports appear in existing files:

```
1. Node.js built-ins (path, fs, crypto)
2. External packages (express, typeorm, react)
3. Internal absolute imports (@/services, @/entities)
4. Relative imports (./user.service, ../entities/user)
5. Type-only imports (import type { ... })
```

Is there a blank line between each group? Is there an ESLint rule enforcing this?

---

## 9. Error Handling

- [ ] **Error class**: Custom error classes (`AppError`, `HttpException`) or native `Error`?
- [ ] **Throwing style**: `throw new AppError(400, 'message')` or `throw new Error('message')`?
- [ ] **Try/catch scope**: Wrap entire function body, or only specific risky calls?
- [ ] **Async error propagation**: `try/catch` or unhandled rejection — is `asyncHandler` used?
- [ ] **Logging**: `console.error`, `winston`, `pino` — where and how are errors logged?
- [ ] **Error response shape**: What does a failed API response look like?

---

## 10. Comment & Documentation Style

- [ ] **JSDoc**: Used on public functions? On all functions? Not at all?
- [ ] **Inline comments**: Are `//` comments used? For what? (non-obvious logic only, or freely?)
- [ ] **TODO format**: `// TODO:`, `// TODO(name):`, or a different format?
- [ ] **Deprecation**: `@deprecated` JSDoc or inline comment?
