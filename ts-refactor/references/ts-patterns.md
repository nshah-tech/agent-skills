# Advanced TypeScript Patterns for Refactoring

## Table of Contents
1. [Eliminating `any`](#eliminating-any)
2. [Utility Types](#utility-types)
3. [Type Guards & Narrowing](#type-guards)
4. [Generic Patterns](#generics)
5. [Discriminated Unions](#discriminated-unions)
6. [Satisfies Operator](#satisfies)
7. [Module Patterns](#module-patterns)

---

## 1. Eliminating `any` {#eliminating-any}

### unknown + type guard (safest)
```typescript
// ❌ Before
function process(data: any) {
  return data.user.name;
}

// ✅ After
interface UserData {
  user: { name: string };
}

function isUserData(x: unknown): x is UserData {
  return (
    typeof x === 'object' && x !== null &&
    'user' in x && typeof (x as any).user?.name === 'string'
  );
}

function process(data: unknown): string {
  if (!isUserData(data)) throw new Error('Invalid data shape');
  return data.user.name;
}
```

### Template: API response typing
```typescript
// ❌ Before: any API response
const fetchUser = async (id: string): Promise<any> => {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
};

// ✅ After: typed with validation
interface User {
  id: string;
  name: string;
  email: string;
}

const fetchUser = async (id: string): Promise<User> => {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: unknown = await res.json();
  // Validate with zod, or your preferred schema library
  return UserSchema.parse(data); // or your own type guard
};
```

---

## 2. Utility Types {#utility-types}

### Common refactoring utilities
```typescript
// Partial — for update functions
type UpdateUserInput = Partial<User>;

// Required — enforce all optional become required
type RequiredConfig = Required<Config>;

// Pick — select a subset of props
type UserPreview = Pick<User, 'id' | 'name'>;

// Omit — remove fields
type UserWithoutPassword = Omit<User, 'password'>;

// Record — typed object map
type UserMap = Record<string, User>;

// ReturnType — infer return type from existing function
type FetchResult = ReturnType<typeof fetchUser>;

// Awaited — unwrap Promise
type UnwrappedUser = Awaited<ReturnType<typeof fetchUser>>;

// Parameters — get function param types
type FetchParams = Parameters<typeof fetchUser>;
```

---

## 3. Type Guards & Narrowing {#type-guards}

```typescript
// Predicate function
function isString(x: unknown): x is string {
  return typeof x === 'string';
}

// Exhaustive check for discriminated unions
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${JSON.stringify(x)}`);
}

// Null narrowing guard
function isDefined<T>(x: T | null | undefined): x is T {
  return x !== null && x !== undefined;
}

// Usage: filter out nulls safely
const validItems = items.filter(isDefined);
//    ^ typed as Item[], not (Item | null | undefined)[]
```

---

## 4. Generic Patterns {#generics}

```typescript
// Generic service function
async function fetchEntity<T>(url: string, schema: ZodSchema<T>): Promise<T> {
  const res = await fetch(url);
  return schema.parse(await res.json());
}

// Generic hook
function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    const stored = localStorage.getItem(key);
    return stored ? (JSON.parse(stored) as T) : initial;
  });
  // ...
}

// Constrained generic
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
```

---

## 5. Discriminated Unions {#discriminated-unions}

```typescript
// ❌ Before: loose state tracking
interface State {
  isLoading: boolean;
  data?: User;
  error?: string;
}

// ✅ After: discriminated union — impossible states become impossible types
type State =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: User }
  | { status: 'error'; error: string };

// TypeScript narrows correctly in each branch:
switch (state.status) {
  case 'success': return state.data.name; // data is User here
  case 'error': return state.error;       // error is string here
}
```

---

## 6. Satisfies Operator (TS 4.9+) {#satisfies}

```typescript
// Use satisfies to keep literal types while enforcing structure
const config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
  features: { darkMode: true, beta: false },
} satisfies AppConfig;

// config.apiUrl is still 'https://api.example.com' (literal), not string
// But TypeScript catches missing required fields from AppConfig
```

---

## 7. Module Patterns {#module-patterns}

### Barrel exports (index.ts)
```typescript
// features/user/index.ts — clean public API
export type { User, UserPreview } from './user.types';
export { UserCard } from './UserCard';
export { useUserProfile } from './hooks/useUserProfile';
// Do NOT export internals
```

### Namespace for related types
```typescript
// Instead of importing 20 types separately:
export namespace API {
  export interface GetUsersRequest { page: number; limit: number; }
  export interface GetUsersResponse { users: User[]; total: number; }
  export type UserEndpoint = '/users' | '/users/:id';
}
```

### Splitting a large file
```
Before: UserService.ts (400 lines — queries, mutations, transforms, types)

After:
  user.types.ts         ← interfaces, type aliases
  user.transforms.ts    ← pure data transformation functions
  user.queries.ts       ← read operations (GET)
  user.mutations.ts     ← write operations (POST/PUT/DELETE)
  user.service.ts       ← re-exports as a clean facade
```
