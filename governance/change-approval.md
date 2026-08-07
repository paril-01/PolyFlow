# Change Approval

## Purpose
Define who can approve what types of changes and the required approval process.

## Approval Matrix

| Change Type | Required Approval | Self-Approve? |
|-------------|------------------|---------------|
| Bug fix (no behavior change) | 1 reviewer | No |
| Feature (within approved design) | 1 reviewer | No |
| API contract change | 2 reviewers | No |
| Database schema change | 2 reviewers + DBA review | No |
| Architecture change | Maker → Reviewer → ADR | No |
| Security-sensitive change | Security-focused review | No |
| Configuration change | 1 reviewer | No |
| Documentation only | Self-approve allowed | Yes |
| Dependency update (patch) | 1 reviewer | No |
| Dependency update (minor/major) | 1 reviewer + testing | No |

## Process

1. Author submits change with description, tests, and impact analysis
2. Reviewer(s) review per the [Review Discipline](../constitution/review-discipline.md)
3. All P0/P1 findings must be resolved
4. Approval is documented
5. Change is merged

## Emergency Changes

For production incidents:
1. Fix can be applied with post-hoc review
2. Must be reviewed within 24 hours
3. Must be documented with incident reference
4. Any shortcuts taken are tracked as technical debt
