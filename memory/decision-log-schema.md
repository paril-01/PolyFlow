# Decision Log Schema

```yaml
entries:
  - id: DL-001
    date: 2026-08-07
    type: architecture  # architecture | technology | process | design
    title: "Selected FastAPI for REST API framework"
    context: "Need a Python REST API framework for team task management"
    decision: "Use FastAPI"
    alternatives:
      - name: "Django REST Framework"
        reason_rejected: "Heavier than needed for MVP"
      - name: "Flask"
        reason_rejected: "No built-in validation, less type safety"
    rationale: "Best developer experience, auto-generated docs, strong type safety"
    consequences:
      positive: ["Fast development", "Auto OpenAPI docs"]
      negative: ["Smaller ecosystem than Django"]
    related_adrs: ["ADR-001"]
    status: active  # active | superseded | deprecated
```
