# RCIR v8.1 — Complete Reproduction & Verification Guide

**Audited Commit:** `8489ece793f4d4285258b0dcb2dbd6fb6ffdc45a`  
**Target Architecture:** RCIR v8.1 Dual-Plane Repository Intelligence  
**Specification Reference:** `enhancements - 02.md` (REPRODUCIBILITY CONTRACT)

---

## 1. Prerequisites & Environment Setup

- **Python Version:** 3.10+ (Standard library with `pytest` for testing)
- **Repository Root:** PolyFlow repository root
- **Precomputed Graph:** `experiments/nextcloud_validation/rcir/nextcloud_graph.json` (50,346 nodes, 143,225 edges)

Ensure Python path includes `rcir/src`:
```powershell
$env:PYTHONPATH = "rcir/src;."
```

---

## 2. Step-by-Step Reproduction Pipeline

### Step 1: Generate Graded Ground Truth & Typed Edge Dataset
```powershell
# 1. Build graded relevance ground truth (721 files partitioned into Tiers 3, 2, 1)
python experiments/rcir_v8_1/scripts/build_graded_ground_truth.py

# 2. Build typed edge ground truth dataset (20 verified relations)
python experiments/rcir_v8_1/scripts/build_edge_ground_truth.py
```
*Output Artifacts:*
- `experiments/rcir_v8_1/ground_truth/graded_ground_truth.json`
- `experiments/rcir_v8_1/ground_truth/typed_edge_ground_truth.json`

### Step 2: Automated Typed Edge Evaluation
```powershell
python experiments/rcir_v8_1/scripts/evaluate_edges.py
```
*Output Artifacts:*
- `experiments/rcir_v8_1/results/edge_evaluation.json`
- `experiments/rcir_v8_1/reports/edge_quality_report.md`

### Step 3: Run Primary Dual-Plane Benchmark & Ablations
```powershell
python experiments/rcir_v8_1/scripts/run_dual_plane_benchmark.py
```
*Output Artifacts:*
- `experiments/rcir_v8_1/results/baseline_p0.json`
- `experiments/rcir_v8_1/results/rcir_v8_initial_p5.json`
- `experiments/rcir_v8_1/results/dual_plane_v8_1.json`
- `experiments/rcir_v8_1/results/lexical_comparison.json`
- `experiments/rcir_v8_1/results/ranker_ablations.json`
- `experiments/rcir_v8_1/reports/impact_plane_report.md`
- `experiments/rcir_v8_1/reports/context_plane_report.md`
- `experiments/rcir_v8_1/reports/ablation_report.md`

### Step 4: Run Agent Turn-Budget & A/B Evaluations
```powershell
python experiments/rcir_v8_1/scripts/run_agent_turn_experiments.py
```
*Output Artifacts:*
- `experiments/rcir_v8_1/results/agent_turn_budget.json`
- `experiments/rcir_v8_1/results/agent_ab_test.json`
- `experiments/rcir_v8_1/reports/agent_turn_budget_report.md`
- `experiments/rcir_v8_1/reports/agent_ab_report.md`

### Step 5: Execute Regression Test Suite
```powershell
pytest tests/test_rcir_v8_1.py -v
```

---

## 3. Directory Layout & Artifact Registry

```text
experiments/rcir_v8_1/
├── baseline/
│   └── baseline_manifest.json
├── datasets/
│   ├── dev.json
│   ├── validation.json
│   └── test.json
├── ground_truth/
│   ├── graded_ground_truth.json
│   └── typed_edge_ground_truth.json
├── results/
│   ├── baseline_p0.json
│   ├── rcir_v8_initial_p5.json
│   ├── dual_plane_v8_1.json
│   ├── edge_evaluation.json
│   ├── lexical_comparison.json
│   ├── ranker_ablations.json
│   ├── agent_turn_budget.json
│   └── agent_ab_test.json
├── reports/
│   ├── v8_reassessment.md
│   ├── benchmark_contract_v8_1.md
│   ├── impact_plane_report.md
│   ├── context_plane_report.md
│   ├── edge_quality_report.md
│   ├── ablation_report.md
│   ├── dataset_split_report.md
│   ├── context_compiler_report.md
│   ├── agent_turn_budget_report.md
│   ├── agent_ab_report.md
│   ├── failure_catalog.md
│   ├── final_assessment.md
│   └── reproduction.md
└── scripts/
    ├── build_graded_ground_truth.py
    ├── build_edge_ground_truth.py
    ├── evaluate_edges.py
    ├── evaluation_v8_1.py
    ├── run_dual_plane_benchmark.py
    └── run_agent_turn_experiments.py
```
