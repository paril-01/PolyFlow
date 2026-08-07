# Reviewer Agent — Severity Matrix

## Purpose

This matrix provides consistent, objective criteria for classifying the severity of review findings. Every finding must be assigned a severity level using this matrix.

---

## Severity Levels

| Level | Name | Description | Response Time | Examples |
|-------|------|-------------|---------------|----------|
| **P0** | Critical | Immediate risk of data loss, security breach, or system failure | Must fix immediately | SQL injection, unencrypted passwords, data corruption bug |
| **P1** | High | Significant bug, security weakness, or missing critical functionality | Must fix before merge/release | Missing auth check, race condition, missing error handling for critical path |
| **P2** | Medium | Code quality issue, missing tests, or documentation gap that impacts maintainability | Should fix before merge | Missing unit tests for business logic, unclear naming, code duplication |
| **P3** | Low | Minor style issue, suggestion for improvement | Fix at author's discretion | Variable naming preference, minor refactoring opportunity |
| **P4** | Informational | Knowledge sharing, alternative approach, future consideration | No action required | "FYI, there's a library that does this", "Consider this pattern for v2" |

---

## Classification Criteria

### Security Impact

| Finding | Severity |
|---------|----------|
| Remote code execution vulnerability | P0 |
| SQL injection | P0 |
| Authentication bypass | P0 |
| Hardcoded credentials | P0 |
| Missing authorization check | P1 |
| XSS vulnerability | P1 |
| Sensitive data in logs | P1 |
| Missing rate limiting on auth endpoints | P1 |
| CORS misconfiguration | P2 |
| Missing security headers | P2 |

### Correctness Impact

| Finding | Severity |
|---------|----------|
| Data corruption / data loss bug | P0 |
| Core business logic error | P1 |
| Off-by-one error in critical path | P1 |
| Edge case not handled (causes crash) | P1 |
| Edge case not handled (graceful failure) | P2 |
| Incorrect error message | P3 |

### Reliability Impact

| Finding | Severity |
|---------|----------|
| No error handling (crash on failure) | P1 |
| Missing timeout on external call | P1 |
| No retry logic for transient failures | P2 |
| Missing health check | P2 |
| Missing graceful shutdown | P3 |

### Performance Impact

| Finding | Severity |
|---------|----------|
| O(n²) algorithm where O(n) is possible on large data | P1 |
| N+1 query problem | P1 |
| Memory leak | P1 |
| Missing database index on frequently queried column | P2 |
| Unnecessary computation | P3 |

### Maintainability Impact

| Finding | Severity |
|---------|----------|
| Incomprehensible code with no documentation | P2 |
| Significant code duplication | P2 |
| Missing tests for critical business logic | P2 |
| Inconsistent naming conventions | P3 |
| Minor code style issue | P4 |

---

## Escalation Rules

- **Any P0 finding** → Review verdict must be REQUEST CHANGES or REJECT
- **Multiple P1 findings** → Review verdict must be REQUEST CHANGES
- **Single P1 finding with clear fix** → May use CONDITIONAL APPROVAL
- **Only P2 and below** → APPROVE or CONDITIONAL APPROVAL acceptable

---

## Disputes

If the author disagrees with a severity classification:

1. The author must provide **evidence** for why the severity should be different
2. The reviewer evaluates the evidence objectively
3. If agreement isn't reached, escalate to the [Governance](../../constitution/governance.md) process
4. The dispute and resolution are recorded by the Historian Agent
