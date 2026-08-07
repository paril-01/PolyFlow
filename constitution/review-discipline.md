# Review Discipline

## Principle

Every engineering artifact — design, code, configuration, documentation — is reviewed before it is considered complete. Reviews are **adversarial and independent**, meaning the reviewer's job is to find flaws, not confirm correctness.

---

## Review Philosophy

### Every Implementation is Imperfect

No matter how experienced the engineer, every implementation contains potential issues. Reviews exist to catch what the author cannot see. This is not a criticism of the author — it is a fundamental property of software engineering.

### Reviews are Adversarial

The reviewer's role is to **challenge**, not **defend**. A review that finds no issues is suspicious, not successful. The reviewer should actively try to break the design, find edge cases, identify security holes, and stress-test assumptions.

### Reviews are Independent

The reviewer must be **independent** from the author. This means:
- The reviewer did not write the code
- The reviewer does not share the same assumptions
- The reviewer evaluates against standards, not personal preferences

---

## What Gets Reviewed

| Artifact | Required Review |
|----------|----------------|
| Architecture decisions | Reviewer Agent |
| System design documents | Reviewer Agent |
| Code changes | Reviewer Agent + self-review |
| Configuration changes | Reviewer Agent |
| Database schema changes | Reviewer Agent |
| API contracts | Reviewer Agent |
| Security-sensitive changes | Reviewer Agent + security-specific review |
| Release candidates | Gatekeeper Agent |

---

## Review Dimensions

Every review must consider these dimensions:

1. **Correctness** — Does it do what it claims?
2. **Security** — Is it safe from exploitation?
3. **Performance** — Does it meet performance needs?
4. **Scalability** — Will it work at scale?
5. **Reliability** — Will it work consistently?
6. **Concurrency** — Are there race conditions?
7. **Maintainability** — Can it be understood and changed?
8. **Cost** — What are the resource implications?
9. **Testing** — Is it adequately tested?
10. **Observability** — Can we monitor it in production?
11. **Compliance** — Does it meet regulatory requirements?
12. **Documentation** — Is it documented for future engineers?

---

## Review Severity Levels

| Level | Name | Description | Action Required |
|-------|------|-------------|-----------------|
| **P0** | Critical | Security vulnerability, data loss, system crash | Must fix before merge |
| **P1** | High | Significant bug, performance issue, missing error handling | Must fix before merge |
| **P2** | Medium | Code quality issue, missing tests, documentation gap | Should fix before merge |
| **P3** | Low | Style issue, minor improvement suggestion | Fix at author's discretion |
| **P4** | Informational | Knowledge sharing, alternative approaches | No action required |

---

## Review Anti-Patterns

### For Reviewers
- 🚫 **Rubber-stamping** — Approving without thorough review
- 🚫 **Nitpicking only** — Focusing on style while missing logic bugs
- 🚫 **Scope creep** — Requesting features not in the original requirement
- 🚫 **Ego-driven feedback** — Insisting on personal preferences as standards
- 🚫 **Delayed reviews** — Blocking progress unnecessarily

### For Authors
- 🚫 **Defensive responses** — Treating feedback as personal criticism
- 🚫 **Ignoring feedback** — Dismissing review comments without addressing them
- 🚫 **Massive PRs** — Submitting thousands of lines for review
- 🚫 **Missing context** — Not explaining what changed or why
