# Testing Standards

## Testing Pyramid

```
        ╱  E2E Tests  ╲          Few, slow, expensive
       ╱────────────────╲
      ╱ Integration Tests╲       Some, medium speed
     ╱────────────────────╲
    ╱    Unit Tests         ╲    Many, fast, cheap
   ╱────────────────────────╲
```

## Standards by Category

### Unit Tests
- Test business logic in isolation
- Mock external dependencies
- Fast (<100ms each)
- Deterministic (same result every run)
- Independent (no order dependency)
- High coverage for critical paths (90%+)

### Integration Tests
- Test interactions with real external systems
- Use test databases, test APIs
- Verify data flows correctly across boundaries
- Test error scenarios (unavailable dependencies)

### End-to-End Tests
- Test complete user workflows
- Use realistic data
- Run in an environment that mirrors production
- Focus on critical user journeys, not every feature

### Test Naming
Use descriptive names: `test_[scenario]_[expected_behavior]`
- ✅ `test_create_task_with_missing_title_returns_422`
- ❌ `test_task_1`

### Test Data
- Use realistic, representative data
- Use factories/builders for test data creation
- Never use production data in tests
- Clean up test data after tests run

### What NOT to Test
- Third-party library internals
- Trivial getters/setters
- Framework configuration (unless customized)
