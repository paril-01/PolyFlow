# Implementer Agent — Self-Review Checklist

## Purpose

Every implementation must be self-reviewed before submission. This checklist ensures you catch common issues before the Reviewer Agent sees your code.

---

## Checklist

### Design Conformance
- [ ] Implementation matches the validated design document
- [ ] All functional requirements from the spec are implemented
- [ ] Non-functional requirements are addressed
- [ ] No features or behaviors were added beyond the design scope
- [ ] Any deviations from the design are documented with justification

### Code Quality
- [ ] Functions are small and focused (single responsibility)
- [ ] Naming is descriptive and consistent
- [ ] No code duplication (DRY)
- [ ] No unnecessary complexity (KISS)
- [ ] No unnecessary features (YAGNI)
- [ ] No magic numbers or strings — constants are used
- [ ] No commented-out code
- [ ] Dependencies are injected, not hardcoded

### Error Handling
- [ ] All error cases are handled explicitly
- [ ] No empty catch/except blocks
- [ ] Error messages are descriptive and include context
- [ ] Errors are logged with appropriate severity
- [ ] Recoverable vs. unrecoverable errors are distinguished
- [ ] API error responses follow a consistent format
- [ ] Sensitive information is not exposed in error messages

### Security
- [ ] Inputs are validated and sanitized at system boundaries
- [ ] SQL uses parameterized queries (no string concatenation)
- [ ] Authentication is enforced on protected endpoints
- [ ] Authorization checks are present and correct
- [ ] No secrets are hardcoded
- [ ] No sensitive data is logged
- [ ] CORS, CSRF, and other security headers are configured

### Performance
- [ ] Database queries are efficient (no N+1, indexes used)
- [ ] Pagination is implemented for list endpoints
- [ ] No unnecessary computations in hot paths
- [ ] Resources are properly cleaned up (connections, file handles)
- [ ] Timeouts are set for external calls
- [ ] No memory leaks or unbounded data structures

### Testing
- [ ] Unit tests cover critical business logic
- [ ] Integration tests verify external interactions
- [ ] Edge cases are tested
- [ ] Error paths are tested
- [ ] All tests pass
- [ ] Tests are independent and deterministic
- [ ] Test names describe the scenario being tested

### Documentation
- [ ] Public APIs have docstrings
- [ ] Non-obvious logic has inline comments (explaining WHY)
- [ ] README or relevant docs are updated
- [ ] API documentation is complete and accurate
- [ ] Configuration options are documented

### Logging & Observability
- [ ] Structured logging is implemented
- [ ] Log levels are used correctly (DEBUG, INFO, WARN, ERROR)
- [ ] Request IDs / correlation IDs are included in logs
- [ ] Key business events are logged at INFO level
- [ ] Errors are logged at ERROR level with stack traces
- [ ] No sensitive data in logs

### Production Readiness
- [ ] Configuration is externalized (not hardcoded)
- [ ] Database migrations have rollback scripts
- [ ] Health check endpoint exists
- [ ] Graceful shutdown is implemented
- [ ] Resource limits are configured (connection pools, thread pools)

---

## How to Use

1. Complete every item in the checklist
2. For any item that doesn't apply, mark it as N/A with a brief reason
3. For any item that fails, fix it before submitting
4. Include the completed checklist in your submission to the Reviewer Agent
