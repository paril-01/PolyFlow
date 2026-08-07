# Maker Agent — ADR Template

## Architecture Decision Record

Use this template to document every significant architecture, technology, or design decision.

---

```markdown
# ADR-[NUMBER]: [TITLE]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Date
[YYYY-MM-DD]

## Context

[Describe the situation that requires a decision. What is the problem or opportunity?
Include relevant background, constraints, and forces at play.]

## Decision Drivers

- [Driver 1: e.g., "Must support 10,000 concurrent users"]
- [Driver 2: e.g., "Team has experience with Python"]
- [Driver 3: e.g., "Must comply with GDPR"]

## Considered Options

### Option 1: [Name]
**Description**: [Brief description of this option]

**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Risk**: [Low/Medium/High]

---

### Option 2: [Name]
**Description**: [Brief description of this option]

**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Risk**: [Low/Medium/High]

---

### Option 3: [Name]
**Description**: [Brief description of this option]

**Pros**:
- [Advantage 1]
- [Advantage 2]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]

**Risk**: [Low/Medium/High]

## Decision

[State the decision clearly. Which option was selected?]

## Rationale

[Explain WHY this option was selected over the alternatives.
Reference the decision drivers and how this option best addresses them.
Be specific about the trade-offs accepted.]

## Consequences

### Positive
- [Positive consequence 1]
- [Positive consequence 2]

### Negative
- [Negative consequence / trade-off 1]
- [Negative consequence / trade-off 2]

### Risks
- [Residual risk 1 — and its mitigation]
- [Residual risk 2 — and its mitigation]

## Follow-up Actions

- [ ] [Action 1]
- [ ] [Action 2]
- [ ] [Action 3]

## References

- [Link or reference 1]
- [Link or reference 2]
```

---

## ADR Guidelines

1. **One decision per ADR** — don't bundle multiple decisions
2. **Be specific** — vague ADRs are useless
3. **Always document alternatives** — show your work
4. **Record the rationale** — the "why" is more valuable than the "what"
5. **ADRs are immutable once accepted** — don't edit old ADRs; supersede them with new ones
6. **Number sequentially** — ADR-001, ADR-002, etc.
7. **Link related ADRs** — decisions often depend on earlier decisions
