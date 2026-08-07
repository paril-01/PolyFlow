# API Standards

## Design Principles
1. **RESTful** — resources as nouns, HTTP methods as verbs
2. **Consistent** — same patterns across all endpoints
3. **Versioned** — URL-based versioning (`/api/v1/`)
4. **Documented** — OpenAPI/Swagger spec for every API
5. **Backward compatible** — breaking changes require version bump

## URL Conventions
- Use kebab-case: `/api/v1/task-assignments`
- Use plurals for collections: `/api/v1/users`
- Use nested resources sparingly: `/api/v1/teams/{id}/members`

## HTTP Methods
| Method | Purpose | Idempotent | Success Code |
|--------|---------|-----------|-------------|
| GET | Read | Yes | 200 |
| POST | Create | No | 201 |
| PUT | Full update | Yes | 200 |
| PATCH | Partial update | No | 200 |
| DELETE | Delete | Yes | 204 |

## Response Format
```json
{
  "data": { ... },
  "meta": { "page": 1, "total": 100 }
}
```

## Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [{ "field": "title", "message": "Title is required" }]
  }
}
```

## Pagination
- Use cursor-based pagination for large datasets
- Include `next` and `previous` cursors in response meta
- Default page size: 50, max page size: 200
