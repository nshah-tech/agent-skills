# Bru Lang — Complete Block Reference

## `meta` block

Required in every `.bru` file.

```bru
meta {
  name: My Request Name    # Display name in UI and reports
  type: http               # http or graphql
  seq: 1                   # Execution order within folder (integer)
}
```

---

## HTTP Method blocks

One of these is required per file:

```bru
get    { url: {{baseUrl}}/path  auth: none }
post   { url: {{baseUrl}}/path  auth: bearer }
put    { url: {{baseUrl}}/path  auth: bearer }
patch  { url: {{baseUrl}}/path  auth: bearer }
delete { url: {{baseUrl}}/path  auth: bearer }
```

**auth values:** `none`, `bearer`, `basic`, `apikey`, `oauth2`, `digest`, `wsse`

---

## `params:query` — Query String Parameters

```bru
params:query {
  page: 1
  limit: 20
  filter: active
  ~disabledParam: ignored   # ~ prefix disables the param
}
```

---

## `params:path` — Path Parameters

For URLs like `/users/:id`:

```bru
params:path {
  id: {{userId}}
}
```

---

## `headers` block

```bru
headers {
  Content-Type: application/json
  Accept: application/json
  X-Api-Version: 2
  ~X-Disabled-Header: not sent   # ~ disables it
}
```

---

## Body blocks (only one per request)

### `body:json`

```bru
body:json {
  {
    "name": "{{name}}",
    "email": "{{email}}",
    "tags": ["admin", "beta"]
  }
}
```

### `body:text`

```bru
body:text {
  Plain text content here
}
```

### `body:xml`

```bru
body:xml {
  <?xml version="1.0"?>
  <user>
    <name>{{name}}</name>
  </user>
}
```

### `body:form-urlencoded`

```bru
body:form-urlencoded {
  grant_type: client_credentials
  client_id: {{clientId}}
  client_secret: {{clientSecret}}
}
```

### `body:multipartForm`

```bru
body:multipartForm {
  username: johndoe
  avatar: @/path/to/image.png    # @ prefix = file upload
  description: Profile picture
}
```

### `body:graphql`

```bru
body:graphql {
  query {
    users {
      id
      name
      email
    }
  }
}

body:graphql:vars {
  {
    "limit": 10
  }
}
```

---

## Auth blocks

Only include the block matching the `auth:` value in the method block.

### `auth:bearer`

```bru
auth:bearer {
  token: {{authToken}}
}
```

### `auth:basic`

```bru
auth:basic {
  username: {{username}}
  password: {{password}}
}
```

### `auth:apikey`

```bru
auth:apikey {
  key: X-API-Key
  value: {{apiKey}}
  placement: header    # header or queryparams
}
```

### `auth:oauth2`

```bru
auth:oauth2 {
  grant_type: client_credentials
  client_id: {{clientId}}
  client_secret: {{clientSecret}}
  token_url: {{baseUrl}}/oauth/token
  scope: read write
}
```

---

## Variable blocks

### `vars:pre-request` — Set variables before the request

Values are JavaScript expressions evaluated before the request:

```bru
vars:pre-request {
  timestamp: Date.now()
  requestId: Math.random().toString(36).slice(2)
}
```

### `vars:post-response` — Extract from response

Values are JavaScript expressions with access to `res`:

```bru
vars:post-response {
  userId: res.body.id
  token: res.body.auth.token
  status: res.status
}
```

---

## `assert` block — Declarative Assertions

No JavaScript needed. Evaluated after the response.

