---
name: bruno-docs
description: >
  Use this skill to create, update, or maintain Bruno API collections and .bru request
  files. Triggers when the user wants to generate Bruno files from an Express or NestJS
  codebase, sync Bruno with existing routes, run /update-bruno, write or edit .bru files
  by hand, set up a Bruno collection folder structure, manage Bruno environment files, or
  keep Bruno in sync after adding new API routes. This skill is about authoring and
  maintaining the Bruno collection itself — not about running it. For running bru commands,
  CI/CD, and scripting, use the bruno-cli skill instead.
---

# Bruno Docs Skill

This skill covers everything about **creating and maintaining** Bruno collections:
- Auto-generating `.bru` files from Express or NestJS source code via `/update-bruno`
- Writing and editing `.bru` files by hand
- Setting up collection folder structure and environment files
- Keeping Bruno in sync as your API evolves

Bruno lives inside your project under a `bruno/` folder (typically a git submodule).

---

## `/update-bruno` — Auto-Sync Routes from Code

The primary workflow. Scans your Express or NestJS project and generates or updates `.bru` files inside `bruno/` without touching your hand-written scripts and tests.

```bash
# Auto-detect framework (reads package.json)
python bruno/scripts/generate_bruno.py

# Specify framework
python bruno/scripts/generate_bruno.py --framework nestjs
python bruno/scripts/generate_bruno.py --framework express
python bruno/scripts/generate_bruno.py --framework both

# Preview changes without writing anything
python bruno/scripts/generate_bruno.py --dry-run

# Full options
python bruno/scripts/generate_bruno.py \
  --project-path /path/to/project \
  --base-url http://localhost:4000 \
  --envs local,staging,production \
  --collection-name "My API"
```

### What gets updated vs preserved

| Block | Who owns it | Behavior |
|-------|------------|---------|
| `meta` (name, seq) | Code | ✏ Always updated |
| Method block (url, auth) | Code | ✏ Always updated |
| `params:path` | Code | ✏ Always updated |
| `headers` (base headers) | Code | ✏ Always updated |
| `auth:bearer/basic/apikey` | Code | ✏ Always updated |
| `params:query` | User | 🔒 Preserved if customized |
| `body:json` | User | 🔒 Preserved if customized |
| `assert` | User | 🔒 Preserved if assertions added |
| `script:pre-request` | User | 🔒 Always preserved |
| `script:post-response` | User | 🔒 Always preserved |
| `tests` | User | 🔒 Preserved if tests added |
| `docs` | User | 🔒 Preserved if customized |

### What Claude does when you say /update-bruno

1. Confirm `bruno/scripts/generate_bruno.py` exists (instruct to install the skill if not)
2. Detect the framework from `package.json`
3. Run the script or show the exact command to run
4. Report created / updated / unchanged counts
5. Suggest `bru run --env local` to validate

---

## Project Structure

```
your-project/
├── src/
│   ├── users/
│   │   └── users.controller.ts      <- NestJS controller
│   └── routes/
│       └── users.routes.ts          <- Express router
├── package.json
└── bruno/                           <- git submodule
    ├── bruno.json                   <- collection config
    ├── scripts/
    │   └── generate_bruno.py        <- scanner (this skill)
    ├── environments/
    │   ├── local.bru
    │   ├── staging.bru
    │   └── production.bru
    └── users/                       <- one folder per resource
        ├── get-users.bru
        ├── get-user-by-id.bru
        ├── create-user.bru
        └── update-user.bru
```

### `bruno.json`

```json
{
  "version": "1",
  "name": "My API",
  "type": "collection",
  "ignore": ["node_modules", ".git"]
}
```

---

## What the Scanner Detects

### NestJS

| Source code | Bruno output |
|-------------|-------------|
| `@Controller('users')` | Route prefix `/users` |
| `@Get(':id')` | `GET /users/:id` |
| `@Post()` | `POST /users` with `body:json` |
| `@UseGuards(JwtAuthGuard)` | `auth: bearer` |
| `@UseGuards(BasicAuthGuard)` | `auth: basic` |
| `@Public()` | `auth: none` (overrides class guard) |
| `@Param('id')` | `params:path { id: {{id}} }` |
| `@Query('page')` | `params:query { page: }` |
| `@Body()` | `body:json { }` |

