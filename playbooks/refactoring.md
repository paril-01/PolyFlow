# Playbook: Refactoring

## When to Use
Restructuring existing code without changing its external behavior.

## Process

### Step 1: Define the Goal
1. Why are you refactoring? (readability, performance, testability, architecture)
2. What is the scope? (single function, class, module, cross-cutting)
3. What is the definition of done?

### Step 2: Ensure Safety Net
1. **Verify existing tests pass** — if no tests exist, write them FIRST
2. Characterization tests — tests that document current behavior (even if buggy)
3. Know what the correct behavior is before changing anything

### Step 3: Refactor in Small Steps
1. Make one small change at a time
2. Run tests after every change
3. Commit frequently — every green test run is a save point
4. If tests break, revert and try a smaller step

### Step 4: Review
1. Submit for Reviewer Agent review
2. Verify no behavior changes (only structural changes)
3. Verify no performance regressions

## Key Rules
- ✅ Tests must pass before, during, and after refactoring
- ✅ Separate refactoring from feature work (different commits/PRs)
- ✅ One refactoring technique at a time
- ❌ Never refactor without tests
- ❌ Never refactor and change behavior simultaneously
- ❌ Never refactor code you don't understand yet
