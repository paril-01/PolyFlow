# Playbook: Technical Debt Management

## When to Use
Managing, tracking, and resolving technical debt across the codebase.

## Process

### Step 1: Identify
1. Flag debt during code reviews
2. Flag debt during implementation (when a shortcut is taken)
3. Flag debt during incident investigations
4. Regular "debt discovery" sessions (quarterly)

### Step 2: Document
For each debt item, record:
- What the debt is
- Why it was introduced (business pressure, time constraint, knowledge gap)
- Impact (what's worse because of this debt?)
- Effort to fix (T-shirt size: S/M/L/XL)
- Priority (critical/high/medium/low)

### Step 3: Prioritize
Use this matrix to prioritize debt resolution:

| Impact \ Effort | Small | Medium | Large |
|----------------|-------|--------|-------|
| **High** | Fix NOW | Fix this sprint | Plan for next quarter |
| **Medium** | Fix this sprint | Plan next sprint | Backlog |
| **Low** | Backlog | Backlog | Accept |

### Step 4: Resolve
1. Treat debt resolution like feature work — design, review, test
2. Follow the [Refactoring](refactoring.md) playbook for structural debt
3. Don't mix debt resolution with feature work in the same PR

### Step 5: Track
1. **Historian Agent** maintains the technical debt registry
2. Review debt trends quarterly — is debt increasing or decreasing?
3. Set a debt budget — allocate 10-20% of each sprint to debt resolution

## Types of Technical Debt

| Type | Example | Typical Fix |
|------|---------|------------|
| **Code quality** | Duplicated code, unclear naming | Refactoring |
| **Architecture** | Wrong pattern, tight coupling | Redesign + refactor |
| **Testing** | Missing tests, flaky tests | Write/fix tests |
| **Documentation** | Outdated docs, missing docs | Update documentation |
| **Dependencies** | Outdated libraries, vulnerable deps | Update/replace deps |
| **Infrastructure** | Manual deployment, no monitoring | Automate, add observability |
