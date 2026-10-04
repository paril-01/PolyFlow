# RCIR v8.3 — Benchmark Reproduction Guide

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Target Repository**: `nextcloud-server`  
**Base Commit**: `07bf269d2eaae6c220978e302c1504434e0dd06e`

## 1. Environment Requirements
- Python 3.10+
- Dependencies: Standard library only (`json`, `hashlib`, `re`, `pathlib`, `collections`, `dataclasses`, `enum`)

## 2. Step-by-Step Reproduction
To reproduce all v8.3 benchmark results and reports identically from scratch:

```bash
# 1. Audit ground truth leakage barrier (must return 0 violations)
python experiments/rcir_v8_3/scripts/audit_ground_truth_leakage.py

# 2. Build verified canonical ground truth
python experiments/rcir_v8_3/scripts/build_canonical_ground_truth.py

# 3. Execute Dual-Plane Benchmark (Impact Plane + Context Plane)
python experiments/rcir_v8_3/scripts/run_dual_plane_benchmark.py

# 4. Run PHP Type-Flow evaluation
python experiments/rcir_v8_3/scripts/run_type_flow_benchmark.py

# 5. Evaluate typed edge recall
python experiments/rcir_v8_3/scripts/evaluate_edges.py

# 6. Run live agent capability probe
python experiments/rcir_v8_3/scripts/run_agent_validation.py

# 7. Evaluate external generalization
python experiments/rcir_v8_3/scripts/run_external_generalization.py

# 8. Evaluate machine benchmark gates
python experiments/rcir_v8_3/scripts/evaluate_gates.py

# 9. Generate all reports
python experiments/rcir_v8_3/scripts/generate_reports.py

# 10. Validate byte/hash consistency of reports
python experiments/rcir_v8_3/scripts/validate_report_consistency.py
```
