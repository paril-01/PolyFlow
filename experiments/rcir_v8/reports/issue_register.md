# RCIR v8 — Issue Register & Architectural Defect Catalog

**Status:** ACTIVE & TRACKED  
**Baseline Commit:** `226cfc6b3b8663f98dd97f0327529f765ac36284`  
**Date:** 2026-10-04  
**Specification Reference:** `enhancemts - 01.md` (PHASE 22)

---

## 1. Defect Register Summary

This register formally documents the core architectural defects identified during the RCIR v7 audit, the empirical evidence demonstrating the failure, the root cause, and the corresponding architectural remediation implemented in RCIR v8.

| Issue ID | Severity | Category | Symptom in Baseline | Root Cause in v7 | RCIR v8 Architectural Fix | Status |
|---|---|---|---|---|---|---|
| **ISSUE-01** | CRITICAL | Retrieval Precision | 5.6% macro precision; 7,276 FP candidates | Unrestricted 2-hop bidirectional BFS across 143k edges | Multi-View Graph + Directional `TraversalPolicy` (Phase 6, 7) | RESOLVED (P5 precision 22.4%) |
| **ISSUE-02** | CRITICAL | Context Utility | Recall@50 = 12.3% despite 96.7% candidate pool | Lack of typed ranking; false positives push true dependencies beyond K=50 | Deterministic Multi-Factor Ranker (Phase 10) | RESOLVED (P5 Recall@50 47.0%) |
| **ISSUE-03** | HIGH | Entity Identity | Symbol collision on common names like `getId` | Unqualified string matching without receiver/namespace | Stable `EntityIdentity` and `EntityResolver` (Phase 5) | RESOLVED |
| **ISSUE-04** | HIGH | Evaluation Integrity | "96.7% recall" masked 87.7% top-50 loss; file recall called edge metric | Binary set-membership evaluation without ranked metrics | Formal Ranked Benchmark Contract (Recall@K, MRR, nDCG) (Phase 2) | RESOLVED |
| **ISSUE-05** | HIGH | Agent Edit Loop | Local LLMs failed to produce exact old_str/new_str matches | Brittle exact substring replacement tool (`edit_file`) | Unified diff `apply_patch` with atomic syntax rollback (Phase 15) | RESOLVED |
| **ISSUE-06** | MEDIUM | Context Compilation | Context dumping candidate sets directly to LLM | No granularity selection or token budgeting | Multi-Granularity `ContextCompiler` (Phase 13) | RESOLVED |
| **ISSUE-07** | MEDIUM | Orchestration Overhead | 6 fixed stages invoked for simple 1-line changes | Monolithic fixed sequential orchestration | Adaptive `TaskRiskRouter` (Phase 17) | RESOLVED |
| **ISSUE-08** | MEDIUM | Ground Truth Fidelity | Only 10 ad-hoc test cases without formal edge schema | Incomplete ground truth specification | Formal Phase 3 Edge Ground Truth Database with line provenance | RESOLVED |

---

## 2. Detailed Issue Analyses

### ISSUE-01: Candidate Explosion via Undirected BFS
- **Empirical Evidence:** In `run_baseline.py`, 7,988 candidates were retrieved across 5 benchmark tasks. In TASK-4 (`IConfig`), 3,475 candidate files were pulled into memory.
- **Root Cause:** In `rcir/impact.py` line 212, `hop1_endpoints` was expanded bidirectionally to all incoming and outgoing `calls` and `imports` edges. Any connection to a core container or utility pulled in the entire repository.
- **Fix in v8:** `TraversalPolicy` dictates edge traversal rules per change operation. For `config_change`, only `config_service` and direct container bindings are followed. Candidate volume dropped from 7,988 to 1,018 (87.3% reduction).

### ISSUE-02: Poor Useful Top-50 Ranking
- **Empirical Evidence:** In `policy_p0.json`, TASK-1 had Recall@50 of 0.0% and MRR of 0.0154, even though all 24 ground truth files were reachable in the candidate pool.
- **Root Cause:** Hybrid retrieval scored candidates purely by TF-IDF on symbol signatures and 0.5 hop decay. Generic classes matching query keywords ranked ahead of the actual routes and test cases.
- **Fix in v8:** `DeterministicRanker` incorporates boundary contracts (+40), direct test relationships (+25), change-type compatibility (+30), and penalizes hop distance (-12) and hub degree. Useful Recall@50 jumped from 12.3% to 47.0%, and nDCG@50 improved from 0.1924 to 0.5425.

### ISSUE-03: Generic Symbol Collision (`getId`)
- **Empirical Evidence:** In TASK-2, `getId` matched 87 distinct classes in Nextcloud, causing 2,212 candidates to be emitted.
- **Root Cause:** Regex scanning in `_pass2_symbol_match` matched any symbol ending with `getId`.
- **Fix in v8:** `EntityResolver` indexes by `(owner, name)` and explicit namespace. When a generic symbol is queried without owner qualification, an ambiguity penalty (-25) is applied, prioritizing specific interface implementations over generic method occurrences.

### ISSUE-05: Brittle Substring Editing
- **Empirical Evidence:** In Nextcloud E2E agent validation, the local model produced valid code changes but failed because of single-character whitespace mismatches in `old_str`.
- **Root Cause:** `edit_file` required bit-exact substring matching.
- **Fix in v8:** `apply_patch` accepts unified diffs, performs fuzzy hunk alignment, validates Python/JSON syntax before committing, and automatically rolls back if syntax errors are detected.