### Express

| Source code | Bruno output |
|-------------|-------------|
| `router.get('/users', ...)` | `GET /users` |
| `app.use('/api', router)` | Prefix `/api` applied to all router routes |
| `authenticate` middleware | `auth: bearer` |
| `verifyToken` middleware | `auth: bearer` |
| Filename `users.routes.ts` | Folder `/users` (fallback if no mount found) |
| POST/PUT/PATCH routes | `body:json` block auto-added |

See `references/scanner-patterns.md` for the full pattern list and troubleshooting.

---

## Writing `.bru` Files by Hand

For the complete block-by-block syntax, see `references/bru-lang-blocks.md`.

### GET request

```bru
meta {
  name: Get User by ID
  type: http
  seq: 1
}

get {
  url: {{baseUrl}}/users/{{id}}
  auth: bearer
}

params:path {
  id: {{id}}
}

headers {
  Accept: application/json
}

auth:bearer {
  token: {{authToken}}
}

assert {
  res.status: eq 200
  res.body.id: isDefined
}

tests {
  test("returns user", function () {
    expect(res.getStatus()).to.equal(200);
    expect(res.getBody()).to.have.property("id");
  });
}
```

### POST request

```bru
meta {
  name: Create User
  type: http
  seq: 2
}

post {
  url: {{baseUrl}}/users
  auth: bearer
}

headers {
  Content-Type: application/json
}

auth:bearer {
  token: {{authToken}}
}

body:json {
  {
    "name": "{{name}}",
    "email": "{{email}}"
  }
}

vars:post-response {
  newUserId: res.body.id
}

assert {
  res.status: eq 201
  res.body.id: isDefined
}
```

---

## The `docs` Block — Request Documentation

Every `.bru` file should have a `docs` block. It is a **Markdown text block** that renders as a "Docs" tab in the Bruno UI, giving anyone reading the collection a complete picture of the endpoint without needing to open the source code.

The `docs` block lives at the **end** of the `.bru` file and is always user-owned — the scanner generates a starter template on first creation, but never overwrites it after that.

### What to put in a docs block

A well-written `docs` block covers four things:

1. **Overview** — what the endpoint does and when to use it
2. **Request shape** — path params, query params, body fields with types and required/optional markers
3. **All possible responses** — every status code the endpoint can return, with example payloads
4. **Notes** — rate limits, deprecation warnings, links to related endpoints

### Full template

```bru
docs {
  # Create User

  `POST` `/api/users`

  ## Overview
  Creates a new user account. The email must be unique across the system.
  Returns the created user with their assigned ID.

  ## Authentication
  Requires a valid Bearer token with `admin` role.

  ## Request

  ### Body
  | Field      | Type   | Required | Description                        |
  |------------|--------|----------|------------------------------------|
  | `name`     | string | ✅ Yes   | Full display name                  |
  | `email`    | string | ✅ Yes   | Valid email, must be unique        |
  | `role`     | string | ❌ No    | `"admin"` \| `"user"` \| `"guest"`. Defaults to `"user"` |
  | `metadata` | object | ❌ No    | Arbitrary key-value pairs          |

  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "admin"
  }
  ```

  ## Responses

  ### ✅ 201 Created
  User was created successfully.
  ```json
  {
    "id": "user_abc123",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "admin",
    "createdAt": "2024-01-15T10:30:00Z"
  }
  ```

  ### ❌ 400 Bad Request
  One or more fields failed validation.
  ```json
  {
    "error": "VALIDATION_ERROR",
    "message": "email is required",
    "fields": { "email": "must be a valid email address" }
  }
  ```

  ### ❌ 401 Unauthorized
  Bearer token is missing or expired.
  ```json
  { "error": "UNAUTHORIZED", "message": "Bearer token is missing or expired" }
  ```

  ### ❌ 403 Forbidden
  Authenticated but insufficient permissions.
  ```json
  { "error": "FORBIDDEN", "message": "Admin role required to create users" }
  ```

  ### ❌ 409 Conflict
  A user with this email already exists.
  ```json
  { "error": "CONFLICT", "message": "A user with this email already exists" }
  ```

  ### ❌ 429 Too Many Requests
  ```json
  { "error": "RATE_LIMITED", "retryAfter": 30 }
  ```

  ### ❌ 500 Internal Server Error
  ```json
  { "error": "INTERNAL_ERROR", "message": "An unexpected error occurred" }
  ```

  ## Notes
  - Rate limit: 10 requests/min per IP
  - The `id` field is a UUID v4 and is assigned server-side
}
```

### Docs block in a complete `.bru` file

The `docs` block goes last, after `tests`:

```bru
meta {
  name: Create User
  type: http
  seq: 2
}

