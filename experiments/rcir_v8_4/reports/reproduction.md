# RCIR v8.4 End-to-End Reproduction Guide

To independently reproduce all empirical results and generate reports from scratch:

```bash
# 1. Run audit scripts (leakage guard and fabrication checks)
python experiments/rcir_v8_4/scripts/audit_metric_fabrication.py
python experiments/rcir_v8_4/scripts/audit_ground_truth_leakage.py

# 2. Run component benchmarks
python experiments/rcir_v8_4/scripts/evaluate_canonicalization.py
python experiments/rcir_v8_4/scripts/evaluate_edges.py
python experiments/rcir_v8_4/scripts/evaluate_type_flow.py
python experiments/rcir_v8_4/scripts/evaluate_determinism.py

# 3. Run decoupled retrieval and context compilation
python experiments/rcir_v8_4/scripts/retrieval_runner.py --split all
python experiments/rcir_v8_4/scripts/context_runner.py --split all

# 4. Evaluate predictions against independent ground truth
python experiments/rcir_v8_4/scripts/evaluate_predictions.py --split all

# 5. Evaluate formal gates
python experiments/rcir_v8_4/scripts/evaluate_gates.py

# 6. Generate reports and validate byte-consistency
python experiments/rcir_v8_4/scripts/generate_reports.py
python experiments/rcir_v8_4/scripts/validate_report_consistency.py
```
