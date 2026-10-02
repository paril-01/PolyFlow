# Nextcloud Server RCIR & PolyFlow Empirical Validation

This directory contains the reproduction harnesses, controlled mutation suites, scale tests, and AI engineering agent benchmarks for **Nextcloud Server** (`https://github.com/nextcloud/server`).

---

## 1. External Repository Reproduction (Git Submodule)

The Nextcloud server codebase is referenced at commit `da57df078d0808a7235a0177bd99d23c010b472e` (PR #64289).

To initialize the repository clone for benchmark reproduction:

```bash
# Option A: Initialize submodule via Git
git submodule update --init --recursive experiments/nextcloud_validation/nextcloud-server

# Option B: Clone external repository directly if cloned without submodules
git clone https://github.com/nextcloud/server experiments/nextcloud_validation/nextcloud-server
cd experiments/nextcloud_validation/nextcloud-server
git checkout da57df078d0808a7235a0177bd99d23c010b472e
```

All benchmark scripts feature preflight checks that verify the existence and non-empty status of `experiments/nextcloud_validation/nextcloud-server` before execution.

---

## 2. Runtime & Toolchain Prerequisites

The validation suite supports 100% native polyglot execution with zero simulated runtime mocks:
- **Python**: 3.10+ (Standard library + optional `openai` for agent harness)
- **Node.js**: v20+ / v25+ (verified for TypeScript/JavaScript cells)
- **OpenJDK**: 21 LTS (`javac` and `java` on PATH)
- **PHP**: 8.2+ / 8.3 CLI (`php` on PATH)
- **Go**: 1.22+ / 1.27 CLI (`go run` on PATH)
- **Local LLM**: Ollama (`http://localhost:11434/v1`) running `qwen2.5:0.5b` (Zero-Cloud Verified, air-gap compatible)

Run the environment verification:
```bash
python -m polyflow_sdk doctor
# or
python -m pytest tests/test_polyflow_runtime_real.py
```

---

## 3. Reproduction Commands

### A. Repository Structure Analysis
```bash
python experiments/nextcloud_validation/scripts/analyze_repo_structure.py
```
Measures live Nextcloud repository metrics: 11,793 files, 926,080 lines of code across PHP, TypeScript, JavaScript, Vue, and SCSS.

### B. RCIR Graph Extraction & Hierarchy Construction
```bash
python experiments/nextcloud_validation/scripts/run_rcir_extraction.py
```
Indexes Nextcloud into a 50,346-node, 110,854-edge graph in ~312 seconds with peak memory < 110 MB.

### C. Controlled Mutation Blast Radius & Semantic Verification
```bash
python experiments/nextcloud_validation/controlled_cases/mutation_suite.py
```
Evaluates 7 controlled mutations with semantic ground-truth filtering (verifying import and type context).

### D. AI Engineering Agent Benchmark & Retrieval Evaluation
```bash
python experiments/nextcloud_validation/scripts/agent_harness.py
```
Evaluates naive localized search vs RCIR graph contracts across 5 non-trivial tasks, and executes the real 6-stage AEF Agent Pool (`Maker` -> `Reviewer` -> `Implementer` -> `Reviewer` -> `Gatekeeper` -> `Historian`) with real token telemetry.

### E. PolyFlow-Native Application Prototype Benchmark
```bash
python experiments/nextcloud_validation/polyflow_app/run_polyflow_agent_benchmark.py
```
Evaluates cross-stack refactoring across `.poly`, Java, Python, and TypeScript artifacts.

### F. Zero-Cloud Socket Isolation Test
```bash
python experiments/nextcloud_validation/scripts/zero_cloud_test.py
```
Enforces socket-level isolation to mathematically prove zero outbound network attempts.

---

## 4. Reports & Evidence Artifacts

- **Official Benchmark Report**: [`reports/benchmark_report.md`](file:///c:/Users/Paril%20Rupani/OneDrive%20-%20Shri%20Vile%20Parle%20Kelavani%20Mandal/Desktop/project/PolyFlow/experiments/nextcloud_validation/reports/benchmark_report.md)
- **Final Validation Report**: [`reports/final_validation_report.md`](file:///c:/Users/Paril%20Rupani/OneDrive%20-%20Shri%20Vile%20Parle%20Kelavani%20Mandal/Desktop/project/PolyFlow/experiments/nextcloud_validation/reports/final_validation_report.md)
- **Failure Catalog**: [`reports/failure_catalog.md`](file:///c:/Users/Paril%20Rupani/OneDrive%20-%20Shri%20Vile%20Parle%20Kelavani%20Mandal/Desktop/project/PolyFlow/experiments/nextcloud_validation/reports/failure_catalog.md)
- **Raw Benchmark Results JSON**: [`reports/agent_benchmark_results.json`](file:///c:/Users/Paril%20Rupani/OneDrive%20-%20Shri%20Vile%20Parle%20Kelavani%20Mandal/Desktop/project/PolyFlow/experiments/nextcloud_validation/reports/agent_benchmark_results.json)
