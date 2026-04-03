---
name: bruno-cli
description: >
  Use this skill whenever the user wants to create, update, or run Bruno API collections
  using the Bruno CLI (`bru`). Triggers include: any mention of "Bruno", ".bru files",
  "bru run", "Bruno collection", "Bruno environment", "Bruno requests", or "API testing
  with Bruno". Also triggers when the user wants to scan an Express or NestJS codebase
  and auto-generate Bruno request files, sync Bruno with existing routes, run /update-bruno,
  or integrate Bruno CLI into CI/CD pipelines. Use this skill any time Bruno is mentioned
  or whenever you would create, edit, or run .bru files — even if the user doesn't say
  "Bruno CLI" explicitly.
---

# Bruno CLI Skill

Bruno is an open-source, Git-native API client that stores collections as plain-text `.bru`
files. This skill covers two modes of use:

1. **Manual** — writing `.bru` files and running `bru` CLI commands by hand
2. **Auto-sync** — scanning an Express or NestJS project and generating/updating Bruno files automatically via `/update-bruno`

The Bruno collection lives inside the project under a folder called `bruno/` (typically a git submodule).

---

## `/update-bruno` — Auto-Sync Routes to Bruno

This is the primary workflow for keeping Bruno in sync with Express and NestJS projects.

### What it does

1. Detects whether the project uses Express, NestJS, or both
2. Scans all controller/router files for route definitions
3. Generates or updates `.bru` files inside the `bruno/` submodule
4. **Preserves** user-written scripts, tests, and assertions on existing files
5. Creates `bruno.json` and environment files if missing

### How to run it

```bash
# From the project root (auto-detects framework)
python bruno/scripts/generate_bruno.py

# Specify framework explicitly
python bruno/scripts/generate_bruno.py --framework nestjs
python bruno/scripts/generate_bruno.py --framework express
python bruno/scripts/generate_bruno.py --framework both

# Preview changes without writing (dry run)
python bruno/scripts/generate_bruno.py --dry-run

# Custom options
python bruno/scripts/generate_bruno.py \
  --project-path /path/to/project \
  --base-url http://localhost:4000 \
  --envs local,staging,production \
  --collection-name "Users API"
```

### What gets created vs preserved

| Block | Behavior |
|-------|---------|
| `meta` (name, seq) | ✏ Updated from code |
| Method block (url, auth) | ✏ Updated from code |
| `params:path` | ✏ Updated from code |
| `headers` (base headers) | ✏ Updated from code |
| `auth:bearer/basic/apikey` | ✏ Updated from code |
| `params:query` | 🔒 Preserved if user has customized |
| `body:json` | 🔒 Preserved if user has customized |
| `assert` | 🔒 Preserved if user has added assertions |
| `script:pre-request` | 🔒 Always preserved |
| `script:post-response` | 🔒 Always preserved |
| `tests` | 🔒 Preserved if user has added tests |

### What Claude does when asked to run /update-bruno

1. Check if `bruno/scripts/generate_bruno.py` exists in the project. If not, tell the user to install the skill.
2. Detect framework from `package.json`
3. Run the script (or describe exactly what command to run if no bash access)
4. Report what was created/updated/unchanged
5. Suggest running `bru run --env local` to validate

---

## Project Structure (with Bruno submodule)

```
your-project/
├── src/
│   ├── users/
│   │   └── users.controller.ts      <- NestJS
│   └── routes/
│       └── users.routes.ts          <- Express
├── package.json
└── bruno/                           <- git submodule
    ├── bruno.json
    ├── scripts/
    │   └── generate_bruno.py        <- the scanner (this skill)
    ├── environments/
    │   ├── local.bru
    │   ├── staging.bru
    │   └── production.bru
    └── users/
        ├── get-users.bru
        ├── create-user.bru
        └── get-user-by-id.bru
```

---

## What the Scanner Detects

### NestJS

Reads from `*.controller.ts` files and any file containing `@Controller(`:

| Source | What's extracted |
|--------|-----------------|
| `@Controller('users')` | Route prefix `/users` |
| `@Get(':id')` | `GET /users/:id` |
| `@Post()` | `POST /users` |
| `@UseGuards(JwtAuthGuard)` | `auth: bearer` |
| `@UseGuards(BasicAuthGuard)` | `auth: basic` |
| `@Public()` | `auth: none` (overrides class guard) |
| `@Body()` | Generates `body:json` block |
| `@Param('id')` | Adds `params:path` block |
| `@Query('page')` | Adds `params:query` entry |

### Express

Reads from any file with `router.METHOD(` or `app.METHOD(` patterns:

| Source | What's extracted |
|--------|-----------------|
| `router.get('/users', ...)` | `GET /users` |
| `app.use('/api', router)` | Resolves prefix to `/api/users` |
| `authenticate` middleware | `auth: bearer` |
| `verifyToken` middleware | `auth: bearer` |
| Filename `users.routes.ts` | Folder prefix `/users` (fallback) |

For the full list of patterns, see `references/scanner-patterns.md`.

---

## Manual `.bru` File Syntax

For the full block reference, see `references/bru-lang-blocks.md`.

### Quick example — GET with auth

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

### Quick example — POST with body

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

Stored in `bruno/environments/<name>.bru`:

```bru
vars {
  baseUrl: http://localhost:3000
}

vars:secret {
  authToken:
  apiKey:
}
```

Reference variables in requests with `{{variableName}}`.