```bru
assert {
  # Status
  res.status: eq 200
  res.status: in [200, 201]

  # Body field checks
  res.body.id: isDefined
  res.body.name: isString
  res.body.count: isNumber
  res.body.active: isBool
  res.body.items: isArray
  res.body.meta: isJson

  # Comparisons
  res.body.count: gt 0
  res.body.count: gte 1
  res.body.score: lt 100
  res.body.score: lte 99

  # String matchers
  res.body.email: contains @example.com
  res.body.url: startsWith https
  res.body.status: endsWith ing

  # Null / undefined
  res.body.error: isNull
  res.body.data: isNotNull
  res.body.optional: isUndefined

  # Performance
  res.responseTime: lt 2000

  # Disable an assertion with ~
  ~res.body.debug: isDefined
}
```

**Full operator list:**
`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `notIn`, `contains`, `notContains`, `startsWith`, `endsWith`, `matches` (regex), `isDefined`, `isUndefined`, `isNull`, `isNotNull`, `isArray`, `isString`, `isNumber`, `isBool`, `isJson`, `isEmpty`, `isNotEmpty`, `length`, `minLength`, `maxLength`

---

## `script:pre-request` block

Runs JavaScript before the HTTP request is sent.

```bru
script:pre-request {
  // Read environment variables
  const env = bru.getEnvVar("environment");

  // Dynamically set a header value
  const signature = generateHmac(bru.getEnvVar("secret"), req.url);
  req.setHeader("X-Signature", signature);

  // Conditionally disable the request
  if (!bru.getVar("shouldRun")) {
    req.disable();
  }
}
```

---

## `script:post-response` block

Runs JavaScript after the HTTP response is received.

```bru
script:post-response {
  const body = res.getBody();
  const status = res.getStatus();

  // Save to env var (persists to .bru file)
  if (status === 200 && body.token) {
    bru.setEnvVar("authToken", body.token, true);
  }

  // Save runtime var (in-memory, this run only)
  bru.setVar("lastUserId", body.id);

  // Log for debugging
  console.log("Response time:", res.getResponseTime(), "ms");
}
```

---

## `tests` block

JavaScript tests using Chai `expect` syntax.

```bru
tests {
  test("status is 200", function () {
    expect(res.getStatus()).to.equal(200);
  });

  test("body has required fields", function () {
    const body = res.getBody();
    expect(body).to.have.property("id");
    expect(body).to.have.property("email");
    expect(body.email).to.include("@");
  });

  test("response time under 2s", function () {
    expect(res.getResponseTime()).to.be.below(2000);
  });

  test("save token", function () {
    const token = res.getBody().token;
    expect(token).to.not.be.empty;
    bru.setEnvVar("authToken", token, true);
  });
}
```

---

## Environment File Syntax

Stored in `environments/<name>.bru`:

```bru
vars {
  baseUrl: https://api.staging.example.com
  timeout: 5000
  userId: user_abc123
}

vars:secret {
  authToken:
  apiKey:
  dbPassword:
}
```

Secret vars are blank in the file — pass via CLI:
```bash
bru run --env staging --env-var authToken=mytoken --env-var apiKey=mykey
```

---

## `folder.bru` — Folder-level config

Optional file placed inside any collection subfolder. Allows folder-wide pre/post scripts and variables:

```bru
meta {
  name: Users Folder
}

vars {
  resourceType: users
}

script:pre-request {
  console.log("Running request in users folder");
}
```

---

## Built-in Dynamic Variables

Available via `{{$variableName}}` syntax in request files:

| Variable | Description |
|----------|-------------|
| `{{$uuid}}` | Random UUID v4 |
| `{{$timestamp}}` | Unix timestamp (seconds) |
| `{{$randomInt}}` | Random integer |
| `{{$isoTimestamp}}` | ISO 8601 datetime string |

Example:
```bru
headers {
  X-Request-ID: {{$uuid}}
  X-Timestamp: {{$timestamp}}
}
```

---

## Tags

Add tags to requests for selective execution:

```bru
meta {
  name: Create User
  type: http
  seq: 1
  tags: [smoke, auth, users]
}
```

CLI usage:
```bash
bru run --tags smoke          # Only run tagged smoke
bru run --exclude-tags slow   # Skip slow-tagged requests
```
