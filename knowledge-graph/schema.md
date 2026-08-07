# Knowledge Graph Schema

## Node Types

| Node Type | Description | Example |
|-----------|-------------|---------|
| **Module** | A code module or component | `auth-service`, `task-api` |
| **Requirement** | A functional or non-functional requirement | FR-01, NFR-03 |
| **Decision** | An architecture or design decision | ADR-001 |
| **Person** | A team member | @engineer-a |
| **Technology** | A technology or framework | FastAPI, PostgreSQL |
| **Risk** | An identified risk | R-01 |
| **Debt** | A technical debt item | TD-01 |

## Edge Types

| Edge | From | To | Meaning |
|------|------|-----|---------|
| `depends_on` | Module | Module | Runtime dependency |
| `implements` | Module | Requirement | Module fulfills requirement |
| `decided_by` | Module | Decision | Architecture choice |
| `owned_by` | Module | Person | Primary ownership |
| `uses` | Module | Technology | Technology dependency |
| `has_risk` | Module | Risk | Associated risk |
| `has_debt` | Module | Debt | Associated technical debt |
| `supersedes` | Decision | Decision | ADR supersession |
| `related_to` | any | any | General relationship |

## Example Graph

```mermaid
graph TD
    TaskAPI[Task API Module] -->|depends_on| AuthModule[Auth Module]
    TaskAPI -->|depends_on| Database[(PostgreSQL)]
    TaskAPI -->|implements| FR01[FR-01: Create Task]
    TaskAPI -->|implements| FR02[FR-02: List Tasks]
    TaskAPI -->|decided_by| ADR001[ADR-001: Use FastAPI]
    TaskAPI -->|owned_by| EngineerA[@engineer-a]
    TaskAPI -->|has_debt| TD01[TD-01: Missing rate limiting]
    AuthModule -->|decided_by| ADR002[ADR-002: JWT with Redis]
    ADR001 -->|related_to| ADR002
```
