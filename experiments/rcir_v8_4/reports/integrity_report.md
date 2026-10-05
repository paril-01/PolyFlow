# RCIR v8.4 Integrity & Anti-Fabrication Audit Report

**Audit Decision**: RUN VALIDITY = **VALID**  
**Fabrication Count**: **0** violations detected  
**Ground Truth Leakage**: **0** violations detected  

## 1. Absolute Rule 0 Verification
Every stage of retrieval (`retrieval_runner.py`) and context compilation (`context_runner.py`) operates in strict isolation from the ground truth answer key:
- Decoupled runners have zero imports of `ground_truth.json` or `ground_truth_edges.json`.
- Prediction outputs contain only candidate entity IDs, rank scores, and file paths.
- Evaluation scripts (`evaluate_predictions.py`, `evaluate_gates.py`) ingest predictions and ground truth independently.

## 2. Rule 0.1: Synthetic Metric Prevention
- **Agent Validation**: In the absence of live LLM inference API credentials, completion rate is reported as `NOT_MEASURED`. Zero fabricated numbers are admitted into formal gates.
- **Split Isolation**: DEV (8 tasks), VALIDATION (6 tasks), and TEST (6 tasks) are strictly isolated. Gate decisions read exclusively from the frozen `test` results.
