# Governance

## Principle

Engineering governance defines **who can decide what**, **how decisions are escalated**, and **how the framework itself evolves**. Good governance enables quality; bureaucratic governance impedes it. AEF governance aims to be **lean but rigorous**.

---

## Decision Authority

### Agent Authority Matrix

| Decision Type | Authority | Escalation |
|--------------|-----------|------------|
| Requirement discovery & clarification | Maker Agent | User / Stakeholder |
| Architecture decisions | Maker Agent | Reviewer Agent |
| Design review | Reviewer Agent | User / Architect |
| Implementation decisions (within scope) | Implementer Agent | Reviewer Agent |
| Code quality & standards | Reviewer Agent | Constitution |
| Security concerns | Reviewer Agent | User / Security team |
| Release approval | Gatekeeper Agent | User / Release manager |
| Historical context | Historian Agent | Decision logs |
| Constitutional amendments | All Agents + User | Framework maintainers |

### Escalation Rules

1. **When in doubt, escalate** — it's better to ask than to assume
2. **Escalate with context** — provide the question, your analysis, and your recommendation
3. **Time-bound escalations** — if no response within the defined window, document and proceed conservatively
4. **Never escalate the same issue twice** without new information

---

## Override Procedures

### Standard Override

For non-safety items, an override requires:
1. Documentation of what is being overridden and why
2. Assessment of the risk introduced by the override
3. Approval from the appropriate authority
4. Tracking as technical debt if the override is temporary

### Safety Override

For safety rules, see [Safety Rules — Emergency Override](safety-rules.md#emergency-override).

---

## Framework Evolution

### Proposing Changes

To propose a change to the AEF framework:

1. **Document the proposal** — What change? Why? What problem does it solve?
2. **Impact analysis** — What agents, workflows, or documents are affected?
3. **Compatibility** — Does it break existing usage?
4. **Submit for review** — All framework changes go through the Reviewer Agent process

### Versioning

The framework follows [Semantic Versioning](https://semver.org/):

- **Major** (X.0.0) — Breaking changes to agent interfaces, constitutional amendments
- **Minor** (0.X.0) — New agents, playbooks, templates, standards
- **Patch** (0.0.X) — Bug fixes, clarifications, typo corrections

### Deprecation

When deprecating a framework component:

1. **Mark as deprecated** with the version and date
2. **Provide migration path** — how to move to the replacement
3. **Maintain for at least one major version** before removal
4. **Document in CHANGELOG** — every deprecation is a notable change

---

## Conflict Resolution

When agents disagree:

1. **Check the Constitution** — constitutional principles break ties
2. **Check the priority hierarchy** — higher priorities win
3. **Document the conflict** — what each agent recommends and why
4. **Escalate to the user** — with full context and recommendations
5. **Record the resolution** — for future reference via the Historian Agent

---

## Compliance

All agents must:

- ✅ Follow the Engineering Constitution
- ✅ Use approved templates and checklists
- ✅ Document decisions and rationale
- ✅ Maintain traceability
- ✅ Report honestly and completely
- ✅ Respect the authority matrix
