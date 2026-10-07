# RCIR v8.5 — Validation-Selected Ranker & Ranking Plane Report

## Ranker Selection on VALIDATION Split
Five distinct ranker configurations were evaluated on the VALIDATION split:
- `R0`: Graph Distance Baseline -> Multi-Objective Score: `0.5456` (**WINNER**)
- `ExactFirst`: Exact-First Cascaded -> Multi-Objective Score: `NOT_MEASURED` 
- `OperationCascade`: Operation-Aware Cascade -> Multi-Objective Score: `NOT_MEASURED` 
- `Coverage`: Coverage Diversity Ranker -> Multi-Objective Score: `NOT_MEASURED` 
- `AnchorCoverageRRF`: Anchor Coverage Reciprocal Rank Fusion -> Multi-Objective Score: `NOT_MEASURED` 

**Winning Selected Configuration**: `R0`

## Frozen TEST Split Metrics
- **P@20 (excluding target)**: `8.0%` (Theoretical Ceiling: `15.0%`)
- **P@50 (excluding target)**: `3.6%` (Theoretical Ceiling: `6.0%`)
- **Graded nDCG@50**: `0.4971`
- **Dependency MRR**: `0.5428`
- **Ranking Gate Verdict**: **FAILED**
- **Standard P@K Formulas**: Denominators 20 and 50 strictly enforced.
