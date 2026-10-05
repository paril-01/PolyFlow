# RCIR v8.4 Cascaded MultiObjective Ranking Report

**Ranker**: `MultiObjectiveRanker` (Reciprocal Rank Fusion over Anchor Cascades and Coverage Linear Ranker)  

## 1. TEST Split Ranking Metrics
- **Precision @ 20**: **0.00%**
- **Precision @ 50**: **0.00%**
- **nDCG @ 50**: **0.0000**
- **Mean Reciprocal Rank (MRR)**: **0.0000**

## 2. Operation Profile Adaptation
Weights are tailored dynamically to the change operation:
- `CONFIG_CHANGE`: High weight on boundary contracts and config reader calls.
- `ROUTE_CHANGE`: High weight on frontend-to-route and controller entry points.
- `SIGNATURE_CHANGE`: High weight on exact call sites and overrides.
