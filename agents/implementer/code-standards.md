# Implementer Agent — Code Standards

## Language-Agnostic Code Quality Standards

These standards apply regardless of programming language. They represent the minimum quality bar for production code.

---

## Structure

### File Organization
- One primary concept per file (class, module, component)
- Files should be under 300 lines (guideline, not hard rule)
- Group related files in directories with clear naming
- Separate concerns: data access, business logic, presentation, configuration

### Function Design
- **Single responsibility** — one function, one job
- **Clear naming** — the name should describe what it does
- **Limited parameters** — prefer 3 or fewer; use structured types for more
- **Short body** — prefer under 20 lines
- **Guard clauses** — return early for error/edge cases
- **No side effects** in pure logic functions
- **Explicit return types** — make the contract clear

### Class/Module Design
- **Single Responsibility Principle** — one reason to change
- **Small public API** — expose only what's necessary
- **Dependency injection** — accept dependencies, don't create them
- **Immutability preferred** — mutable state is a source of bugs

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions/Methods | verb_noun or verbNoun | `calculate_total`, `validateInput` |
| Variables | descriptive noun | `user_count`, `activeConnections` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Booleans | is/has/can/should prefix | `is_valid`, `hasPermission` |
| Classes/Types | PascalCase | `UserService`, `TaskRepository` |
| Files | kebab-case or snake_case | `user-service.ts`, `task_repository.py` |
| Directories | kebab-case | `data-access`, `business-logic` |

### Naming Rules
- ❌ No single-letter variables (except loop counters `i`, `j`)
- ❌ No abbreviations unless universally understood (`id`, `url`, `http`)
- ❌ No Hungarian notation (`strName`, `intCount`)
- ✅ Names should be pronounceable
- ✅ Names should be searchable (grep-friendly)
- ✅ Longer names for larger scopes; shorter for small, obvious scopes

---

## Error Handling

### Principles
1. **Every function that can fail should communicate failure explicitly**
2. **Never swallow errors** — empty catch/except blocks are forbidden
3. **Provide context** — error messages should help debugging
4. **Classify errors** — distinguish recoverable from unrecoverable
5. **Log errors with context** — include request ID, input, and stack trace

### Patterns

```
# GOOD: Explicit error handling
try:
    result = database.query(sql, params)
except DatabaseConnectionError as e:
    logger.error("Database query failed", extra={"query": sql, "error": str(e)})
    raise ServiceUnavailableError("Unable to process request") from e

# BAD: Swallowing errors
try:
    result = database.query(sql, params)
except Exception:
    pass  # ❌ NEVER DO THIS
```

---

## Testing Standards

### Test Organization
- Test files mirror source file structure
- Test function names describe the scenario: `test_create_task_with_valid_input_returns_201`
- Group tests by feature or behavior, not by method

### Test Quality
- Each test tests ONE thing
- Tests are independent — no shared mutable state between tests
- Tests are deterministic — same result every run
- Tests are fast — unit tests under 100ms each
- Tests use realistic data (not just "test", "foo", "bar")

### Test Categories
| Category | What it Tests | Speed | Isolation |
|----------|--------------|-------|-----------|
| Unit | Business logic, algorithms | Fast | Fully isolated |
| Integration | Database, API, external services | Medium | Partially isolated |
| End-to-end | Full user workflows | Slow | No isolation |
| Edge case | Boundary conditions | Fast | Fully isolated |
| Error path | Failure scenarios | Fast | Fully isolated |

### Coverage Expectations
- **Critical business logic**: 90%+ coverage
- **Data access layer**: 80%+ coverage
- **Utility functions**: 80%+ coverage
- **Configuration/wiring**: Coverage not required

---

## Documentation

### Inline Comments
- Comment **WHY**, not **WHAT** — the code shows what
- Comment workarounds with a link to the issue/ticket
- Comment performance-critical sections explaining the approach
- Comment complex algorithms with a brief explanation

### Docstrings/API Documentation
- Every public function/method gets a docstring
- Include: purpose, parameters, return value, exceptions, example
- Keep docstrings updated when behavior changes

---

## Anti-Patterns to Avoid

- 🚫 **God classes/functions** — doing too much in one place
- 🚫 **Premature optimization** — optimize when benchmarks prove a problem
- 🚫 **Magic numbers/strings** — use named constants
- 🚫 **Deep nesting** — use guard clauses and early returns
- 🚫 **Boolean parameters** — use enums or separate functions
- 🚫 **Commented-out code** — delete it; version control remembers
- 🚫 **Copy-paste programming** — abstract shared logic
- 🚫 **Stringly-typed code** — use proper types/enums
