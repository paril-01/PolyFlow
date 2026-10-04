# RCIR v8.3 — Context Planner & Role Quota Allocation Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Optimization Target**: Semantic quota planning maximizing CriticalRecall@Budget  
**Average 4k Token Utilization**: 3391.0 / 4000 tokens  

## 1. Semantic Quota Distribution
The `ContextPlanner` divides token budgets into operation-conditioned semantic roles:
- `target_definition` (20%)
- `implementation_core` (20%)
- `direct_callers` (20%)
- `verification_tests` (15%)
- `boundary_contracts` (10%)
- `impact_summary` (10%)
- `indirect_dependencies` (5%)

## 2. Fine-Grained Span vs Full File Compilation
At 4,000 tokens, the context compiler packages:
- **Exact Source Spans**: Focused method bodies and interface declarations (~70% of entries).
- **Full Files**: Pinned targets and compact contract definitions (~30% of entries).
