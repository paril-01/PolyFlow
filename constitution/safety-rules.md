# Safety Rules

## Principle

Safety rules are **absolute constraints** that no agent, process, or business requirement can override. They exist to prevent catastrophic failures, data loss, security breaches, and irreversible damage.

---

## Non-Negotiable Safety Rules

### 1. Data Safety

- ❌ **Never delete production data** without a verified backup and rollback plan
- ❌ **Never run destructive operations** (DROP, TRUNCATE, DELETE without WHERE) in production without explicit confirmation
- ❌ **Never modify database schemas** without a tested migration and rollback script
- ✅ **Always back up** before destructive operations
- ✅ **Always use transactions** for multi-step data modifications
- ✅ **Always verify backups** can be restored before relying on them

### 2. Authentication & Authorization Safety

- ❌ **Never bypass authentication** for convenience
- ❌ **Never hardcode credentials** in source code, configuration files, or logs
- ❌ **Never log sensitive data** (passwords, tokens, PII, credit card numbers)
- ❌ **Never disable security features** in production (CORS, CSRF, CSP, rate limiting)
- ✅ **Always use the principle of least privilege**
- ✅ **Always validate and sanitize input** — trust nothing from external sources
- ✅ **Always use parameterized queries** — never construct SQL from user input

### 3. Deployment Safety

- ❌ **Never deploy directly to production** without staging verification
- ❌ **Never deploy without a rollback strategy**
- ❌ **Never deploy on Fridays** (or before extended breaks) without exceptional justification
- ✅ **Always use feature flags** for risky changes
- ✅ **Always use canary deployments** or blue-green for high-risk releases
- ✅ **Always monitor** after deployment for anomalies

### 4. Error Handling Safety

- ❌ **Never swallow exceptions** silently (empty catch blocks)
- ❌ **Never expose internal error details** to end users (stack traces, SQL errors)
- ❌ **Never ignore error return values**
- ✅ **Always handle errors explicitly** — decide what to do with each error case
- ✅ **Always log errors** with sufficient context for debugging
- ✅ **Always fail safely** — prefer a clear error over corrupted state

### 5. Concurrency Safety

- ❌ **Never share mutable state** across threads without synchronization
- ❌ **Never assume operations are atomic** unless explicitly guaranteed
- ❌ **Never use sleep/delay as a synchronization mechanism**
- ✅ **Always use proper locking** or lock-free data structures
- ✅ **Always consider race conditions** in multi-threaded or distributed systems
- ✅ **Always test concurrent scenarios**

### 6. Dependency Safety

- ❌ **Never use dependencies with known vulnerabilities** without documented risk acceptance
- ❌ **Never auto-update dependencies** in production without testing
- ❌ **Never use unmaintained dependencies** for critical functionality
- ✅ **Always pin dependency versions** in production
- ✅ **Always audit dependencies** regularly for vulnerabilities
- ✅ **Always have a plan** for replacing deprecated dependencies

---

## Defensive Programming Principles

1. **Validate all inputs** — from users, APIs, databases, files, and configuration
2. **Check all return values** — including error codes and null returns
3. **Set resource limits** — timeouts, memory limits, file size limits, rate limits
4. **Use type safety** — leverage the type system to prevent errors at compile time
5. **Fail fast** — detect and report errors as early as possible
6. **Fail safely** — ensure failures don't leave the system in a corrupted state
7. **Log defensively** — provide enough context to debug any production issue
8. **Test defensively** — test edge cases, boundary conditions, and error paths

---

## Emergency Override

Safety rules may only be overridden when:

1. There is an **active production incident** causing user harm
2. The override is **documented** with justification
3. The override is **time-bounded** with a plan to restore safety
4. The override is **approved** by a senior engineer or the Gatekeeper Agent
5. The override is **tracked** as technical debt for follow-up
