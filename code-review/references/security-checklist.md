# Security Checklist — OWASP Top 10 for Node.js / React

Use this checklist during the Security Pass of any full-diff review.

---

## A01: Broken Access Control

- [ ] Every API endpoint has authentication check
- [ ] Authorization: user can only access their own resources
- [ ] Admin endpoints protected by role check
- [ ] No direct object reference without ownership check (IDOR)
  ```typescript
  // ❌ IDOR — user can query any order by ID
  app.get('/orders/:id', auth, async (req, res) => {
    const order = await Order.findById(req.params.id); // no ownership check!
    res.json(order);
  });
  // ✅ Always filter by authenticated user
  const order = await Order.findOne({ _id: req.params.id, userId: req.user.id });
  ```
- [ ] File access restricted — no path traversal possible
- [ ] JWT/session not exposed to frontend unnecessarily
- [ ] CORS not set to wildcard `*` in production

---

## A02: Cryptographic Failures

- [ ] Passwords hashed with bcrypt (cost ≥ 12) or argon2 — never MD5/SHA1
- [ ] No sensitive data in logs (tokens, passwords, PII)
- [ ] HTTPS enforced in production — HTTP redirected
- [ ] JWT signed with strong secret (≥ 256-bit) or RS256 asymmetric key
- [ ] Sensitive data not in URL params (tokens, session IDs)
- [ ] No sensitive fields in localStorage (use httpOnly cookies)

---

## A03: Injection

- [ ] **SQL** — parameterized queries or ORM, never string concatenation
  ```typescript
  // ❌ SQL injection
  db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);
  // ✅ Parameterized
  db.query('SELECT * FROM users WHERE id = $1', [req.params.id]);
  ```
- [ ] **NoSQL** — Mongoose sanitize plugin or manual validation
  ```typescript
  // ❌ NoSQL injection
  User.find({ email: req.body.email }); // if email = { $gt: "" } → returns all users
  // ✅ Validate type first
  const email = z.string().email().parse(req.body.email);
  User.find({ email });
  ```
- [ ] **Command injection** — never use `exec()`/`spawn()` with user input
- [ ] **XSS** — React escapes by default; flag any `dangerouslySetInnerHTML`

---

## A04: Insecure Design

- [ ] Rate limiting on auth endpoints (brute force protection)
- [ ] Account lockout after N failed attempts
- [ ] Password reset tokens have expiry (< 1 hour)
- [ ] Password reset uses secure random token, not predictable value
- [ ] Email enumeration prevented (same message for existing/non-existing accounts)
- [ ] OTP/2FA codes have expiry and attempt limits

---

## A05: Security Misconfiguration

- [ ] `NODE_ENV=production` set in prod — disables stack traces
- [ ] Debug endpoints disabled in production (`/api/debug`, `/health` with internal info)
- [ ] Default credentials changed
- [ ] Unnecessary features/packages removed
- [ ] Error responses don't leak stack traces or internal paths
- [ ] Helmet.js configured (CSP, HSTS, X-Frame-Options, etc.)

---

## A06: Vulnerable & Outdated Components

- [ ] Run `npm audit` — no high/critical vulnerabilities
- [ ] Dependencies not pinned to exact version without lockfile
- [ ] No packages with known CVEs (check Snyk or GitHub Dependabot)

---

## A07: Identification & Authentication Failures

- [ ] JWT `exp` claim set (short-lived: 15min–1hr for access tokens)
- [ ] Refresh token rotation implemented
- [ ] JWT not stored in localStorage (XSS risk) — prefer httpOnly cookie
- [ ] Session fixation prevented — new session ID on login
- [ ] Logout invalidates session/token server-side
- [ ] Multi-factor authentication for admin accounts

---

## A08: Software & Data Integrity Failures

- [ ] File uploads validated: MIME type (not just extension), size limit
  ```typescript
  const upload = multer({
    limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
    fileFilter: (req, file, cb) => {
      const allowed = ['image/jpeg', 'image/png', 'image/webp'];
      cb(null, allowed.includes(file.mimetype));
    },
  });
  ```
- [ ] Webhook endpoints verify signatures (GitHub, Stripe, etc.)
- [ ] Deserialization of user input is safe — no `eval()`, no unvalidated JSON.parse

---

## A09: Security Logging & Monitoring

- [ ] Auth events logged: login, logout, failed attempts, password reset
- [ ] Access control failures logged with user ID and resource
- [ ] Logs don't include passwords or tokens
- [ ] Log injection prevented (no raw user input in log messages)
  ```typescript
  // ❌ Log injection
  logger.info(`User logged in: ${req.body.username}`);
  // ✅ Structured logging
  logger.info('User logged in', { username: req.body.username });
  ```

---

## A10: Server-Side Request Forgery (SSRF)

- [ ] If app fetches URLs provided by users, validate against allowlist
- [ ] Internal URLs not accessible via user-provided input
- [ ] `axios`/`fetch` calls don't follow redirects to internal IP ranges
  ```typescript
  // ❌ SSRF
  const data = await axios.get(req.body.webhookUrl); // user controls URL!
  // ✅ Validate URL
  const url = new URL(req.body.webhookUrl);
  if (!['https:'].includes(url.protocol)) throw new BadRequestException();
  if (['localhost', '127.0.0.1', '0.0.0.0'].includes(url.hostname)) throw new ForbiddenException();
  ```

---

## Quick Security Verdict

| Finding | Severity | Action |
|---------|----------|--------|
| Hardcoded secret/credential | CRITICAL | Block commit immediately |
| SQL/NoSQL injection | CRITICAL | Block commit |
| Missing auth on endpoint | CRITICAL | Block commit |
| XSS via dangerouslySetInnerHTML | HIGH | Block commit |
| Rate limiting missing on auth | HIGH | Fix before merge |
| JWT stored in localStorage | HIGH | Fix before merge |
| `npm audit` high vulnerability | HIGH | Fix before merge |
| CORS misconfigured | MEDIUM | Fix before merge |
| Missing input validation | MEDIUM | Fix before merge |
| Sensitive data in logs | MEDIUM | Fix before merge |
| Missing error boundary | LOW | Suggestion |
