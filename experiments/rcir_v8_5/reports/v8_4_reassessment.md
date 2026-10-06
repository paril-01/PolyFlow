# RCIR v8.4 Baseline Reassessment & Scientific Invalidation Audit

**Audit Date**: 2026-10-05  
**Baseline Tag**: `RCIR_V8_4_BASELINE` (`d14daaff946b4ecdecd499add3db11f7457188a5`)  
**Formal Evaluation Status**: **INVALID — NOT_EVALUATED**  
**Audit Finding**: Multiple critical methodological and provenance failures invalidate the v8.4 formal result.

---

## 1. Executive Summary

While RCIR v8.4 made substantial architectural progress over v8.3—specifically:
- Eliminating synthetic agent simulation metrics and enforcing Rule 0 / Rule 0.1 compliance (`NOT_MEASURED`),
- Developing AST-driven forward lexical propagation in `PHPTypeFlowAnalyzer`,
- Introducing kind-based canonical entity URIs (`php://`, `ts://`, `external://`),
- Enforcing token budget ceilings on rendered markdown prompts,
- Implementing decoupled retrieval and context compilation runners,

the resulting formal gate decision (`OPTION_B`) cannot be considered scientifically valid. Pursuant to **Absolute Rule 0.1**, the v8.4 evaluation is formally declared **INVALID** and **NOT_EVALUATED** due to three fatal structural flaws:

```text
GROUND_TRUTH_PROVENANCE_FAILURE
+
SOURCE_ROOT_CONFIGURATION_FAILURE
+
GATE_CONTRACT_MISMATCH
```

---

## 2. Root Cause Analysis

### Failure Mode 1: Ground Truth Provenance Failure
- **Finding**: Ground-truth tasks in `experiments/rcir_v8_4/ground_truth/ground_truth.json` claimed upstream Nextcloud historical commit hashes (e.g. `e812d4a1b029c781037f419c89481a5330e7041f`, `7a309cb84f9812908fbb23091849102c89281a02`, `384910bc184b29c801039fbc7910482910a82710`).
- **Audit Verification**: When queried against the real Nextcloud git object database (`experiments/nextcloud_validation/nextcloud-server`), these SHAs could not be verified (`git cat-file -e <sha>^{commit}` failed).
- **Impact**: Without verified upstream commit provenance, ground-truth diffs and change sets cannot be independently audited or reproduced against real repository history.

### Failure Mode 2: Source Root Configuration Failure
- **Finding**: Evaluators, compilers, and scanners in v8.4 were instantiated using `REPO_ROOT` (pointing to the PolyFlow repository root) rather than `target_repo_root` (`experiments/nextcloud_validation/nextcloud-server`).
- **Impact**: 
  - `ContextCompiler` looked for Nextcloud files inside `PolyFlow/lib/...` instead of `PolyFlow/experiments/nextcloud_validation/nextcloud-server/lib/...`.
  - When target source files could not be opened, context compilation defaulted to filename references rather than actual source code spans.
  - `PHPTypeFlowAnalyzer` evaluated files against empty or misplaced roots, failing to inspect genuine repository ASTs.

### Failure Mode 3: Gate Contract Mismatch & Ad-Hoc Decision Logic
- **Finding**: `benchmark_contract.json` specified clear conditions for Option B:
  - `global_pool_recall_min: 0.90`
  - `precision_at_50_improvement_over_p0: 0.15`
  - `context_compiler_deterministic: true`
- **Deviation**: When test macro candidate recall reached 48.61% (below 90%), `evaluate_gates.py` substituted ad-hoc logic (`elif det_passed and tf_passed and (gate_context_passed or gate_impact_passed): architecture_decision = "OPTION_B"`) rather than executing the strict contract specification.
- **Impact**: A formal benchmark evaluator must be an executable specification of its contract. Any ad-hoc substitution invalidates the formal gate.

### Failure Mode 4: Edge Ground Truth Mislabeling & Non-Standard Precision
- **Finding**: Relationships in `ground_truth_edges.json` labeled class-interface implementations (`AllConfig implements IConfig`) as `inherits`.
- **Finding**: Precision was computed as `exact / (exact + wrong_relation)` over ground-truth positives rather than over a defined prediction universe with false-positive tracking.

### Failure Mode 5: Missing Run Manifest & Artifact Provenance
- **Finding**: v8.4 generated output JSON files without a unified run manifest (`manifests/benchmark_run_manifest.json`) and lacked strict `run_id` consistency validation across dependent artifacts.

---

## 3. Mandatory v8.5 Remediations

To establish irreproachable scientific rigor, RCIR v8.5 mandates:

1. **BenchmarkEnvironment**: Single unified configuration object providing verified paths to `target_repo_root`, `polyflow_root`, `graph_path`, etc., with fail-fast sentinel checks (`IConfig.php`, `.git`).
2. **Real Upstream Git Provenance**: Every task in DEV, VALIDATION, and TEST must trace to an authentic, verified commit in the target repository history with reconstructible parent commit and diff.
3. **Canonical Graph Internal/External Indexing**: Endpoints declared inside the target repository must never fall back to `external://`.
4. **Exact Edge Taxonomy & Evaluated Prediction Universe**: Distinct `implements`, `inherits`, `calls`, `injects`, `route_to_controller`, etc., evaluated with exact canonical endpoint matching.
5. **Real Source Context & Source Recall**: Distinguish `CriticalFileRecall@Budget` from `CriticalSourceRecall@Budget`. Stubs (`// File referenced: ...`) are strictly rejected.
6. **Multi-Channel Retrieval Architecture**: 7 semantic discovery channels (Exact Graph, Type Flow, Boundary, Events, Config/DI, Verification, Lexical Fallback) with deterministic evidence fusion.
7. **Unified Run Manifest & Run ID Invariance**: Strict cryptographic hash recording across all contracts, datasets, ground truths, configurations, and artifacts.
8. **Real Agent Execution Branch**: Live execution with authentic provider models, isolated worktrees, and pre-test fail / post-test pass verification.
