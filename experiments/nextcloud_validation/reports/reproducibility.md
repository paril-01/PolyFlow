# Reproduction Guide: Nextcloud Server RCIR Validation

**Repository**: `https://github.com/nextcloud/server`  
**Frozen Commit**: `da57df078d0808a7235a0177bd99d23c010b472e`  
**PolyFlow Root**: `c:\Users\Paril Rupani\OneDrive - Shri Vile Parle Kelavani Mandal\Desktop\project\PolyFlow`  

All experimental data, graphs, reports, and scripts are self-contained inside the `experiments/nextcloud_validation/` directory.

---

## 1. Environment Requirements

- **Operating System**: Windows 11 / Server 2022 (or Linux / macOS with forward-slash path support)
- **Python**: Version 3.10+ (tested on Python 3.12.3)
- **Java**: OpenJDK 21 LTS (`java`, `javac`)
- **Node.js**: Version 20+ (tested on v25.8.0, `npm 11.1.0`)
- **Git**: 2.40+

---

## 2. Step-by-Step Reproduction

### Step 1: Environment Inspection
Verify host toolchains:
```powershell
python --version
node --version
npm --version
java -version
javac -version
```

### Step 2: Target Repository Setup
Clone the frozen Nextcloud Server repository (shallow clone):
```powershell
git clone --depth=1 https://github.com/nextcloud/server.git experiments/nextcloud_validation/nextcloud-server
```

### Step 3: Run Repository Structure Analysis (Phase A)
Measures LOC, file distribution, framework patterns, migrations, and plugin apps:
```powershell
python experiments/nextcloud_validation/scripts/analyze_repo_structure.py
```
Output saved to: `experiments/nextcloud_validation/rcir/extraction_metrics.json`

### Step 4: Run RCIR Graph Extraction (Phase B)
Executes the full graph extractor over Nextcloud (5,736 PHP files, 2,573 JS/TS files):
```powershell
python experiments/nextcloud_validation/scripts/run_rcir_extraction.py
```
Outputs:
- Full dependency graph (JSON): `experiments/nextcloud_validation/rcir/nextcloud_graph.json` (~53 MB)
- Metrics: `experiments/nextcloud_validation/rcir/extraction_metrics.json`

### Step 5: Run Repository Scale Test (Phase C)
Benchmarks extraction, hierarchy building, retrieval, and impact queries across 4 real subsets:
```powershell
python experiments/nextcloud_validation/scripts/scale_test.py
```
Output saved to: `experiments/nextcloud_validation/reports/scale_test_results.json`

### Step 6: Ground Truth Establishment & Evaluation (Phase D)
Establishes independent ground truth and evaluates graph precision/recall:
```powershell
python experiments/nextcloud_validation/scripts/establish_ground_truth.py
python experiments/nextcloud_validation/scripts/evaluate_ground_truth.py
```
Output saved to: `experiments/nextcloud_validation/reports/ground_truth_evaluation.json`

### Step 7: Run Controlled Mutation Suite (Phase D)
Evaluates blast radius on 7 controlled mutations of real Nextcloud entities:
```powershell
python experiments/nextcloud_validation/controlled_cases/mutation_suite.py
```
Output saved to: `experiments/nextcloud_validation/reports/mutation_suite_results.json`

### Step 8: Run Historical PR Benchmark (Section 13)
Evaluates RCIR impact analysis against 5 actual merged PR changes:
```powershell
python experiments/nextcloud_validation/scripts/run_historical_benchmark.py
```
Output saved to: `experiments/nextcloud_validation/reports/historical_cases_results.json`

### Step 9: Run AI Engineering Agent Benchmark (Phase E)
Runs the head-to-head comparison (Baseline vs. RCIR) across 5 complex refactoring tasks:
```powershell
python experiments/nextcloud_validation/scripts/agent_harness.py
```
Output saved to: `experiments/nextcloud_validation/reports/agent_benchmark_results.json`

### Step 10: Run Zero-Cloud Isolation Validation (Phase G)
Runs core analysis operations under socket monkey-patching to verify air-gap compliance:
```powershell
python experiments/nextcloud_validation/scripts/zero_cloud_test.py
```
Output saved to: `experiments/nextcloud_validation/reports/zero_cloud_validation.json`

### Step 11: PolyFlow-Native Multi-Language Application (Phase F)
Compile and execute the polyglot cloud drive application and its agent benchmark:
```powershell
# 1. Compile Java JVM Backend
javac -d "experiments/nextcloud_validation/polyflow_app/backend-java/bin" experiments/nextcloud_validation/polyflow_app/backend-java/src/main/java/polyflow/storage/*.java

# 2. Run Java Test Suite
java -cp "experiments/nextcloud_validation/polyflow_app/backend-java/bin" polyflow.storage.TestStorageSuite

# 3. Run Node.js Frontend Suite
node experiments/nextcloud_validation/polyflow_app/frontend-ts/src/test_frontend.js

# 4. Run Complete Vertical Slice Integration Test
python experiments/nextcloud_validation/polyflow_app/tests/test_polyflow_cloud_drive.py

# 5. Run PolyFlow App Agent Benchmark
python experiments/nextcloud_validation/polyflow_app/run_polyflow_agent_benchmark.py
```
