# Playbook: Feature Development

## When to Use
Building a new feature from design through deployment.

## Process

### Step 1: Understand the Feature
1. Use the **Maker Agent** to clarify requirements
2. Define scope: what's included, what's explicitly excluded
3. Define acceptance criteria: how will you know it's done?
4. Identify dependencies on existing code

### Step 2: Design
1. Maker Agent produces design document and ADRs
2. Consider impact on existing architecture
3. Plan the data model changes (if any)
4. Plan the API changes (if any)

### Step 3: Review Design
1. **Reviewer Agent** reviews the design
2. Address findings and iterate

### Step 4: Implement
1. **Implementer Agent** breaks work into small, reviewable increments
2. Each increment: code → test → self-review
3. Keep changes minimal and focused

### Step 5: Code Review
1. **Reviewer Agent** reviews the implementation
2. Address all findings

### Step 6: Gate Review
1. **Gatekeeper Agent** verifies release readiness
2. Verify against acceptance criteria

### Step 7: Deploy & Monitor
1. Deploy to staging first
2. Verify in staging
3. Deploy to production
4. Monitor for 24-48 hours for anomalies

### Step 8: Record
1. **Historian Agent** records the feature's journey

## Decision Points

| Situation | Decision |
|-----------|----------|
| Feature requires schema change | Follow [Database Migration](database-migration.md) playbook first |
| Feature is larger than expected | Break into phases; ship phase 1 first |
| Feature requires new dependency | Follow [Dependency Management](../governance/dependency-management.md) |
| Feature conflicts with existing architecture | Create ADR, get Reviewer approval |
