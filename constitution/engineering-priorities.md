# Engineering Priorities

## Principle

When priorities conflict, this hierarchy determines the order of importance. Higher priorities always take precedence over lower ones. This hierarchy is **non-negotiable**.

---

## Priority Hierarchy

```
┌─────────────────────────────────────┐
│ 1. CORRECTNESS                      │  ← Highest Priority
│    Does it produce the right result? │
├─────────────────────────────────────┤
│ 2. SECURITY                         │
│    Is it safe from exploitation?     │
├─────────────────────────────────────┤
│ 3. RELIABILITY                      │
│    Does it work consistently?        │
├─────────────────────────────────────┤
│ 4. DATA INTEGRITY                   │
│    Is data preserved and accurate?   │
├─────────────────────────────────────┤
│ 5. PERFORMANCE                      │
│    Does it meet performance needs?   │
├─────────────────────────────────────┤
│ 6. MAINTAINABILITY                  │
│    Can it be understood and changed? │
├─────────────────────────────────────┤
│ 7. OBSERVABILITY                    │
│    Can we see what's happening?      │
├─────────────────────────────────────┤
│ 8. SCALABILITY                      │
│    Can it grow with demand?          │
├─────────────────────────────────────┤
│ 9. USABILITY                        │
│    Is it easy to use correctly?      │
├─────────────────────────────────────┤
│ 10. VELOCITY                        │  ← Lowest Priority
│     How fast can we deliver?         │
└─────────────────────────────────────┘
```

---

## How to Apply This Hierarchy

### Rule 1: Never Sacrifice a Higher Priority for a Lower One

- ❌ **Never** sacrifice correctness for velocity
- ❌ **Never** sacrifice security for performance
- ❌ **Never** sacrifice reliability for features
- ❌ **Never** sacrifice data integrity for speed

### Rule 2: Document Trade-offs When Same-Level Priorities Conflict

When two priorities at the same level conflict (rare but possible), document:
- What the conflict is
- What alternatives were considered
- What decision was made and why
- What risks the decision introduces

### Rule 3: "Fast but Wrong" is Never Acceptable

A fast implementation that produces incorrect results is worse than no implementation. Speed is the **lowest** engineering priority, not the highest.

---

## Common Conflicts and Resolution

| Conflict | Resolution |
|----------|------------|
| Performance vs. Correctness | Correctness wins. Optimize later. |
| Velocity vs. Security | Security wins. Ship securely. |
| Features vs. Reliability | Reliability wins. Reduce scope. |
| Performance vs. Maintainability | Maintainability wins, unless benchmarks prove a problem. |
| Velocity vs. Observability | Observability wins. You can't debug what you can't see. |

---

## Anti-Patterns

- 🚫 **"We'll fix it later"** — Deferring correctness or security is creating hidden risk
- 🚫 **"It works on my machine"** — Reliability requires verified behavior across environments
- 🚫 **"We don't have time for tests"** — Tests are correctness verification, not optional extras
- 🚫 **"Logging is overhead"** — Observability is how you find problems in production
- 🚫 **"Just ship it"** — Velocity is important but never at the cost of higher priorities
