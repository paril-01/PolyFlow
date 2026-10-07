# RCIR v8.5 — Context Planner & Budget Allocation Report

## Context Planner Invariants
1. **Target Pinning**: Target symbol and file context are always pinned first.
2. **Deterministic Role Quotas**: Allocates token budget across `TARGET`, `DIRECT_CALLER`, `IMPLEMENTATION`, `BOUNDARY`, `TEST`, and `CONFIG_SCHEMA`.
3. **Strict Budget Invariant**: Rendered token budget invariant `actual_tokens <= token_budget` has **0 violations** across all evaluated tasks.
4. **Context Representation Distribution**:
   - Extracted Source Spans (`SOURCE_SPAN`): `41`
   - Structural Summaries (`STRUCTURAL_SUMMARY`): `15`
   - Unresolved References (`UNRESOLVED`): `4`
   - Critical Source Recall at 4k: `73.3%`

## Saturation Curve on TEST Split
| Budget | Critical Source Recall | Mean Delivered Tokens | Violations |
|---|---|---|---|
| **1000** | 50.0% | 743 | 0 |
| **2000** | 60.0% | 1606 | 0 |
| **4000** | 73.3% | 2852 | 0 |
| **8000** | 80.0% | 5841 | 0 |
| **16000** | 80.0% | 9981 | 0 |
