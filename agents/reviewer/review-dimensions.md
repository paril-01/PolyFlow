# Reviewer Agent — Review Dimensions

Detailed breakdown of all 12 review dimensions with specific checklist items for each.

---

## 1. Correctness

Does the implementation produce the right result?

### Checklist
- [ ] Implementation matches the requirements specification
- [ ] Business rules are correctly implemented
- [ ] Edge cases are handled (null, empty, max values, negative numbers)
- [ ] Off-by-one errors are absent
- [ ] Type conversions are correct
- [ ] Mathematical operations are accurate (overflow, precision)
- [ ] Date/time handling is correct (timezones, leap years, DST)
- [ ] String handling is correct (encoding, unicode, escaping)
- [ ] Return values are correct for all code paths
- [ ] Error conditions return appropriate results

---

## 2. Security

Is the implementation safe from exploitation?

### Checklist
- [ ] Inputs are validated and sanitized
- [ ] SQL queries use parameterized statements
- [ ] XSS protection is in place (output encoding)
- [ ] CSRF protection is implemented
- [ ] Authentication is properly enforced
- [ ] Authorization checks exist at every access point
- [ ] Secrets are not hardcoded
- [ ] Sensitive data is not logged
- [ ] Data is encrypted at rest and in transit
- [ ] CORS is properly configured
- [ ] Rate limiting is implemented
- [ ] File uploads are validated (type, size, content)
- [ ] Dependencies have no known vulnerabilities

---

## 3. Performance

Does it meet performance requirements?

### Checklist
- [ ] Database queries are optimized (no N+1, proper indexes)
- [ ] Caching is used where appropriate
- [ ] No unnecessary computations in hot paths
- [ ] Memory allocation is efficient (no unbounded growth)
- [ ] I/O operations are minimized and batched where possible
- [ ] Large data sets use pagination or streaming
- [ ] No blocking operations on event loop (if async)
- [ ] Response times meet requirements
- [ ] Resource cleanup is proper (connections, file handles)

---

## 4. Scalability

Will it work at scale?

### Checklist
- [ ] No single points of failure
- [ ] State management supports horizontal scaling
- [ ] Database design supports sharding/partitioning if needed
- [ ] No global locks or bottlenecks
- [ ] Connection pooling is configured correctly
- [ ] Background jobs are designed for parallel execution
- [ ] File storage is external (not local filesystem)
- [ ] Session management is stateless or externalized

---

## 5. Reliability

Does it work consistently?

### Checklist
- [ ] Timeouts are configured for all external calls
- [ ] Retry logic has exponential backoff and jitter
- [ ] Circuit breakers protect against cascade failures
- [ ] Health checks are implemented
- [ ] Graceful degradation is implemented for non-critical features
- [ ] Graceful shutdown handles in-flight requests
- [ ] Database transactions have appropriate isolation levels
- [ ] Idempotency is implemented where needed

---

## 6. Concurrency

Are concurrent operations safe?

### Checklist
- [ ] Shared mutable state is properly synchronized
- [ ] No race conditions in critical sections
- [ ] Deadlock potential is assessed and mitigated
- [ ] Optimistic locking is used where appropriate
- [ ] Thread pool sizes are configured correctly
- [ ] Async operations don't have hidden synchronous bottlenecks
- [ ] Database transactions handle concurrent access correctly

---

## 7. Maintainability

Can future engineers understand and modify this?

### Checklist
- [ ] Code follows consistent naming conventions
- [ ] Functions/methods have a single responsibility
- [ ] Dependencies are injected, not hardcoded
- [ ] Configuration is externalized
- [ ] Code duplication is minimized
- [ ] Complex logic has explanatory comments
- [ ] Magic numbers/strings are replaced with named constants
- [ ] Error messages are descriptive
- [ ] Code is modular and loosely coupled
- [ ] Complexity is proportional to the problem (not over-engineered)

---

## 8. Cost

What are the resource implications?

### Checklist
- [ ] Compute resources are proportional to the workload
- [ ] Storage costs are manageable at projected data volumes
- [ ] Network costs (egress) are considered
- [ ] Third-party API costs are understood
- [ ] Cost-optimization opportunities are identified
- [ ] Auto-scaling is configured (if applicable)

---

## 9. Testing

Is it adequately tested?

### Checklist
- [ ] Unit tests cover critical business logic
- [ ] Integration tests verify external interactions
- [ ] Edge cases have dedicated tests
- [ ] Error paths are tested
- [ ] Tests are independent and deterministic
- [ ] Test data is realistic
- [ ] Test assertions are specific (not just "no error")
- [ ] Negative tests exist (what should fail?)
- [ ] Performance tests exist for critical paths
- [ ] Tests run in CI/CD pipeline

---

## 10. Observability

Can you see what's happening in production?

### Checklist
- [ ] Structured logging is implemented
- [ ] Log levels are used appropriately (DEBUG, INFO, WARN, ERROR)
- [ ] Request IDs enable distributed tracing
- [ ] Key metrics are instrumented (latency, error rate, throughput)
- [ ] Alerts are configured for critical conditions
- [ ] Dashboards exist for operational monitoring
- [ ] Error logging includes sufficient context for debugging

---

## 11. Compliance

Does it meet regulatory requirements?

### Checklist
- [ ] PII handling complies with applicable regulations
- [ ] Data retention policies are implemented
- [ ] Audit trails are maintained for sensitive operations
- [ ] Access controls meet compliance requirements
- [ ] Data residency requirements are met
- [ ] Right to deletion (GDPR) is supported

---

## 12. Documentation

Is it documented for future engineers?

### Checklist
- [ ] Architecture decisions are documented (ADRs)
- [ ] API contracts are documented with examples
- [ ] Configuration options are documented
- [ ] Deployment procedures are documented
- [ ] Operational runbooks exist
- [ ] Known issues and limitations are documented
- [ ] Code comments explain "why" for non-obvious logic
