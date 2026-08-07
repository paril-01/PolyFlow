# Naming Conventions

## Purpose
Consistent naming reduces cognitive load, improves searchability, and makes code self-documenting.

## Universal Rules

1. **Be descriptive** — names should convey meaning without context
2. **Be consistent** — same concept = same name everywhere
3. **Be searchable** — names should be unique enough to grep
4. **Avoid abbreviations** — unless universally understood (id, url, http, api)

## Convention Reference

| Element | Convention | Example |
|---------|-----------|---------|
| Classes/Types | PascalCase | `UserService`, `TaskRepository` |
| Functions/Methods | camelCase or snake_case | `calculateTotal`, `validate_input` |
| Variables | camelCase or snake_case | `userCount`, `max_retries` |
| Constants | UPPER_SNAKE_CASE | `MAX_CONNECTIONS`, `API_VERSION` |
| Booleans | is/has/can/should prefix | `isValid`, `has_permission` |
| Files (source) | Follow language convention | `user_service.py`, `UserService.ts` |
| Files (config) | kebab-case | `app-config.yaml` |
| Directories | kebab-case or snake_case | `data-access`, `business_logic` |
| Database tables | snake_case, plural | `users`, `task_assignments` |
| Database columns | snake_case | `created_at`, `is_deleted` |
| API endpoints | kebab-case, plural | `/api/v1/task-assignments` |
| Environment variables | UPPER_SNAKE_CASE | `DATABASE_URL`, `JWT_SECRET` |

## Anti-Patterns
- ❌ Single-letter variables (except `i`, `j` in loops)
- ❌ Hungarian notation (`strName`, `intCount`)
- ❌ Meaningless names (`data`, `info`, `temp`, `result`)
- ❌ Misleading names (a function called `getUser` that also modifies data)
- ❌ Inconsistent plurality (`user` table with `tasks` table)
