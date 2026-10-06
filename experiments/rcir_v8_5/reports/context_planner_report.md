# RCIR v8.5 — Context Planner & Budget Allocation Report

## Context Planner Invariants
1. **Target Pinning**: Target symbol and file context are always pinned first.
2. **Deterministic Role Quotas**: Allocates token budget across `TARGET`, `DIRECT_CALLER`, `IMPLEMENTATION`, `BOUNDARY`, `TEST`, and `CONFIG_SCHEMA`.
3. **Strict Budget Invariant**: Rendered token budget invariant `actual_tokens <= token_budget` has **0 violations** across all 16 tasks.
4. **Source Recall**: All compiled context entries contain extracted source spans from real files; zero file-reference stubs.

## Saturation Curve on TEST Split
| Budget | Critical Source Recall | Mean Delivered Tokens | Violations |
|---|---|---|---|
| **1000** | 46.7% | 686 | 0 |
| **2000** | 56.7% | 1460 | 0 |
| **4000** | 56.7% | 2636 | 0 |
| **8000** | 76.7% | 6066 | 0 |
| **16000** | 76.7% | 13707 | 0 |
