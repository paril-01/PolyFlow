# RCIR v8.5 — Validation-Selected Ranker & Ranking Plane Report

## Ranker Selection on VALIDATION Split
Five distinct ranker configurations were evaluated on the VALIDATION split:
- `R0`: Graph Distance Baseline -> Multi-Objective Score: `0.3081` (**WINNER**)
- `ExactFirst`: Exact-First Cascaded -> Multi-Objective Score: `0.2907` 
- `OperationCascade`: Operation-Aware Cascade -> Multi-Objective Score: `0.3070` 
- `Coverage`: Coverage Diversity Ranker -> Multi-Objective Score: `0.3068` 
- `AnchorCoverageRRF`: Anchor Coverage Reciprocal Rank Fusion -> Multi-Objective Score: `0.2944` 

**Winning Selected Configuration**: `R0`

## Frozen TEST Split Metrics
- **P@20 (excluding target)**: `5.0%` (Theoretical Ceiling: `15.0%`)
- **P@50 (excluding target)**: `2.0%` (Theoretical Ceiling: `6.0%`)
- **Graded nDCG@50**: `0.3911`
- **Dependency MRR**: `0.4728`
- **Ranking Gate Verdict**: **PASSED**
- **Standard P@K Formulas**: Denominators 20 and 50 strictly enforced.
