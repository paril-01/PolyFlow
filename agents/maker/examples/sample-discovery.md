# Maker Agent — Example Discovery Session

## Scenario

A user requests: *"Build me a REST API for a task management application."*

---

## Phase 1: Problem Understanding

### Maker Agent Response

> Thank you for the request. Before I begin designing, I need to understand the problem deeply. Let me ask some questions:
>
> **Business Context:**
> 1. What is the primary purpose of this task management app? (Personal use, team collaboration, enterprise project management?)
> 2. Who are the target users? (Individual developers, small teams, enterprise organizations?)
> 3. Is this a new system or replacing an existing one?
> 4. What's the expected timeline for the first usable version?
>
> **Functional Scope:**
> 5. What does a "task" look like? (Title, description, due date, priority, assignee, labels, subtasks, attachments?)
> 6. Do you need user authentication and authorization?
> 7. Do you need team/organization support?
> 8. Do you need real-time updates (WebSocket) or is polling acceptable?
> 9. Do you need search and filtering capabilities?
> 10. Do you need audit logging (who changed what, when)?
>
> **Technical Constraints:**
> 11. Any preferred programming language or framework?
> 12. Any preferred database?
> 13. Cloud provider preference?
> 14. Expected number of users? (10? 100? 10,000? 1,000,000?)

### User Response

> It's for small team collaboration, about 5-20 users per team. New system. We use Python. PostgreSQL is fine. No cloud preference. Need basic auth, task CRUD, assignment, and due dates. MVP in 2 weeks.

---

## Phase 2: Requirements Specification

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|------------|-------------------|
| FR-01 | User registration and authentication | Users can register, login, and logout. JWT-based auth. |
| FR-02 | Team management | Create teams, invite members, remove members |
| FR-03 | Task creation | Title (required), description, due date, priority (low/medium/high/critical), assignee |
| FR-04 | Task listing | List tasks with filtering by status, assignee, priority, due date |
| FR-05 | Task update | Update any task field. Track who modified and when. |
| FR-06 | Task deletion | Soft delete with option to restore |
| FR-07 | Task status workflow | Open → In Progress → Done (with option to reopen) |
| FR-08 | Task assignment | Assign/unassign team members to tasks |
| FR-09 | Due date tracking | Filter overdue tasks. Optional due date reminders. |
| FR-10 | Basic search | Search tasks by title and description |

### Non-Functional Requirements

| Category | Requirement | Target |
|----------|------------|--------|
| Performance | API response time | < 200ms p95 |
| Scalability | Concurrent users per team | 20 |
| Scalability | Total teams | 100 (initial) |
| Availability | Uptime | 99.5% |
| Security | Authentication | JWT with refresh tokens |
| Security | Data at rest | PostgreSQL encryption |
| Data | Backup frequency | Daily |

### Assumptions

| ID | Assumption |
|----|-----------|
| A-01 | Team sizes will remain small (5-20 members) for the foreseeable future |
| A-02 | Real-time updates are not required for MVP |
| A-03 | File attachments are not required for MVP |
| A-04 | Email notifications are not required for MVP |

---

## Phase 3: Architecture Decision

### ADR-001: API Framework Selection

**Status**: Accepted

**Context**: We need a Python REST API framework for a small-to-medium team task management application.

**Considered Options**:
1. **FastAPI** — Modern, async, auto-generated OpenAPI docs, type hints
2. **Django REST Framework** — Mature, batteries-included, large community
3. **Flask + Flask-RESTful** — Lightweight, flexible, well-known

**Decision**: FastAPI

**Rationale**: FastAPI provides the best developer experience with automatic OpenAPI documentation, native async support for future scalability, and strong type safety through Pydantic. The team can ship the MVP faster with auto-generated docs and validation.

---

## Phase 4: Handoff to Reviewer

### Summary for Reviewer Agent

This design covers a REST API for team-based task management. Key areas to review:

1. **Security**: JWT implementation for small teams — is this sufficient?
2. **Data model**: Soft delete approach — any concerns?
3. **Scalability**: The design assumes small teams; will it hold if growth exceeds assumptions?
4. **Missing requirements**: Are there obvious requirements the user didn't mention that we should flag?

**Risks**:
- Scope creep during MVP development (2-week timeline is tight)
- No real-time updates may frustrate users expecting live collaboration
