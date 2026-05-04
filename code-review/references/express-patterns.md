# Express Patterns — Deep Reference

## Table of Contents
1. [Security Must-Haves](#security)
2. [Async Error Handling](#async)
3. [Middleware Order](#middleware)
4. [Input Validation](#validation)
5. [Response Patterns](#responses)
6. [Common Hidden Bugs](#hidden-bugs)

---

## 1. Security Must-Haves {#security}

### Baseline Security Setup
```typescript
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';

const app = express();

// ✅ Security headers
app.use(helmet());

// ✅ CORS — never use origin: '*' in production
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') ?? [],
  credentials: true,
}));

// ✅ Rate limiting on all routes
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));

// ✅ Stricter rate limiting on auth endpoints
const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 10 });
app.use('/api/auth', authLimiter);

// ✅ Body parsing with size limits
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true, limit: '10kb' }));
```

### ❌ Path Traversal
```typescript
// WRONG — user can pass ../../etc/passwd
app.get('/file', (req, res) => {
  const file = path.join(__dirname, req.query.name);
  res.sendFile(file);
});

// ✅ CORRECT — validate and sanitize
app.get('/file', (req, res) => {
  const name = path.basename(req.query.name as string); // strips path components
  const file = path.join(__dirname, 'uploads', name);
  if (!file.startsWith(path.join(__dirname, 'uploads'))) {
    return res.status(400).json({ error: 'Invalid file path' });
  }
  res.sendFile(file);
});
```

### ❌ Prototype Pollution via req.body
```typescript
// WRONG — merge can pollute Object.prototype
Object.assign(target, req.body);

// ✅ CORRECT — use spread with validated fields only
const { name, email } = req.body; // destructure known fields
const user = { name, email };
```

---

## 2. Async Error Handling {#async}

### ❌ Async handler without try/catch crashes Express 4
```typescript
// WRONG — unhandled Promise rejection, no error response
app.get('/users', async (req, res) => {
  const users = await db.query('SELECT * FROM users');
  res.json(users);
  // if db.query throws → unhandled rejection
});

// ✅ OPTION A — explicit try/catch
app.get('/users', async (req, res, next) => {
  try {
    const users = await db.query('SELECT * FROM users');
    res.json(users);
  } catch (err) {
    next(err); // passes to error handler
  }
});

// ✅ OPTION B — asyncHandler wrapper (recommended for many routes)
const asyncHandler = (fn: Function) => (req: Request, res: Response, next: NextFunction) =>
  Promise.resolve(fn(req, res, next)).catch(next);

app.get('/users', asyncHandler(async (req, res) => {
  const users = await db.query('SELECT * FROM users');
  res.json(users);
}));
```

### ❌ Error middleware missing 4th argument
```typescript
// WRONG — Express won't recognize this as error middleware
app.use((err, req, res) => {
  res.status(500).json({ error: err.message });
});

// ✅ CORRECT — must have exactly 4 parameters
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  const status = (err as any).status ?? 500;
  res.status(status).json({
    error: process.env.NODE_ENV === 'production' ? 'Internal server error' : err.message,
  });
});
```

---

## 3. Middleware Order {#middleware}

### ❌ Wrong middleware order
```typescript
// WRONG — body parser after routes, auth after routes
app.get('/users', authMiddleware, handler);
app.use(express.json()); // too late!
app.use(authMiddleware);  // too late!

// ✅ CORRECT — global middleware BEFORE routes
app.use(helmet());
app.use(cors(corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(requestLogger);
app.use(rateLimit(options));

// Then routes
app.use('/api/auth', authRoutes);
app.use('/api/users', authenticate, userRoutes);

// Error handler LAST
app.use(notFoundHandler);
app.use(errorHandler);
```

---

## 4. Input Validation {#validation}

### ❌ No validation on route parameters
```typescript
// WRONG — SQL injection or invalid ID crash DB
app.get('/users/:id', async (req, res) => {
  const user = await db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);
  res.json(user);
});

// ✅ CORRECT — validate params, use parameterized queries
import Joi from 'joi';
// or use express-validator, zod, etc.

app.get('/users/:id', async (req, res, next) => {
  const { error, value } = Joi.string().uuid().validate(req.params.id);
  if (error) return res.status(400).json({ error: 'Invalid user ID' });

  const user = await db.query('SELECT * FROM users WHERE id = $1', [value]);
  res.json(user);
});
```

### Using Zod for validation (recommended)
```typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  role: z.enum(['user', 'admin']).default('user'),
});

app.post('/users', (req, res, next) => {
  const result = createUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.flatten() });
  }
  // result.data is fully typed
  next();
});
```

---

## 5. Response Patterns {#responses}

### ❌ No response sent (hangs)
```typescript
// WRONG — if condition fails, no response → connection hangs forever
app.get('/users/:id', async (req, res) => {
  const user = await userService.findById(req.params.id);
  if (user) {
    res.json(user);
  }
  // missing else → no response sent!
});

// ✅ CORRECT — every branch sends response
app.get('/users/:id', async (req, res, next) => {
  try {
    const user = await userService.findById(req.params.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (err) { next(err); }
});
```

### ❌ Double response
```typescript
// WRONG — res.json called twice
if (error) {
  res.status(400).json({ error }); // sends response
}
res.json(data); // crashes: "Cannot set headers after they are sent"

// ✅ CORRECT — use return
if (error) {
  return res.status(400).json({ error });
}
res.json(data);
```

---

## 6. Common Hidden Bugs {#hidden-bugs}

### Missing await causes Promise in response
```typescript
// BUG — sends "[object Promise]"
app.get('/data', (req, res) => {
  const data = fetchData(); // missing await
  res.json(data);           // sends Promise object
});
```

### Route order conflicts
```typescript
// BUG — /users/me never reached because /:id catches it first
app.get('/users/:id', getUserById);
app.get('/users/me', getCurrentUser); // unreachable!

// ✅ CORRECT — specific routes first
app.get('/users/me', getCurrentUser);
app.get('/users/:id', getUserById);
```

### JSON middleware missing for POST body
```typescript
// BUG — req.body is undefined
app.post('/users', (req, res) => {
  console.log(req.body); // undefined!
});

// Fix: ensure express.json() is before this route
app.use(express.json());
```

### Cookie security flags missing
```typescript
// WRONG
res.cookie('token', jwt, { httpOnly: true });

// ✅ CORRECT
res.cookie('token', jwt, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 24 * 60 * 60 * 1000,
});
```
