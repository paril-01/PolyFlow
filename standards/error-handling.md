# Error Handling Standards

## Principles
1. **Every function that can fail must communicate failure explicitly**
2. **Never swallow errors** — empty catch blocks are forbidden
3. **Provide context** — error messages should help debugging
4. **Classify errors** — distinguish recoverable from unrecoverable
5. **Fail fast, fail safely** — detect errors early, leave system in safe state

## Error Categories

| Category | Example | Response |
|----------|---------|----------|
| **Validation** | Invalid input | Return 4xx with details, don't log as error |
| **Business logic** | Insufficient funds | Return 4xx with message, log as warning |
| **Infrastructure** | Database down | Return 5xx, log as error, retry if transient |
| **Programming** | Null reference | Return 5xx, log as error with stack trace |
| **External** | Third-party API failure | Return 5xx, log as error, circuit break |

## Error Response Format
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested task was not found",
    "details": [],
    "request_id": "abc-123-def"
  }
}
```

## Rules
- ✅ Log errors with: timestamp, request ID, error code, message, stack trace, context
- ✅ Use specific error types/codes (not generic "Something went wrong")
- ✅ Set timeouts on ALL external calls
- ✅ Implement retry with exponential backoff for transient errors
- ✅ Use circuit breakers for external dependencies
- ❌ Never expose internal stack traces to end users
- ❌ Never use exceptions for control flow
- ❌ Never catch Exception/Error generically without re-throwing
