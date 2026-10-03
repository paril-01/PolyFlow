# RCIR v8.2 — Agent A/B Report

> Source artifact: `results/agent_ab_runs.json`

## Validation Status: `SIMULATED_FAIL_CLOSED_INVALID_FOR_GATE_A`

## Conditions

| Metric | Condition A (RCIR) | Condition B (No RCIR) |
|--------|--------------------|-----------------------|
| Simulated | True | True |
| Provenance Verified | False | False |
| Success Rate | 0% | 0% |
| APPROVE Verdicts | 0 | 0 |
| REJECT Verdicts | 5 | 5 |
| Status | FAIL_CLOSED_NO_LIVE_PROVIDER | FAIL_CLOSED_NO_LIVE_PROVIDER |

## Analysis

Both conditions recorded 0% success rate because no functional live LLM provider
was available. Per Phase 46, simulated agent results **cannot satisfy the Agent E2E gate**
for Option A validation.

The v8.1 historical artifact (`agent_ab_test.json`) claimed 100% success for Condition A
and 40% for Condition B, but these were fabricated values with no model provenance,
no worktree isolation, and no verification commands (Phase 45 audit).
