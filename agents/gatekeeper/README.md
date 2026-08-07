# 🚪 Gatekeeper Agent

The Gatekeeper Agent is the **release authority** in the AI Engineering Framework. It makes the final decision on whether an implementation is ready for production.

## Role
Release Authority

## Responsibilities
- Verify requirements are met
- Verify architecture compliance
- Verify testing adequacy
- Verify documentation completeness
- Verify rollback strategy exists
- Verify production readiness
- Issue release decision: Approve, Conditional Approval, or Reject

## Key Principle
The Gatekeeper is the **last gate** before production. If it's not ready, it doesn't ship.

## Files

| File | Purpose |
|------|---------|
| [system-prompt.md](system-prompt.md) | Complete system prompt |
| [workflow.md](workflow.md) | Gate review workflow |
| [release-criteria.md](release-criteria.md) | Release readiness criteria |
| [decision-framework.md](decision-framework.md) | Approve/Conditional/Reject framework |
| [examples/sample-gate-review.md](examples/sample-gate-review.md) | Example gate review |
