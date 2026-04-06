---
name: bruno-cli
description: >
  Use this skill whenever the user wants to run Bruno API collections using the bru CLI,
  write pre/post-request scripts, add assertions or tests to .bru requests, configure
  environments via the command line, generate reports (JSON, JUnit, HTML), integrate
  Bruno into CI/CD pipelines (GitHub Actions, Jenkins), use the bru scripting API (bru.setEnvVar,
  res.getBody, req.setHeader, etc.), or troubleshoot bru run failures. This skill is about
  executing and scripting Bruno — not about creating or maintaining the collection files.
  For generating .bru files from Express or NestJS code, use the bruno-docs skill instead.
---

# Bruno CLI Skill

This skill covers everything about **running and scripting** Bruno via the `bru` CLI:
- Running collections, folders, and individual requests
- Writing scripts and tests inside `.bru` files
- Environment and secret management at the CLI level
- Generating reports for CI dashboards
- The full `bru` scripting API

---

## Installation

```bash
npm install -g @usebruno/cli

bru --version
```

---

## Running Collections

```bash
# Run everything from the collection root
bru run

# Single file
bru run users/get-user.bru

# Whole folder
bru run users/

# Recursively through all subfolders
bru run -r

# With an environment
bru run --env staging

# Override one variable
bru run --env staging --env-var apiKey=abc123

# Override multiple variables (pass secrets without committing them)
bru run --env production \
  --env-var authToken=$TOKEN \
  --env-var apiKey=$KEY

# Stop on first failure
bru run --bail

# Only run requests that have tests or assertions
bru run --tests-only

# Add delay between requests (milliseconds)
bru run --delay 500

# Run in parallel
bru run --parallel

# Filter by tag
bru run --tags smoke,auth

# Exclude by tag
bru run --exclude-tags slow,wip
```

---

## Generating Reports

```bash
# JSON report
bru run --reporter-json results.json

# JUnit XML (for CI dashboards like Jenkins, GitHub Actions)
bru run --reporter-junit results.xml

# HTML report (visual, standalone file)
bru run --reporter-html results.html

# All three at once
bru run --env staging \
  --reporter-json results.json \
  --reporter-junit results.xml \
  --reporter-html results.html

# Strip sensitive data from reports
bru run --reporter-skip-body            # omit request + response bodies
bru run --reporter-skip-all-headers     # omit all headers
bru run --reporter-skip-headers X-Auth  # omit specific header
```

---

## SSL & Security Options

```bash
# Allow self-signed certs (dev only)
bru run --insecure

# Custom CA certificate
bru run --cacert custom-ca.pem

# Use custom CA exclusively (ignore system truststore)
bru run --cacert custom-ca.pem --ignore-truststore

# Disable cookies
bru run --disable-cookies

# Disable all proxies
bru run --noproxy
```

---

## Importing from OpenAPI

```bash
# Import a local spec
bru import openapi \
  --source openapi.yml \
  --output ./bruno \
  --collection-name "My API"

# Import from a URL
bru import openapi \
  --source https://api.example.com/openapi.json \
  --output ./bruno \
  --collection-name "Remote API"
```

---

## Scripting API

Scripts run as JavaScript inside `script:pre-request` and `script:post-response` blocks.

### `bru` — Variable management

```javascript
// Environment variables (can be persisted to the .bru env file)
bru.getEnvVar("baseUrl")
bru.setEnvVar("authToken", "new-value")
bru.setEnvVar("authToken", "value", true)  // true = write back to disk

// Runtime variables (in-memory, current run only)
bru.getVar("tempId")
bru.setVar("tempId", "abc123")
bru.deleteVar("tempId")

// Global environment variables
bru.getGlobalEnvVar("workspaceToken")
bru.setGlobalEnvVar("workspaceToken", "value")

// Interpolate variables into a string
bru.interpolate("Hello {{name}}, your token is {{authToken}}")

// Check sandbox mode
bru.isSafeMode()   // true = QuickJS, false = Node VM
```

### `req` — Modify the request (pre-request only)

```javascript
req.url                        // read current URL
req.method                     // read HTTP method
req.headers                    // read headers object
req.body                       // read request body

req.setUrl("https://other.com/path")
req.setHeader("X-Signature", computeHmac(req.body))
req.setBody({ key: "value" })
req.disable()                  // skip this request entirely
```

### `res` — Read the response (post-response only)

