# Code Review Checklist

- [ ] Code matches the design specification
- [ ] Logic is correct (no off-by-one, no race conditions)
- [ ] Error handling is comprehensive (no swallowed errors)
- [ ] Inputs are validated at system boundaries
- [ ] Security: no hardcoded secrets, no SQL injection, auth enforced
- [ ] Performance: no N+1 queries, no unbounded loops, resources cleaned up
- [ ] Tests exist and are meaningful (not just asserting true)
- [ ] Naming is clear and consistent
- [ ] No code duplication
- [ ] No commented-out code
- [ ] Logging is adequate for production debugging
- [ ] Documentation is updated
- [ ] No unnecessary changes (minimal diff)
