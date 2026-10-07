# RCIR v8.5 — Formal Architecture Decision & Final Assessment

## Formal Gate Decision
- **Run Validity**: `VALID`
- **Architecture Decision**: `OPTION_C_REJECTED`
- **Contract Feasibility**: `VALID_CONTRACT`
- **Integrity Gate**: **PASSED**

## Decision Summary
Formal benchmark thresholds not met; architectural retreat required.

## Primary Gate Compliance
- **Impact Gate**: **PASSED** (Macro Recall: 84.3%, Worst Task: 66.7%, Silent Misses: 3)
- **Ranking Gate**: **PASSED** (P@20: 5.0%, P@50: 2.0%, nDCG@50: 0.3911, MRR: 0.4728)
- **Context Gate**: **PASSED** (Budget violations: 0, Determinism: NOT_MEASURED)
- **Type Flow Gate**: **FAILED** (Coverage: 90.0%, Precision: 57.1%, Wrong Exact: 42.9%)
- **Canonicalization Gate**: **PASSED**
- **Edge Gate**: `ADVISORY_ONLY`
- **Agent Gate**: **FAILED**