Pass secrets at runtime — never commit them:
```bash
bru run --env local --env-var authToken=mytoken
```

---

## `bru` CLI Reference

```bash
# Run everything
bru run --env local

# Run a single file
bru run users/get-users.bru --env local

# Run a folder
bru run users/ --env staging

# Bail on first failure (good for CI)
bru run --env production --bail

# Run only requests with tests
bru run --tests-only

# Pass secrets inline
bru run --env staging --env-var authToken=$TOKEN --env-var apiKey=$KEY

# Generate reports
bru run --env ci \
  --reporter-json results.json \
  --reporter-junit results.xml \
  --reporter-html results.html

# Run by tag
bru run --tags smoke
bru run --exclude-tags slow

# Import from OpenAPI spec
bru import openapi --source openapi.yml --output ./bruno --collection-name "My API"
```

---

## `bru` Scripting API

Available in `script:pre-request` and `script:post-response` blocks:

```javascript
// Variables
bru.getEnvVar("baseUrl")
bru.setEnvVar("authToken", value, true)  // true = persist to disk
bru.getVar("tempId")
bru.setVar("tempId", "abc")

// Request object (pre-request only)
req.setUrl("https://new-url.com")
req.setHeader("X-Custom", "value")
req.disable()                            // skip this request

// Response object (post-response only)
res.getStatus()                          // 200
res.getBody()                            // parsed JSON
res.getHeader("Content-Type")
res.getResponseTime()                    // ms
```

---

## Auth Token Chaining Pattern

**auth/login.bru**
```bru
meta { name: Login  type: http  seq: 1 }
post { url: {{baseUrl}}/auth/login  auth: none }
body:json { { "username": "{{username}}", "password": "{{password}}" } }
script:post-response {
  const token = res.getBody().token;
  bru.setEnvVar("authToken", token, true);
}
```

All subsequent requests use `auth: bearer` with `token: {{authToken}}`.

---

## CI/CD Integration

```bash
# Sync Bruno from code, then run
python bruno/scripts/generate_bruno.py --framework nestjs
cd bruno && bru run --env ci --env-var authToken=$TOKEN --bail

# GitHub Actions full example
- run: npm install -g @usebruno/cli
- run: python bruno/scripts/generate_bruno.py
- run: |
    cd bruno && bru run \
      --env ci \
      --env-var authToken=${{ secrets.API_TOKEN }} \
      --reporter-junit results.xml \
      --bail
```

---

## Integration with project-docs-generator

The `project-docs-generator` skill generates `API.md` documenting your routes.
The `bruno-cli` skill generates `.bru` files from those same routes.
They are complementary — run them together after adding new routes:

```bash
# Best: use the combined workflow (scans routes only once)
/update-all

# Or run individually
/update-docs
/update-bruno
```

### Auto-Creating the `/update-all` Workflow

When setting up Bruno for a project or running `/update-bruno`, **always do these steps**:

1. **Create `.agent/workflows/update-bruno.md`** if it doesn't exist:

```markdown
---
description: Sync Bruno API collection with the latest route definitions from the codebase.
---

# Update Bruno Collection

This workflow utilizes the `bruno-cli` skill to scan the repository's controllers and route files, then generate or update `.bru` request files in the `bruno/` directory.

## Steps

1. **Trigger Bruno Sync**
   Execute the `bruno-cli` skill on the current repository.

   // turbo
   `@[/bruno-cli] Scan all controllers and route files in this repository and sync the Bruno collection. Preserve existing user-written scripts, tests, and assertions.`
```

2. **Check for cross-skill integration**: After creating `update-bruno.md`, check if `.agent/workflows/update-docs.md` already exists (created by the `project-docs-generator` skill). If it does and `.agent/workflows/update-all.md` does **not** exist, create the combined workflow:

```markdown
---
description: Scan routes once, then update both project documentation and Bruno API collection in a single pass to avoid duplicate token consumption.
---

# Update All — Docs + Bruno

This workflow combines `/update-docs` and `/update-bruno` into a single pass. Instead of scanning controllers and route files twice, the agent reads them once and produces both outputs from the same research.

## Steps

1. **Shared Research Phase**
   Scan all NestJS controllers (`*.controller.ts`) and Express route files (`*.routes.ts`). For each route, extract: HTTP method, path, auth type (guards/middleware), path params, query params, body shape, and any decorators. Also read `package.json` for framework detection. Hold all route data in memory for the next two steps.

2. **Update Documentation**
   // turbo
   `@[.agent/skills/project-docs-generator] Using the route and project data already gathered in this conversation, refresh the documentation for this repository. Do NOT re-scan controller or route files — use what was already collected in step 1.`

3. **Update Bruno Collection**
   // turbo
   `@[/bruno-cli] Using the route data already gathered in this conversation, sync the Bruno collection. Do NOT re-scan controller or route files — use what was already collected in step 1. Preserve existing user-written scripts, tests, and assertions in .bru files.`

4. **Validate Bruno (if applicable)**
   If the Bruno collection exists and `bru` CLI is installed, run:
   `cd bruno && bru run --env local --tests-only`
```

If `.agent/workflows/update-docs.md` does **not** exist, skip the `/update-all` creation — it only makes sense when both skills are present.

---

## Reference Files

- `references/bru-lang-blocks.md` — Full block syntax: all auth modes, body types, dynamic vars
- `references/scanner-patterns.md` — All patterns the scanner uses for NestJS and Express
- `scripts/generate_bruno.py` — The scanner/generator script
