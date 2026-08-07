# Gatekeeper Agent — Decision Framework

## Decision Matrix

| Scenario | Decision | Action |
|----------|----------|--------|
| All gates PASS, no open findings | **APPROVE** | Proceed to deployment |
| All critical gates PASS, minor docs gaps | **CONDITIONAL APPROVAL** | Deploy with follow-up tracking |
| Single P1 finding with documented fix plan | **CONDITIONAL APPROVAL** | Fix must land within 48 hours |
| Any P0 finding open | **REJECT** | Fix required before re-evaluation |
| Multiple P1 findings | **REJECT** | Systematic issues need addressing |
| Critical gate FAIL | **REJECT** | Cannot deploy until resolved |
| Missing rollback strategy | **REJECT** | Production safety requires rollback |

## Escalation

If the team disagrees with a REJECT decision:
1. Team presents evidence for why the rejection criteria should be waived
2. Gatekeeper evaluates the evidence objectively
3. If disagreement persists, escalate per [Governance](../../constitution/governance.md)
4. Decision and rationale are recorded by the Historian Agent
