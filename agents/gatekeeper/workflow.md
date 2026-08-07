# Gatekeeper Agent — Workflow

## Workflow Diagram

```mermaid
graph TD
    A[Receive Implementation Package] --> B[Step 1: Requirements Verification]
    B --> C[Step 2: Architecture Compliance]
    C --> D[Step 3: Code Review Verification]
    D --> E[Step 4: Testing Verification]
    E --> F[Step 5: Documentation Verification]
    F --> G[Step 6: Production Readiness]
    G --> H{All Gates Pass?}
    H -->|Yes| I[APPROVE]
    H -->|Minor gaps| J[CONDITIONAL APPROVAL]
    H -->|Significant gaps| K[REJECT]
    I --> L[Record Decision via Historian]
    J --> L
    K --> L
```

## Input Required

The Gatekeeper expects to receive:
1. Original requirements specification
2. Validated design documents and ADRs
3. Implementation code and changes
4. Reviewer Agent's review report
5. Test results and coverage report
6. Deployment documentation

## Gate Criteria

Each gate is evaluated as PASS or FAIL. Any FAIL in critical gates results in rejection.

| Gate | Critical? | PASS Criteria |
|------|-----------|---------------|
| Requirements | Yes | All requirements verified as implemented |
| Architecture | Yes | Implementation matches approved design |
| Code Review | Yes | Reviewer approved with no blocking findings |
| Testing | Yes | All tests pass, adequate coverage |
| Documentation | No | Docs exist and are reasonably complete |
| Production Readiness | Yes | Health checks, monitoring, rollback ready |
