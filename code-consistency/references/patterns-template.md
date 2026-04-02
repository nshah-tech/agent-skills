# CONTRIBUTION.md — Antigravity Codebase Guidelines

> **This file is the single source of truth for codebase patterns.**
> Before writing any code, read this file. After establishing any new pattern, update this file.
> Last updated: [DATE]

---

## Stack

- **Runtime**: Node.js with TypeScript
- **Backend framework**: Express
- **ORM**: TypeORM
- **Frontend**: React (Web) with TypeScript
- **State management**: [FILL IN — e.g. Redux Toolkit / Zustand / Context]
- **Styling**: [FILL IN — e.g. Tailwind / CSS Modules / styled-components]
- **Testing**: [FILL IN — e.g. Jest / Vitest / Playwright]
- **Package manager**: [FILL IN — npm / yarn / pnpm]

---

## Project Structure

```
[FILL IN after scanning the project — example below]

src/
├── api/
│   ├── routes/          # Express route definitions
│   ├── controllers/     # Request handlers
│   ├── middlewares/     # Express middlewares
│   └── validators/      # Input validation
├── services/            # Business logic
├── repositories/        # TypeORM data access layer
├── entities/            # TypeORM entity definitions
├── types/               # Shared TypeScript types & interfaces
├── utils/               # Pure utility/helper functions
└── config/              # App configuration

client/
├── src/
│   ├── components/      # Reusable React components
│   ├── pages/           # Page-level components
│   ├── hooks/           # Custom React hooks
│   ├── store/           # State management
│   ├── services/        # API call functions
│   └── types/           # Frontend TypeScript types
```

---

## File Naming Conventions

| File type | Convention | Example |
|---|---|---|
| Express route | `[domain].routes.ts` | `user.routes.ts` |
| Controller | `[domain].controller.ts` | `user.controller.ts` |
| Service | `[domain].service.ts` | `user.service.ts` |
| Repository | `[domain].repository.ts` | `user.repository.ts` |
| TypeORM entity | `[Domain].entity.ts` | `User.entity.ts` |
| DTO | `[domain].dto.ts` | `create-user.dto.ts` |
| React component | `PascalCase.tsx` | `UserCard.tsx` |
| React hook | `use[Name].ts` | `useAuth.ts` |
| Utility | `[name].util.ts` or `[name].ts` | `date.util.ts` |
| Type file | `[domain].types.ts` | `user.types.ts` |

---

## TypeScript Conventions

```typescript
// ✅ Prefer interface for object shapes
interface User {
  id: number;
  email: string;
  createdAt: Date;
}

// ✅ Use type for unions and computed types
type UserRole = 'admin' | 'user' | 'guest';
type UserWithRole = User & { role: UserRole };

// ✅ Always declare explicit return types on functions
async function getUserById(id: number): Promise<User | null> { ... }

// ✅ Use string[] not Array<string>
const ids: number[] = [];

// ✅ DTOs are separate typed classes/interfaces from entities
interface CreateUserDto {
  email: string;
  password: string;
}

// ✅ Null vs undefined — [FILL IN preference after observing codebase]
```

---

## Express Patterns

### Route Definition
```typescript
// [FILL IN with actual pattern from codebase — example:]
import { Router } from 'express';
import { UserController } from '../controllers/user.controller';

const router = Router();
const userController = new UserController();

router.get('/', userController.getAll);
router.get('/:id', userController.getById);
router.post('/', userController.create);

export default router;
```

### Controller Structure
```typescript
// [FILL IN with actual pattern — example:]
export class UserController {
  async getById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const user = await userService.getById(Number(id));
      res.json({ data: user });
    } catch (error) {
      next(error);
    }
  }
}
```

### Response Shape
```typescript
// Success
res.json({ data: result, message: 'Success' });

// Error (via central error handler — do not return errors directly)
// [FILL IN actual error response shape]
```

### Validation
```typescript
// [FILL IN — class-validator / zod / joi / manual]
```

---

## TypeORM Patterns

> **Critical**: All repositories in this codebase use ONE query style. Do not mix styles.

### Active Style: [FILL IN — QueryBuilder OR find() — after observing existing repositories]

