# RCIR v8.2 — Reproduction Guide

## Prerequisites

- Python 3.12+
- Dependencies: `pip install -e rcir/` (from PolyFlow root)
- Precomputed graph: `experiments/nextcloud_validation/rcir/nextcloud_graph.json`

## Step-by-Step Reproduction

### 1. Run Dual-Plane Benchmark

```bash
python experiments/rcir_v8_2/scripts/run_dual_plane_benchmark.py
```

Produces:
- `results/impact_plane.json`
- `results/context_plane.json`
- `results/ranker_ablations.json`
- `results/selected_ranker_config.json`
- `results/lexical_evaluation.json`

### 2. Run Type-Flow Benchmark

```bash
python experiments/rcir_v8_2/scripts/run_type_flow_benchmark.py
```

Produces: `results/type_flow_evaluation.json`

### 3. Run Edge Evaluator

```bash
python experiments/rcir_v8_2/scripts/evaluate_edges.py
```

Produces: `results/edge_evaluation.json`

### 4. Run Agent Validation (Fail-Closed)

```bash
python experiments/rcir_v8_2/scripts/run_agent_validation.py
```

Produces:
- `results/agent_turn_budget.json`
- `results/agent_ab_runs.json`

### 5. Run Performance Benchmark

```bash
python experiments/rcir_v8_2/scripts/benchmark_performance.py
```

Produces: `results/performance_benchmark.json`

### 6. Run Gate Evaluator

```bash
python experiments/rcir_v8_2/scripts/evaluate_gates.py \
  --dual-plane experiments/rcir_v8_2/results/context_plane.json \
  --contract experiments/rcir_v8_2/benchmark_contract.json \
  --agent-ab experiments/rcir_v8_2/results/agent_ab_runs.json \
  --output experiments/rcir_v8_2/results/gate_evaluation.json
```

Produces: `results/gate_evaluation.json`

### 7. Generate Reports

```bash
python experiments/rcir_v8_2/scripts/generate_reports.py
```

Produces all Markdown reports in `experiments/rcir_v8_2/reports/`.

### 8. Run Regression Tests

```bash
pytest tests/test_rcir_v8_2.py -v
```

## Verification

```bash
python experiments/rcir_v8_2/scripts/validate_report_consistency.py
```

This verifies that all numbers in generated reports match the raw JSON artifacts.
