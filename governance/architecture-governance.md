# Architecture Governance

## Purpose
Ensure that the system's architecture remains consistent, intentional, and aligned with documented decisions over time.

## Rules

### 1. All Architecture Decisions Must Be Documented
- Every significant architecture decision requires an ADR
- "Significant" = affects system structure, component boundaries, data flow, or technology choice
- ADRs must be reviewed before implementation

### 2. No Unauthorized Architecture Changes
- Changes to component boundaries, data flow, or system topology require ADR approval
- Refactoring within a component is allowed without ADR (unless it changes the API)
- New dependencies require justification

### 3. Architecture Patterns Must Be Consistent
- If the project uses a layered architecture, all modules follow the same layering
- If the project uses event-driven patterns, new features follow the same pattern
- Deviations require ADR documentation

### 4. Dependency Direction
- Dependencies flow in one direction (e.g., presentation → business logic → data access)
- Circular dependencies are not allowed
- Domain/business logic must not depend on infrastructure details

### 5. Component Boundaries
- Each component has a clear, documented responsibility
- Components communicate through defined interfaces
- Internal implementation details are not exposed

## Enforcement

The Reviewer Agent checks architecture compliance during every review. The Gatekeeper Agent verifies architecture compliance before release.
