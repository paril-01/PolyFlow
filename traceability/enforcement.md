# Traceability Enforcement

## How Traceability is Enforced

### During Design (Maker Agent)
- Every requirement gets an ID
- Every ADR references the requirements it addresses
- Design documents reference requirements

### During Implementation (Implementer Agent)
- Code references requirement IDs in commit messages or comments
- Tests reference the requirement they verify

### During Review (Reviewer Agent)
- Verify that implementations trace to requirements
- Verify that tests trace to implementations
- Flag any code without requirement traceability

### During Gate Review (Gatekeeper Agent)
- Verify the traceability matrix is complete
- Every requirement has implementation and tests
- No orphaned code (code without requirements)

### During Recording (Historian Agent)
- Archive the traceability matrix with each release
- Track requirement changes over time
