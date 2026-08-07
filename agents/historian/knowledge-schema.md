# Historian Agent — Knowledge Schema

## Engineering Memory Schema

This schema defines the structure of engineering memory maintained by the Historian Agent.

---

## Entry Types

### Decision Record
```yaml
type: decision
date: YYYY-MM-DD
title: "Brief description of the decision"
context: "What situation required this decision"
decision: "What was decided"
alternatives: 
  - "Alternative 1 and why it was rejected"
  - "Alternative 2 and why it was rejected"
rationale: "Why this option was chosen"
consequences:
  positive: ["List of positive consequences"]
  negative: ["List of negative consequences"]
related_adrs: ["ADR-001", "ADR-003"]
status: "active | superseded | deprecated"
```

### Technical Debt Entry
```yaml
type: technical_debt
date_identified: YYYY-MM-DD
title: "Brief description of the debt"
description: "Detailed explanation"
cause: "Why this debt was introduced"
impact: "low | medium | high | critical"
affected_components: ["component-a", "component-b"]
remediation_plan: "How to fix it"
estimated_effort: "hours/days/weeks"
priority: "low | medium | high | critical"
status: "open | in_progress | resolved | accepted"
```

### Implementation Record
```yaml
type: implementation
date: YYYY-MM-DD
title: "What was implemented"
summary: "Brief description"
files_changed: ["path/to/file1", "path/to/file2"]
requirements_addressed: ["FR-01", "FR-02"]
review_status: "approved | conditional | rejected"
lessons_learned: ["Lesson 1", "Lesson 2"]
```

### Incident Record
```yaml
type: incident
date: YYYY-MM-DD
severity: "low | medium | high | critical"
title: "Brief description of the incident"
timeline: "Chronological sequence of events"
root_cause: "What caused the incident"
resolution: "How it was resolved"
preventive_actions: ["Action 1", "Action 2"]
lessons_learned: ["Lesson 1", "Lesson 2"]
```

---

## Organization

Entries are organized by:
1. **Chronology** — reverse chronological order
2. **Component** — grouped by system component
3. **Type** — decisions, debt, implementations, incidents
4. **Search** — full-text searchable
