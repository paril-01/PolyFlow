# RCIR v8.5 — Validation-Selected Ranker & Ranking Plane Report

## Ranker Selection on VALIDATION Split
In accordance with **Phases 50-52**, five distinct ranker configurations were evaluated on the VALIDATION split:
- `R0`: Graph Distance Baseline -> Multi-Objective Score: `0.5387` (**WINNER**)
- `ExactFirst`: Exact-First Cascaded -> Multi-Objective Score: `0.5387`
- `OperationCascade`: Operation-Aware Cascade -> Multi-Objective Score: `0.5177`
- `Coverage`: Coverage Diversity Ranker -> Multi-Objective Score: `0.5279`
- `AnchorCoverageRRF`: Anchor Coverage Reciprocal Rank Fusion -> Multi-Objective Score: `0.5031`

**Winning Selected Configuration**: `R0`

## Frozen TEST Split Metrics
- **P@20 (excluding target)**: `11.0%`
- **P@50 (excluding target)**: `6.4%`
- **Graded nDCG@50**: `0.5820`
- **Dependency MRR**: `0.4228`
- **Standard P@K Formulas**: Denominators 20 and 50 strictly enforced.
