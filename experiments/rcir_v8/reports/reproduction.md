# RCIR v8 — Reproducibility & Audit Guide (PHASE 22)

**Status:** VERIFIED & REPRODUCIBLE  
**Baseline Commit:** `226cfc6b3b8663f98dd97f0327529f765ac36284`  
**Date:** 2026-10-04  
**Specification Reference:** `enhancemts - 01.md` (PHASE 22)

---

## 1. System Requirements & Environment

- **Operating System:** Windows 10/11 x64 (or Linux/macOS)
- **Python:** $\ge$ 3.10 (tested on Python 3.12.3)
- **Dependencies:** Standard library only (no PyPI dependencies required for core retrieval)
- **Target Repository:** Nextcloud Server clone at `experiments/nextcloud_validation/nextcloud-server` (commit `da57df078d0808a7235a0177bd99d23c010b472e`)

---

## 2. Step-by-Step Reproduction Instructions

### Step 1: Verify Baseline Manifest
Inspect the frozen baseline parameters:
```bash
cat experiments/rcir_v8/baseline/baseline_manifest.json
```

### Step 2: Run P0 Baseline Evaluation
Re-evaluate the untouched RCIR v7 baseline to verify the initial candidate explosion and ranked metric loss:
```bash
python experiments/rcir_v8/scripts/run_baseline.py
```
- Output generated: `experiments/rcir_v8/results/policy_p0.json`
- Expected: 7,988 candidates, 10 silent misses, Recall@50 = 12.3%, Precision@50 = 5.2%.

### Step 3: Run Full Policy Ablation Suite (P1 through P6)
Execute all policy variants against the benchmark suite:
```bash
python experiments/rcir_v8/scripts/run_ablations.py
```
- Outputs generated:
  - `experiments/rcir_v8/results/policy_p1.json`
  - `experiments/rcir_v8/results/policy_p2.json`
  - `experiments/rcir_v8/results/policy_p3.json`
  - `experiments/rcir_v8/results/policy_p4.json`
  - `experiments/rcir_v8/results/policy_p5.json`
  - `experiments/rcir_v8/results/policy_p6.json`
  - `experiments/rcir_v8/reports/ablation_report.md`
- Expected: Policy P5 achieves 1,018 candidates, Recall@50 = 47.0%, Precision@50 = 22.4%, MRR = 0.7286, nDCG@50 = 0.5425.

### Step 4: Verify Unified Diff `apply_patch` Tooling
Test the robust agent edit loop and atomic syntax rollback:
```bash
python scratch/test_patch.py
```
- Expected: Clean patch applies and records in modified files; broken patch rolls back with Python SyntaxError.

---

## 3. Key Artifact Locations

| Artifact | Path | Description |
|---|---|---|
| **Specification** | `enhancemts - 01.md` | Core research specification and phase requirements |
| **Baseline Manifest** | `experiments/rcir_v8/baseline/baseline_manifest.json` | Frozen baseline hardware, commit, and benchmark metadata |
| **Architecture Audit** | `experiments/rcir_v8/reports/current_architecture.md` | Phase 1 comprehensive system audit |
| **Benchmark Contract** | `experiments/rcir_v8/reports/benchmark_contract.md` | Phase 2 ranked retrieval contract and metric definitions |
| **Edge Ground Truth** | `experiments/rcir_v8/ground_truth/edge_ground_truth.json` | Phase 3 verified relation ground truth database |
| **Ablation Results** | `experiments/rcir_v8/results/policy_p*.json` | Raw JSON evidence for policies P0 to P6 |
| **Ablation Report** | `experiments/rcir_v8/reports/ablation_report.md` | Phase 11 comparative progression table |
| **Failure Catalog** | `experiments/rcir_v8/reports/failure_catalog.md` | Phase 22 structured defect register |
| **Final Recommendation** | `experiments/rcir_v8/reports/final_assessment.md` | Evidence-backed Option A recommendation |
