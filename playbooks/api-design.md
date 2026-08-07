# Playbook: API Design

## When to Use
Designing a new API or evolving an existing one.

## Process

### Step 1: Define the Contract
1. Identify the API consumers — who will use this?
2. Define resources and operations (REST) or queries/mutations (GraphQL)
3. Define request/response schemas with examples
4. Define error codes and messages
5. Define pagination, filtering, and sorting
6. Define authentication and authorization requirements
7. Define rate limits

### Step 2: Design Principles
- **Consistency** — all endpoints follow the same patterns
- **Predictability** — consumers can guess the endpoint for a new resource
- **Backward compatibility** — existing consumers must not break
- **Versioning** — use URL versioning (e.g., `/api/v1/`)
- **HATEOAS** — include links to related resources (optional but recommended)

### Step 3: Review
- Reviewer Agent reviews the API design
- Check for consistency, security, usability
- Consider consumer experience — is the API easy to use correctly?

### Step 4: Document
- OpenAPI/Swagger specification
- Request/response examples for every endpoint
- Error code reference
- Authentication guide
- Rate limiting documentation

### Step 5: Implement
- Follow the API contract exactly
- Validate inputs against the contract
- Return the documented error codes

## REST API Conventions

| Action | HTTP Method | URL Pattern | Success Code |
|--------|-------------|-------------|-------------|
| List | GET | /resources | 200 |
| Get one | GET | /resources/:id | 200 |
| Create | POST | /resources | 201 |
| Update | PUT/PATCH | /resources/:id | 200 |
| Delete | DELETE | /resources/:id | 204 |

## Anti-Patterns
- 🚫 Verbs in URLs (`/getUsers`) — use HTTP methods
- 🚫 Inconsistent response formats
- 🚫 Missing pagination on list endpoints
- 🚫 Breaking changes without versioning
