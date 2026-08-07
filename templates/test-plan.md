# Test Plan Template

```markdown
# Test Plan — [Feature/Project Name]

## 1. Scope
[What is being tested and what is not]

## 2. Test Strategy

| Category | Purpose | Tools |
|----------|---------|-------|
| Unit Tests | Business logic verification | [Testing framework] |
| Integration Tests | External system interactions | [Testing framework] |
| E2E Tests | Full user workflows | [Testing tool] |
| Performance Tests | Load and response time | [Load testing tool] |

## 3. Test Cases

### Unit Tests
| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-01 | [Scenario] | [Input data] | [Expected result] | High/Med/Low |

### Integration Tests
| ID | Scenario | Systems Involved | Expected Behavior | Priority |
|----|----------|-----------------|-------------------|----------|
| IT-01 | [Scenario] | [Systems] | [Expected behavior] | High/Med/Low |

### Edge Cases
| ID | Scenario | Input | Expected Behavior |
|----|----------|-------|-------------------|
| EC-01 | [Edge case] | [Boundary input] | [Expected handling] |

## 4. Test Data
[Description of test data requirements]

## 5. Test Environment
[Environment requirements for testing]

## 6. Entry/Exit Criteria
- **Entry**: All code compiled, basic smoke test passes
- **Exit**: All high-priority tests pass, no P0/P1 defects open
```
