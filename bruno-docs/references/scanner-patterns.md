# Scanner Patterns Reference

Patterns the `generate_bruno.py` script uses to detect routes.
Useful when debugging why a route wasn't picked up.

---

## NestJS Patterns

### Controller detection
Files scanned: any `.ts` file (excluding `node_modules`, `dist`, `.spec.`, `.test.`)
that contains `@Controller(` OR is named `*.controller.ts`.

```ts
// Detected: string prefix
@Controller('users')
@Controller("api/users")

// Detected: object with path
@Controller({ path: 'users', version: '1' })

// Detected: no prefix (root)
@Controller()
```

### HTTP method decorators
```ts
@Get()              -> GET    /prefix
@Get(':id')         -> GET    /prefix/:id
@Get('me/profile')  -> GET    /prefix/me/profile
@Post()             -> POST   /prefix
@Put(':id')         -> PUT    /prefix/:id
@Patch(':id')       -> PATCH  /prefix/:id
@Delete(':id')      -> DELETE /prefix/:id
```

### Auth detection (class-level and method-level)

| Decorator/Pattern | Auth assigned |
|-------------------|--------------|
| `@UseGuards(JwtAuthGuard)` | `bearer` |
| `@UseGuards(AuthGuard)` | `bearer` |
| `@UseGuards(AccessTokenGuard)` | `bearer` |
| `@UseGuards(BasicAuthGuard)` | `basic` |
| `@UseGuards(ApiKeyGuard)` | `apikey` |
| `@Public()` | `none` (overrides class guard) |
| No guard decorator | inherits class-level |

Class-level `@UseGuards` applies to all methods.
Method-level overrides class-level.
`@Public()` always wins — sets `auth: none`.

### Parameter detection

```ts
@Param('id')         -> adds id to params:path
@Param()             -> reads from path pattern
@Query('page')       -> adds page to params:query
@Query()             -> adds placeholder params:query block
@Body()              -> generates body:json block
```

### Body detection
A `body:json` block is generated when:
- `@Body()` or `@Body(` is found in the method, OR
- The HTTP method is POST, PUT, or PATCH (auto-assumed to have a body)

---

## Express Patterns

### Router variable detection
```ts
const router = express.Router()
const router = Router()
const usersRouter = express.Router()
```
The variable name (`router`, `usersRouter`, etc.) is tracked to match against route definitions.

### Route definition patterns
```ts
router.get('/path', handler)
router.post('/path', middleware, handler)
router.put('/path', auth, validate, handler)
router.patch('/path', handler)
router.delete('/path', handler)

app.get('/path', handler)
app.post('/path', handler)
```

### Router mounting (prefix resolution)
Scanned in entry files: `app.ts`, `main.ts`, `server.ts`, `index.ts`, `routes/index.ts`

```ts
app.use('/api/users', usersRouter)   -> prefix /api/users
app.use('/api', apiRouter)           -> prefix /api
```

If a router variable is found in `mount_map`, its routes get the mounted prefix.
If NOT found (inline routers, dynamic mounting), the prefix is guessed from the filename:

```
users.routes.ts      -> /users
auth.router.ts       -> /auth
orders.ts            -> /orders
```

Files named `app`, `main`, `server`, `index`, `routes` get no prefix guess.

### Auth middleware detection

| Middleware name (anywhere in route handler args) | Auth |
|----------------------------------------------|------|
| `authenticate` | bearer |
| `verifyToken` | bearer |
| `requireAuth` | bearer |
| `isAuthenticated` | bearer |
| `passport.authenticate` | bearer |
| `jwtMiddleware` | bearer |
| `authMiddleware` | bearer |
| `TokenGuard` | bearer |
| `basicAuth` | basic |
| `basic-auth` | basic |
| `BasicAuthGuard` | basic |
| `apiKey` | apikey |
| `x-api-key` | apikey |
| `ApiKeyGuard` | apikey |

---

## Known Limitations

### NestJS
- Dynamic module prefixes (e.g., `forRoot()` injected paths) are not resolved
- Versioned controllers (`@Controller({ version: '2' })`) extract the path but ignore version — add it manually
- DTO class introspection is not performed; body fields are left blank for the user to fill in

### Express
- Chained route definitions (`router.route('/path').get(...).post(...)`) are not yet detected
- Dynamic `app.use()` calls where the path is a variable are not resolved
- Nested routers (router mounted inside another router) may not resolve the full prefix — verify the generated URL

### Both
- Auth is inferred from naming conventions, not from actual logic. Always verify generated `auth:` values.
- The scanner reads files statically with regex, not via a TypeScript/AST parser. Heavily dynamic codebases may need manual adjustments.

---

## Troubleshooting

**Route not found:**
- Make sure the file isn't in `dist/`, `node_modules/`, or `*.spec.ts`
- For NestJS: verify `@Controller` is present in the file
- For Express: verify the file has `router.METHOD(` or `app.METHOD(`

**Wrong auth detected:**
- Manually set the `auth:` value in the method block after generation
- The block will be preserved on the next `/update-bruno` run (it's code-owned, but you can override it)

**Wrong prefix on Express routes:**
- Add a `app.use('/correct-prefix', yourRouter)` entry in your app entry file
- Or pass `--framework nestjs` if you accidentally scanned an Express project with NestJS scanner

**Body block not generated:**
- Check that `@Body()` is in the method signature (NestJS)
- For Express, POST/PUT/PATCH always get a body block by default
