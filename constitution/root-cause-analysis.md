# Root Cause Analysis

## Principle

When a bug, failure, or unexpected behavior occurs, the engineering response must be to **find and fix the root cause**, not apply a superficial patch to the symptom. Symptom fixes create technical debt and mask deeper systemic issues.

---

## Root Cause Analysis Methodology

### Step 1: Define the Problem Clearly

Before investigating, clearly state:
- **What** happened (observed behavior)
- **What** was expected (expected behavior)
- **When** it happened (timeline, triggers)
- **Where** it happened (component, environment)
- **How often** it happens (frequency, reproducibility)

A vague problem definition leads to a vague investigation.

### Step 2: Gather Evidence

Collect all available evidence:
- **Logs** — application, system, and access logs
- **Metrics** — performance, error rates, resource usage
- **Traces** — distributed tracing, request flows
- **Code history** — recent changes, deployments
- **User reports** — affected users, reproduction steps
- **Configuration** — recent config changes, environment differences

### Step 3: The 5 Whys

Ask "Why?" repeatedly to drill past symptoms to the root cause:

```
Problem: API returns 500 errors intermittently

Why? → The database query times out
Why? → The query scans the full table instead of using an index
Why? → The column used in the WHERE clause is not indexed
Why? → The schema migration that added the index was not applied in production
Why? → The deployment pipeline skips migration verification

Root Cause: Missing migration verification step in the deployment pipeline
Fix: Add migration verification to the deployment checklist and pipeline
```

### Step 4: Fishbone Analysis (Ishikawa)

For complex problems, categorize potential causes:

```
                          ┌─── Code Logic
                          ├─── Data Issues
Problem ───┤
                          ├─── Configuration
                          ├─── Infrastructure
                          ├─── External Dependencies
                          └─── Human Error
```

### Step 5: Verify the Root Cause

Before implementing a fix:
- **Reproduce** the problem reliably
- **Confirm** the root cause by demonstrating that the proposed fix resolves the problem
- **Eliminate** alternative hypotheses

---

## Fix Classification

| Type | Description | Example | Acceptable? |
|------|-------------|---------|-------------|
| **Root Cause Fix** | Addresses the underlying cause | Add missing index | ✅ Preferred |
| **Systemic Fix** | Prevents the category of issue | Add migration verification | ✅ Best |
| **Workaround** | Mitigates the symptom temporarily | Increase timeout | ⚠️ Temporary only |
| **Symptom Fix** | Hides the symptom | Retry on error | ❌ Unacceptable alone |

---

## Blameless Postmortems

When things go wrong:

1. **Focus on systems, not people** — "What allowed this to happen?" not "Who did this?"
2. **Document the timeline** — exact sequence of events
3. **Identify contributing factors** — multiple causes, not just one
4. **Define action items** — specific, actionable, assigned, time-bound
5. **Share learnings** — everyone benefits from understanding failures

---

## Anti-Patterns

- 🚫 **"Just add a try-catch"** — Swallowing exceptions hides bugs
- 🚫 **"Just increase the timeout"** — Longer timeouts mask performance problems
- 🚫 **"Just restart the service"** — Restarts hide resource leaks and state corruption
- 🚫 **"It only happens rarely"** — Rare bugs in production affect real users
- 🚫 **"We fixed the symptom, so it's done"** — The root cause will manifest elsewhere