#### If using QueryBuilder:
```typescript
// ✅ Correct — matches existing pattern
async findByEmail(email: string): Promise<User | null> {
  return this.userRepository
    .createQueryBuilder('user')
    .where('user.email = :email', { email })
    .getOne();
}

// ✅ With relations
async findWithOrders(userId: number): Promise<User | null> {
  return this.userRepository
    .createQueryBuilder('user')
    .leftJoinAndSelect('user.orders', 'order')
    .where('user.id = :userId', { userId })
    .getOne();
}
```

#### If using find():
```typescript
// ✅ Correct — matches existing pattern
async findByEmail(email: string): Promise<User | null> {
  return this.userRepository.findOne({ where: { email } });
}

// ✅ With relations
async findWithOrders(userId: number): Promise<User | null> {
  return this.userRepository.findOne({
    where: { id: userId },
    relations: ['orders'],
  });
}
```

### Transactions
```typescript
// [FILL IN actual transaction pattern from codebase]
```

### Repository Injection
```typescript
// [FILL IN — @InjectRepository or dataSource.getRepository]
@Injectable()
export class UserRepository {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}
}
```

---

## React Component Patterns

### Component Structure
```typescript
// [FILL IN with actual observed pattern — example:]
import { useState, useEffect } from 'react';
import styles from './UserCard.module.css'; // or Tailwind classes

interface Props {
  userId: number;
  onSelect?: (id: number) => void;
}

export function UserCard({ userId, onSelect }: Props) {
  // 1. State
  const [user, setUser] = useState<User | null>(null);

  // 2. Effects
  useEffect(() => {
    // fetch user
  }, [userId]);

  // 3. Event handlers
  const handleClick = () => {
    onSelect?.(userId);
  };

  // 4. Render
  return (
    <div onClick={handleClick}>
      {user?.name}
    </div>
  );
}
```

### Key Rules
- **Declaration**: `[FILL IN — function or arrow function const]`
- **Export**: `[FILL IN — named or default]`
- **Props interface**: Above the component, named `Props` or `[ComponentName]Props`
- **Event handlers**: Prefixed with `handle` (e.g., `handleSubmit`, `handleChange`)
- **Conditional rendering**: `[FILL IN — ternary, &&, or early return preference]`

---

## State Management

### Library: [FILL IN]

```typescript
// [FILL IN actual pattern — example for Redux Toolkit:]

// Slice naming: [domain]Slice
// Action naming: camelCase verb-first

export const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setCurrentUser: (state, action: PayloadAction<User>) => {
      state.currentUser = action.payload;
    },
  },
});
```

---

## Naming Conventions

| Thing | Convention |
|---|---|
| Classes | `PascalCase` |
| Interfaces | `PascalCase` (no `I` prefix) |
| Type aliases | `PascalCase` |
| Functions / methods | `camelCase`, verb-first |
| Variables | `camelCase` |
| Constants | `SCREAMING_SNAKE_CASE` for module-level, `camelCase` for local |
| Booleans | `isX`, `hasX`, `canX`, `shouldX` prefix |
| Event handlers (React) | `handleX` |
| Custom hooks | `useX` |
| Enum names | `PascalCase` |
| Enum values | `[FILL IN — PascalCase or SCREAMING_SNAKE_CASE]` |
| API route paths | `[FILL IN — /kebab-case or /camelCase]` |

---

## Import Ordering

```typescript
// 1. Node built-ins
import path from 'path';

// 2. External packages
import { Repository } from 'typeorm';
import { Injectable } from '@nestjs/common';

// 3. Internal absolute imports (aliased)
import { UserService } from '@/services/user.service';

// 4. Relative imports
import { CreateUserDto } from './create-user.dto';

// 5. Type-only imports (last)
import type { User } from './User.entity';
```

Blank line between each group: **[FILL IN — yes/no]**

---

## Error Handling

```typescript
// [FILL IN after observing the error handling pattern]

// Custom error class used:
throw new AppError(400, 'User not found');

// Or:
throw new Error('User not found');
```

- Errors are caught by: `[FILL IN — central error middleware / asyncHandler wrapper / inline]`
- Logging: `[FILL IN — console / winston / pino]`
- Error response shape: `[FILL IN]`

---

## Comment Style

- JSDoc on: `[FILL IN — all exported functions / public methods only / none]`
- Inline comments: For non-obvious logic only
- TODOs: `// TODO: description` or `// TODO(name): description`

---

## Changelog

| Date | Change | Author |
|---|---|---|
| [DATE] | Initial generation by Claude | AI |

> Append a row here every time a new pattern is documented or an existing pattern changes.
