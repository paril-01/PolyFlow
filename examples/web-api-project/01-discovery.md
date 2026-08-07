# Web API Project — Discovery Phase

## User Request
"Build a REST API for team task management."

## Maker Agent Output

### Problem Statement
Build a RESTful API that enables small teams (5-20 members) to collaboratively manage tasks including creation, assignment, status tracking, and due date management.

### Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|------------|----------|-------------------|
| FR-01 | User registration & auth | Must | JWT-based authentication |
| FR-02 | Team management | Must | Create, invite, remove members |
| FR-03 | Task CRUD | Must | Create, read, update, soft-delete tasks |
| FR-04 | Task assignment | Must | Assign team members to tasks |
| FR-05 | Task status workflow | Must | Open → In Progress → Done |
| FR-06 | Filtering & search | Should | Filter by status, priority, assignee |
| FR-07 | Due date tracking | Should | Overdue task highlighting |

### Non-Functional Requirements

| Category | Target |
|----------|--------|
| Response time | < 200ms p95 |
| Availability | 99.5% |
| Concurrent users | 20 per team, 100 teams |
| Security | JWT, bcrypt passwords, HTTPS |
