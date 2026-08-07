# Reviewer Agent — Example Review

## Scenario

Reviewing the Maker Agent's design for a task management REST API (from the [Maker example](../../maker/examples/sample-discovery.md)).

---

## Review Summary

Reviewed the design artifacts for a team-based task management REST API. The design is solid for an MVP but has several important gaps in security, reliability, and testing that should be addressed before implementation.

**Overall Assessment**: The design is well-structured with clear requirements and a sensible architecture choice. However, there are critical gaps in authentication security, error handling strategy, and missing non-functional specifications that need attention.

---

## Critical Findings (P0-P1)

### Finding 1: JWT Token Revocation Not Addressed

- **Severity**: P1
- **Dimension**: Security
- **Location**: Non-functional requirements, security section
- **Description**: The design specifies JWT with refresh tokens but doesn't address token revocation. If a user's account is compromised or they leave a team, there's no way to invalidate active tokens.
- **Impact**: Compromised accounts could retain access until token expiration.
- **Recommendation**: Implement a token blacklist (Redis-backed) or use short-lived access tokens (5 min) with refresh token rotation. Document the chosen approach in an ADR.

### Finding 2: No Input Validation Strategy

- **Severity**: P1
- **Dimension**: Security
- **Location**: Functional requirements — missing
- **Description**: The design doesn't specify input validation rules. Task titles, descriptions, and other user inputs need validation for length, format, and sanitization.
- **Impact**: Potential for XSS, injection attacks, or resource exhaustion via oversized inputs.
- **Recommendation**: Define maximum lengths for all text fields. Specify sanitization rules. Add input validation as a cross-cutting requirement.

### Finding 3: No Error Handling Strategy

- **Severity**: P1
- **Dimension**: Reliability
- **Location**: Design-wide — missing
- **Description**: The design doesn't define an error handling strategy. What error codes does the API return? How are errors formatted? What happens when the database is unavailable?
- **Impact**: Inconsistent error responses, poor debugging experience, potential information leakage in error messages.
- **Recommendation**: Define a standard error response format, error code taxonomy, and behavior for each failure mode (database down, auth service down, etc.).

---

## Important Findings (P2)

### Finding 4: Soft Delete Complexity

- **Severity**: P2
- **Dimension**: Maintainability
- **Description**: Soft delete adds complexity to every query (must filter deleted records). Consider whether this complexity is justified for an MVP.
- **Recommendation**: If soft delete is required, create a database view or query scope that automatically filters deleted records. Document the pattern for implementers.

### Finding 5: Missing Pagination Specification

- **Severity**: P2
- **Dimension**: Performance
- **Description**: Task listing endpoint doesn't specify pagination strategy. Without pagination, listing tasks for active teams could return unbounded results.
- **Recommendation**: Specify cursor-based or offset-based pagination with a default page size (e.g., 50) and maximum page size (e.g., 200).

### Finding 6: No Rate Limiting Specification

- **Severity**: P2
- **Dimension**: Security / Reliability
- **Description**: No rate limiting is specified for API endpoints, particularly authentication endpoints.
- **Recommendation**: Define rate limits for auth endpoints (e.g., 5 failed logins per minute) and general API endpoints (e.g., 100 requests per minute per user).

---

## Minor Findings (P3-P4)

### Finding 7: Missing API Versioning Strategy

- **Severity**: P3
- **Dimension**: Maintainability
- **Description**: No API versioning strategy is defined. This will become important when the API evolves.
- **Recommendation**: Use URL-based versioning (e.g., `/api/v1/`) from day one.

### Finding 8: Consider OpenAPI Specification

- **Severity**: P4
- **Dimension**: Documentation
- **Description**: Since FastAPI auto-generates OpenAPI specs, this should be mentioned as a deliverable.
- **Recommendation**: Include the OpenAPI specification as a required artifact of implementation.

---

## Positive Observations

- ✅ Clear problem statement and scope definition
- ✅ Well-structured requirements with acceptance criteria
- ✅ Good ADR format with alternatives considered
- ✅ Assumptions are explicitly documented
- ✅ Reasonable technology choice (FastAPI) with solid rationale
- ✅ Scope is appropriately limited for an MVP

---

## Verdict

**CONDITIONAL APPROVAL**

**Conditions**:
1. Address Finding 1 (JWT revocation) — add an ADR for the chosen approach
2. Address Finding 2 (input validation) — add validation requirements
3. Address Finding 3 (error handling) — define error response format and failure modes

Once these three items are addressed, the design is ready for the Implementer Agent.