post {
  url: {{baseUrl}}/users
  auth: bearer
}

headers {
  Content-Type: application/json
}

auth:bearer {
  token: {{authToken}}
}

body:json {
  {
    "name": "{{name}}",
    "email": "{{email}}",
    "role": "user"
  }
}

assert {
  res.status: eq 201
  res.body.id: isDefined
}

tests {
  test("user created", function () {
    expect(res.getStatus()).to.equal(201);
    expect(res.getBody()).to.have.property("id");
    bru.setVar("newUserId", res.getBody().id);
  });
}

docs {
  # Create User

  `POST` `/api/users`

  ## Overview
  Creates a new user. Email must be unique.

  ## Authentication
  Bearer token required. Admin role only.

  ## Request Body
  | Field   | Type   | Required | Description       |
  |---------|--------|----------|-------------------|
  | `name`  | string | ✅ Yes   | Full display name |
  | `email` | string | ✅ Yes   | Unique email      |
  | `role`  | string | ❌ No    | Defaults to "user"|

  ## Responses
  | Status | Meaning                        |
  |--------|--------------------------------|
  | 201    | User created successfully      |
  | 400    | Validation error               |
  | 401    | Missing or invalid token       |
  | 403    | Insufficient permissions       |
  | 409    | Email already in use           |
  | 500    | Server error                   |
}
```

### What the scanner generates automatically

When `/update-bruno` creates a new `.bru` file, it generates a starter `docs` block with:
- The method, path, and inferred name filled in
- Auth section based on detected guard
- Placeholder sections for body, path params, and responses
- Common response codes pre-populated (200/201, 400, 401, 404, 500)

You fill in the field types, descriptions, and exact response payloads — the scanner handles the scaffolding.

For complete `docs` block syntax including all Markdown features, see `references/bru-lang-blocks.md`.

---

## Environment Files

Stored in `bruno/environments/<name>.bru`. Never commit secret values.

```bru
vars {
  baseUrl: http://localhost:3000
}

vars:secret {
  authToken:
  apiKey:
}
```

Use `{{variableName}}` syntax anywhere in request files to reference these values.

---

## Common `.bru` Patterns

### Auth token chaining (login → use token)

**auth/login.bru**
```bru
meta { name: Login  type: http  seq: 1 }
post { url: {{baseUrl}}/auth/login  auth: none }
body:json { { "username": "{{username}}", "password": "{{password}}" } }
script:post-response {
  const token = res.getBody().token;
  bru.setEnvVar("authToken", token, true);  // true = persist to disk
}
```

All subsequent requests use `auth: bearer` + `token: {{authToken}}`.

### Chaining IDs between requests

```bru
vars:post-response {
  createdId: res.body.id
}
```

Next request references `{{createdId}}` in its URL or body.

### Declarative assertions

```bru
assert {
  res.status: eq 200
  res.body.name: isString
  res.body.items: isArray
  res.body.count: gte 1
  res.body.email: contains @
  res.responseTime: lt 2000
}
```

---

## Integration with project-docs-generator

Both skills read the same source files and produce complementary outputs. Run them together after adding new routes:

```bash
# 1. Update API docs (project-docs-generator skill)
/update-docs

# 2. Sync Bruno collection (this skill)
python bruno/scripts/generate_bruno.py

# 3. Validate
cd bruno && bru run --env local --tests-only
```

---

## Reference Files

- `references/bru-lang-blocks.md` — Complete block syntax: all auth modes, body types, dynamic variables, assertions
- `references/scanner-patterns.md` — All patterns the scanner uses, known limitations, and troubleshooting
- `scripts/generate_bruno.py` — The route scanner and `.bru` file generator