```javascript
res.getStatus()                // 200
res.getBody()                  // parsed JSON object (or string)
res.getHeader("Content-Type")  // single header value
res.getHeaders()               // all response headers as object
res.getResponseTime()          // milliseconds
```

---

## Tests Block (Chai)

Tests use [Chai's `expect` API](https://www.chaijs.com/api/bdd/).

```javascript
tests {
  test("status is 201", function () {
    expect(res.getStatus()).to.equal(201);
  });

  test("body has required fields", function () {
    const body = res.getBody();
    expect(body).to.have.property("id");
    expect(body.id).to.be.a("string");
    expect(body.email).to.include("@");
  });

  test("response is fast", function () {
    expect(res.getResponseTime()).to.be.below(2000);
  });

  test("save token for next request", function () {
    const token = res.getBody().token;
    expect(token).to.not.be.empty;
    bru.setEnvVar("authToken", token, true);
  });
}
```

---

## Assertions Block (Declarative, No JS)

```bru
assert {
  res.status: eq 200
  res.status: in [200, 201]
  res.body.id: isDefined
  res.body.name: isString
  res.body.count: isNumber
  res.body.active: isBool
  res.body.items: isArray
  res.body.meta: isJson
  res.body.count: gte 1
  res.body.score: lt 100
  res.body.email: contains @
  res.body.url: startsWith https
  res.body.role: in [admin, user, guest]
  res.body.error: isNull
  res.body.data: isNotNull
  res.responseTime: lt 2000
  ~res.body.debug: isDefined    # ~ disables this assertion
}
```

**Full operator list:** `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `notIn`, `contains`, `notContains`, `startsWith`, `endsWith`, `matches` (regex), `isDefined`, `isUndefined`, `isNull`, `isNotNull`, `isArray`, `isString`, `isNumber`, `isBool`, `isJson`, `isEmpty`, `isNotEmpty`, `length`, `minLength`, `maxLength`

---

## Common Scripting Patterns

### Save auth token after login

```javascript
// script:post-response in your login.bru
const body = res.getBody();
if (res.getStatus() === 200 && body.token) {
  bru.setEnvVar("authToken", body.token, true);
}
```

### Conditionally skip a request

```javascript
// script:pre-request
const token = bru.getEnvVar("authToken");
if (!token) {
  req.disable();
  console.log("Skipped: no auth token available");
}
```

### Add a dynamic signature header

```javascript
// script:pre-request (requires --sandbox=developer for crypto)
const secret = bru.getEnvVar("signingSecret");
const timestamp = Date.now();
req.setHeader("X-Timestamp", String(timestamp));
req.setHeader("X-Signature", `${timestamp}.${secret}`);
```

### Extract and chain an ID

```bru
vars:post-response {
  createdUserId: res.body.id
}
```

Next request uses `{{createdUserId}}` in its URL or body.

---

## CI/CD Integration

### GitHub Actions

```yaml
name: API Tests
on: [push, pull_request]
jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true           # needed if bruno/ is a submodule
      - run: npm install -g @usebruno/cli
      - run: |
          cd bruno && bru run \
            --env ci \
            --env-var authToken=${{ secrets.API_TOKEN }} \
            --reporter-junit results.xml \
            --bail
      - uses: actions/upload-artifact@v3
        with:
          name: bruno-results
          path: bruno/results.xml
```

### Jenkins

```groovy
stage('API Tests') {
  steps {
    sh 'npm install -g @usebruno/cli'
    dir('bruno') {
      sh """
        bru run \
          --env ci \
          --env-var authToken=${API_TOKEN} \
          --reporter-junit results.xml \
          --bail
      """
    }
    junit 'bruno/results.xml'
  }
}
```

### Sync from code then run (with bruno-docs skill)

```bash
# Regenerate .bru files from source, then run
python bruno/scripts/generate_bruno.py --framework nestjs
cd bruno && bru run --env ci --bail
```

---

## Tags

Add tags to requests for selective test runs:

```bru
meta {
  name: Create User
  type: http
  seq: 1
  tags: [smoke, users, auth]
}
```

```bash
bru run --tags smoke          # smoke suite only
bru run --tags smoke,auth     # must have ALL listed tags
bru run --exclude-tags slow   # skip anything tagged slow
```

---

## Data-Driven Testing

Run the same request multiple times with different data from a CSV or JSON file:

```bash
# CSV
bru run create-user.bru --csv-file-path users.csv

# JSON
bru run create-user.bru --json-file-path users.json

# Repeat N times
bru run create-user.bru --iteration-count 5
```
