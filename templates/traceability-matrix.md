# Traceability Matrix Template

```markdown
# Requirements Traceability Matrix — [Project Name]

| Req ID | Requirement | Design Doc | ADR | Implementation | Test Case | Deployment | Status |
|--------|------------|------------|-----|---------------|-----------|------------|--------|
| FR-01 | [Brief description] | [Section ref] | ADR-001 | [File/class] | UT-01, IT-01 | v1.0.0 | Verified |
| FR-02 | [Brief description] | [Section ref] | — | [File/class] | UT-02 | v1.0.0 | Verified |
| NFR-01 | [Brief description] | [Section ref] | ADR-002 | [Config/code] | PT-01 | v1.0.0 | Verified |
```

## Purpose

The traceability matrix ensures that:
1. Every requirement has a corresponding design
2. Every design has a corresponding implementation
3. Every implementation has corresponding tests
4. Every test has been verified
5. Nothing exists without justification

## How to Maintain

1. Create the matrix during design (Maker Agent)
2. Update during implementation (Implementer Agent)
3. Verify during gate review (Gatekeeper Agent)
4. Archive versions with releases (Historian Agent)
