# Documentation Standards

## Principle

If it's not documented, it doesn't exist. Documentation is a **first-class engineering artifact**, not an afterthought. Every significant engineering decision, design, implementation, and operational procedure must be documented.

---

## What Must Be Documented

### Always Document

| Artifact | Required Documentation |
|----------|----------------------|
| **Architecture decisions** | ADR (Architecture Decision Record) |
| **Requirements** | Requirements specification |
| **Design** | Technical design document |
| **API contracts** | API documentation with examples |
| **Database schema** | Schema documentation with relationships |
| **Configuration** | Configuration reference with defaults and constraints |
| **Deployment** | Deployment guide with prerequisites |
| **Operational procedures** | Runbooks and playbooks |
| **Known issues** | Issue tracker with reproduction steps |
| **Trade-offs** | Decision log with rationale |

### Document Immediately

- **Before implementation**: Requirements, design, ADRs
- **During implementation**: Inline comments for non-obvious logic, API docs
- **After implementation**: Test plans, deployment guides, release notes
- **On change**: Update all affected documentation

---

## Documentation Quality Standards

### Clarity

- Write for the reader, not the author
- Use **plain language** — avoid jargon unless necessary (and define it when used)
- Use **concrete examples** — show, don't just tell
- Use **diagrams** for complex relationships or workflows

### Completeness

- Cover the **what**, **why**, **how**, **when**, and **who**
- Include **prerequisites** and **assumptions**
- Include **edge cases** and **error scenarios**
- Include **limitations** and **known issues**

### Accuracy

- Documentation must match the **current state** of the system
- **Outdated documentation is worse than no documentation** — it misleads
- Update documentation as part of every change, not as a separate task

### Maintainability

- Keep documentation **close to the code** it describes
- Use **templates** for consistency
- Use **cross-references** instead of duplication
- Version documentation alongside code

---

## Documentation Types

### 1. Architecture Decision Records (ADRs)

- **When**: Every significant architecture or technology decision
- **Template**: See [ADR Template](../templates/adr-template.md)
- **Content**: Context, decision, alternatives considered, consequences

### 2. Requirements Specifications

- **When**: Before implementation begins
- **Template**: See [Requirements Template](../templates/requirements-template.md)
- **Content**: Functional requirements, non-functional requirements, constraints, acceptance criteria

### 3. Design Documents

- **When**: For any non-trivial implementation
- **Template**: See [Design Document Template](../templates/design-document.md)
- **Content**: Problem statement, proposed solution, alternatives, trade-offs, risks

### 4. API Documentation

- **When**: For every public API endpoint or interface
- **Content**: Endpoint, method, parameters, request/response examples, error codes, rate limits

### 5. Inline Code Comments

- **When**: For non-obvious logic, workarounds, or performance-critical sections
- **What to comment**: WHY, not WHAT — the code shows what; comments explain why

### 6. Test Documentation

- **When**: For every test suite
- **Content**: What is tested, why, test data requirements, expected behaviors

---

## Anti-Patterns

- 🚫 **"The code is self-documenting"** — Code shows HOW, not WHY or WHEN
- 🚫 **"I'll document it later"** — Later never comes; document as you go
- 🚫 **"Everyone knows this"** — New team members don't; future you won't
- 🚫 **"It's just a prototype"** — Prototypes become production code; document the intent
- 🚫 **"Documentation slows us down"** — Debugging undocumented systems is slower
