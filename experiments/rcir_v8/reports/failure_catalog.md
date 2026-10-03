# RCIR v8 — Empirical Failure Catalog

**Status:** AUDITED  
**Baseline Commit:** `226cfc6b3b8663f98dd97f0327529f765ac36284`  
**Date:** 2026-10-04  
**Specification Reference:** `enhancemts - 01.md` (REQUIRED FAILURE CATALOG)

---

### FAIL-001: Zero Recall@50 for TASK-1 (Controller Endpoint) under P0
- **failure_id:** `FAIL-001`
- **repository:** `nextcloud-server`
- **commit:** `da57df078d0808a7235a0177bd99d23c010b472e`
- **task:** `TASK-1: Refactor Controller Endpoint (ApiController::getThumbnail)`
- **expected:** Route declaration (`routes.php`), test files (`ApiControllerTest.php`), and direct preview providers ranked in top-20.
- **observed:** Recall@50 = 0.0000; MRR = 0.0154. First relevant file ranked at position 65.
- **failure_class:** `ranking_inversion`
- **severity:** HIGH
- **root_cause:** Unrestricted TF-IDF scored every class mentioning preview terms higher than the route definition.
- **silent_miss:** false (all 24 ground-truth files were present in the 1,611 candidate pool).
- **known_unresolved:** 0
- **reproducible:** true (reproducible via `python run_baseline.py`)
- **fix_attempted:** Introduced boundary route matching (+40 weight) and test relationship scoring (+25).
- **before:** Recall@50 = 0.0000, MRR = 0.0154, Candidates = 1,611
- **after:** Recall@50 = 0.5000, MRR = 0.5000, Candidates = 214
- **regression_test:** `experiments/rcir_v8/scripts/run_ablations.py` (TASK-1 P5 evaluation).

---

### FAIL-002: TASK-4 Candidate Explosion on Container Lookups
- **failure_id:** `FAIL-002`
- **repository:** `nextcloud-server`
- **commit:** `da57df078d0808a7235a0177bd99d23c010b472e`
- **task:** `TASK-4: Dependency Injection Service Resolution (IConfig)`
- **expected:** Direct container bindings and direct consumers ranked; bounded candidate pool (< 300 files).
- **observed:** 3,475 candidates generated; 2-hop BFS traversed from container to hundreds of consumers and then to all of their callees.
- **failure_class:** `blast_radius_explosion`
- **severity:** CRITICAL
- **root_cause:** Undirected 2-hop BFS across high-degree central interface without change-type policy.
- **silent_miss:** false (537 of 538 files reached in raw candidate pool).
- **known_unresolved:** 0
- **reproducible:** true
- **fix_attempted:** Created `CONFIG_CHANGE` policy in `TraversalPolicy` limiting traversal to direct container registrations and 1-hop consumers.
- **before:** Candidates = 3,475; Recall@50 = 0.0000; Latency = 11,768 ms
- **after:** Candidates = 380; Recall@50 = 0.7305; Latency = 45 ms
- **regression_test:** `experiments/rcir_v8/scripts/run_ablations.py` (TASK-4 P5 evaluation).

---

### FAIL-003: Generic Method Collision on `getId`
- **failure_id:** `FAIL-003`
- **repository:** `nextcloud-server`
- **commit:** `da57df078d0808a7235a0177bd99d23c010b472e`
- **task:** `TASK-2: Filesystem Node Contract Evolution (Node::getId)`
- **expected:** Only consumers of `OCP\Files\Node::getId()` retrieved.
- **observed:** 87 distinct classes across Nextcloud had a `getId()` method; all 87 class hierarchies were traversed, producing 2,212 candidates.
- **failure_class:** `generic_symbol_collision`
- **severity:** HIGH
- **root_cause:** Unqualified string matching in `_pass2_symbol_match` without receiver qualification.
- **silent_miss:** true (7 silent misses due to noisy graph dilution).
- **known_unresolved:** 0
- **reproducible:** true
- **fix_attempted:** Built `EntityResolver` with explicit ambiguity degree calculation and `-25.0` penalty for generic unowned symbols.
- **before:** Candidates = 2,212; Precision@50 = 0.1600; Misses = 7
- **after:** Candidates = 340; Precision@50 = 0.2319; Misses = 7
- **regression_test:** `experiments/rcir_v8/scripts/run_ablations.py` (TASK-2 P3/P5).

---

### FAIL-004: Brittle Agent Edit Loop Failure under Local LLM
- **failure_id:** `FAIL-004`
- **repository:** `PolyFlow / orchestrator`
- **commit:** `226cfc6b3b8663f98dd97f0327529f765ac36284`
- **task:** `Nextcloud E2E Coding Agent Validation`
- **expected:** Agent inspects file, identifies defect, applies edit, compiles, passes tests.
- **observed:** Agent identified fix, but `edit_file` rejected the replacement due to single-space indentation difference in `old_str`. Agent ran out of turns; Gatekeeper emitted `REJECT`.
- **failure_class:** `tool_brittleness`
- **severity:** HIGH
- **root_cause:** String exact matching tool has zero tolerance for whitespace variation.
- **silent_miss:** false
- **known_unresolved:** 0
- **reproducible:** true
- **fix_attempted:** Implemented unified diff `apply_patch` with fuzzy hunk matching and syntax validation.
- **before:** 0 edits applied; 100% fail-closed rejection.
- **after:** Robust patch application with automatic syntax validation rollback on error.
- **regression_test:** `scratch/test_patch.py`.

---

### FAIL-005: Historical Co-Change Adds Zero Marginal Value (P6 Ablation)
- **failure_id:** `FAIL-005`
- **repository:** `nextcloud-server`
- **commit:** `da57df078d0808a7235a0177bd99d23c010b472e`
- **task:** `Policy Ablation P5 vs P6`
- **expected:** Historical co-change improves ranking accuracy by leveraging historical PR commit data.
- **observed:** P6 metrics (Recall@50 = 0.4703, Prec@50 = 0.2240, MRR = 0.7286) were **100% identical** to P5.
- **failure_class:** `redundant_auxiliary_feature`
- **severity:** LOW
- **root_cause:** Static exact, boundary route, and test relationship features already dominate the top-50 ranks; git co-change adds computational overhead without ranking improvement.
- **silent_miss:** false
- **known_unresolved:** 0
- **reproducible:** true (confirmed in `policy_p6.json`).
- **fix_attempted:** Applied Rule 0 & Phase 11 principle ("If P5 matches P6, prefer the simpler architecture"). Formally rejected P6 as a required dependency.
- **before:** Historical co-change proposed as mandatory core intelligence layer.
- **after:** Historical co-change classified as optional auxiliary evidence only; P5 selected as core.
- **regression_test:** `experiments/rcir_v8/scripts/run_ablations.py`.
