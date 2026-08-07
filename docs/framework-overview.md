# 📐 Framework Overview

The **AI Engineering Framework (AEF)** is designed to address the core challenges of AI-assisted software development:
unstructured code generation, missing architectural rationale, lack of test rigor, security oversight, and loss of historical context.

---

## Architecture of AEF

AEF operates on four primary layers:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CONSTITUTIONAL LAYER                                     │
│    Engineering Ethics, Priorities, Safety Rules, Governance │
├─────────────────────────────────────────────────────────────┤
│ 2. AGENT OPERATING LAYER                                    │
│    Maker, Reviewer, Implementer, Gatekeeper, Historian      │
├─────────────────────────────────────────────────────────────┤
│ 3. PROCESS & GOVERNANCE LAYER                               │
│    Playbooks, Checklists, Protocols, Standards              │
├─────────────────────────────────────────────────────────────┤
│ 4. KNOWLEDGE & MEMORY LAYER                                 │
│    Knowledge Graph, Traceability Matrix, Decision Logs      │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Constitutional Layer

Every agent in AEF inherits an immutable **Engineering Constitution**. Key principles include:

1. **Correctness over Speed**: Fast code that fails edge cases is negative productivity.
2. **Evidence over Assumptions**: Every architectural choice must be justified.
3. **Adversarial Review**: Code is assumed imperfect until rigorously reviewed across 12 dimensions.
4. **Minimal Safe Changes**: Avoid scope creep; keep code changes atomic and focused.

---

## 2. Agent Operating Layer

AEF decomposes the Software Development Life Cycle (SDLC) into 5 specialized roles:

- **🔍 Maker Agent**: Discovers functional and non-functional requirements, performs trade-off analyses, and generates ADRs. *Never writes production implementation code.*
- **🔬 Reviewer Agent**: Evaluates designs, code diffs, and security parameters across 12 key dimensions. *Operates with an adversarial mindset.*
- **⚙️ Implementer Agent**: Produces production-grade, tested, and documented code adhering to SOLID/DRY/KISS/YAGNI principles.
- **🚪 Gatekeeper Agent**: Acts as release authority. Verifies requirements, architecture compliance, test coverage, and rollback readiness before production deployment.
- **📚 Historian Agent**: Maintains engineering memory, tracks technical debt, updates the knowledge graph, and logs institutional decision context.

---

## 3. Process & Governance Layer

To ensure repeatability, AEF provides structured assets:

- **Playbooks**: Step-by-step procedure guides for complex scenarios (e.g., performance tuning, incident response, schema migrations).
- **Checklists**: Operational verification steps prior to coding, review, and deployment.
- **Protocols**: Formal agreements governing inter-agent handoffs and reviews.
- **Standards**: Language-agnostic coding, security, testing, and observability standards.

---

## 4. Knowledge & Memory Layer

- **Traceability Matrix**: Maps Requirements → Architecture → ADR → Code → Tests → Deployment.
- **Decision Logs & Debt Register**: Ensures technical debt is tracked explicitly and resolved strategically.
- **Knowledge Graph**: Tracks dependencies, component boundaries, and ownership across the project lifecycle.
