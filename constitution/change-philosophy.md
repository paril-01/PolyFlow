# Change Philosophy

## Principle

Every change to a system carries risk. The Change Philosophy governs how engineers approach modifications to ensure they are **safe, minimal, well-understood, and reversible**.

---

## Core Tenets

### 1. Understand Before Modifying

Before changing any code:
- **Read the existing code** — understand what it does and why
- **Read the tests** — understand what behavior is verified
- **Read the documentation** — understand the design intent
- **Read the history** — understand how it evolved (git blame, ADRs, decision logs)

Changing code you don't understand is engineering malpractice.

### 2. Minimal Safe Changes

- Change **only what is necessary** to achieve the objective
- Do not refactor unrelated code in the same change
- Do not "improve" code that isn't part of the task
- Every additional line changed is additional risk

The ideal change is the **smallest change** that correctly solves the problem.

### 3. One Change, One Purpose

- Each change should have a **single, clear purpose**
- Do not mix feature development with refactoring
- Do not mix bug fixes with performance improvements
- Do not mix configuration changes with code changes

This makes changes easier to review, test, understand, and revert.

### 4. Reversibility

Every change should be **reversible**:
- Code changes can be reverted via version control
- Database migrations must have rollback scripts
- Configuration changes must be restorable
- Feature flags should control risky changes

If a change cannot be easily reversed, it requires additional review and planning.

### 5. Never Cargo Cult

- Do not copy patterns without understanding them
- Do not apply "best practices" without verifying they fit the context
- Do not use design patterns because they're popular — use them because they solve a specific problem
- Every technique must earn its place through demonstrated value

---

## Change Process

```
1. Understand the current state
2. Define the desired state
3. Identify the minimal change needed
4. Assess the risk of the change
5. Plan the change (with rollback strategy)
6. Implement the change
7. Self-review the change
8. Submit for review
9. Verify the change
10. Document the change
```

---

## Risk Assessment

Before every change, assess:

| Factor | Question |
|--------|----------|
| **Scope** | How much code is affected? |
| **Blast radius** | What could break if this goes wrong? |
| **Reversibility** | Can this be easily undone? |
| **Dependencies** | What depends on the changed code? |
| **Data impact** | Does this affect stored data? |
| **User impact** | Does this affect user-facing behavior? |
| **Performance impact** | Does this affect system performance? |
| **Security impact** | Does this affect the security posture? |

---

## Anti-Patterns

- 🚫 **"While I'm in here..."** — Don't mix unrelated changes
- 🚫 **"Let me just refactor this real quick"** — Refactoring is a separate, planned activity
- 🚫 **"I know what this does"** — Verify. Don't assume.
- 🚫 **"It worked before, so my change is fine"** — Verify the change didn't break something subtle
- 🚫 **"We'll roll back if something goes wrong"** — Plan for rollback before you need it
- 🚫 **"Copy this pattern from StackOverflow"** — Understand it first, adapt it to your context
