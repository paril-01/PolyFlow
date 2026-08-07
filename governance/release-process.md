# Release Process

## Purpose
Define the process for releasing software to production.

## Release Workflow

```mermaid
graph TD
    A[Development Complete] --> B[Code Review]
    B --> C[All Tests Pass]
    C --> D[Gate Review by Gatekeeper]
    D --> E{Approved?}
    E -->|Yes| F[Create Release Branch]
    E -->|No| G[Address Findings]
    G --> B
    F --> H[Deploy to Staging]
    H --> I[Staging Verification]
    I --> J{Staging OK?}
    J -->|Yes| K[Deploy to Production]
    J -->|No| L[Fix & Re-verify]
    L --> H
    K --> M[Post-Deploy Verification]
    M --> N[Update CHANGELOG]
    N --> O[Tag Release]
    O --> P[Record in History]
```

## Release Checklist

- [ ] All tests pass on CI/CD
- [ ] Gatekeeper Agent approved
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Release notes written
- [ ] Staging deployment successful
- [ ] Staging verification complete
- [ ] Rollback plan documented
- [ ] Monitoring dashboards ready
- [ ] On-call team notified

## Rollback Procedure

1. Identify the issue
2. Decide: fix forward or roll back
3. If rolling back: deploy the previous version
4. Verify rollback succeeded
5. Document the incident
6. Investigate root cause
