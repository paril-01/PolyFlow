# Dependency Management

## Purpose
Govern how external dependencies are selected, added, updated, and removed to minimize risk and maximize reliability.

## Policies

### Adding Dependencies
1. **Justify the need** — can this be done with existing dependencies or standard library?
2. **Evaluate the dependency** — maturity, maintenance, community, license, security
3. **Assess the risk** — what happens if this dependency is abandoned?
4. **Pin the version** — use exact versions in production, not ranges
5. **Document the decision** — why this dependency was chosen over alternatives

### Updating Dependencies
1. **Review changelogs** before updating — understand what changed
2. **Test after updating** — run the full test suite
3. **Update one at a time** — never batch unrelated dependency updates
4. **Security updates** — apply within 48 hours for critical vulnerabilities

### Removing Dependencies
1. **Verify nothing depends on it** — check for transitive dependencies
2. **Remove completely** — don't leave orphaned references
3. **Document the removal** — why it was removed

### Prohibited Practices
- ❌ Never use `*` or `latest` versions in production
- ❌ Never add dependencies without reviewing their license
- ❌ Never add dependencies with known critical vulnerabilities
- ❌ Never add unmaintained dependencies (no updates in 12+ months) for critical paths

### Dependency Review Criteria

| Criterion | Minimum Acceptable |
|-----------|-------------------|
| Last update | Within 12 months |
| Open issues response | Maintainer responds within 30 days |
| License | Compatible with project license |
| Known vulnerabilities | None with severity High or Critical |
| Test coverage | Has a test suite |
