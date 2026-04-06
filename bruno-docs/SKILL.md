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
