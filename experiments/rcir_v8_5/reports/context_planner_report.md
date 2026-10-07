# RCIR v8.5 — Context Planner & Budget Allocation Report

## Context Planner Invariants
1. **Target Pinning**: Target symbol and file context are always pinned first.
2. **Deterministic Role Quotas**: Allocates token budget across `TARGET`, `DIRECT_CALLER`, `IMPLEMENTATION`, `BOUNDARY`, `TEST`, and `CONFIG_SCHEMA`.
3. **Strict Budget Invariant**: Rendered token budget invariant `actual_tokens <= token_budget` has **0 violations** across all evaluated tasks.
4. **Context Representation Distribution**:
   - Extracted Source Spans (`SOURCE_SPAN`): `45`
   - Structural Summaries (`STRUCTURAL_SUMMARY`): `10`
   - Unresolved References (`UNRESOLVED`): `5`
   - Critical Source Recall at 4k: `66.7%`

## Saturation Curve on TEST Split
| Budget | Critical Source Recall | Mean Delivered Tokens | Violations |
|---|---|---|---|
| **1000** | 50.0% | 737 | 0 |
| **2000** | 60.0% | 1463 | 0 |
| **4000** | 66.7% | 3299 | 0 |
| **8000** | 86.7% | 6737 | 0 |
| **16000** | 86.7% | 13415 | 0 |
