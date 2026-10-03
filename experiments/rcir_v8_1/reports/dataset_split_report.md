# RCIR v8.1 — Dataset Split & Benchmark Architecture Report

**Version:** 8.1  
**Status:** COMPLETE & FROZEN  
**Specification Reference:** `enhancements - 02.md` (PHASES 21 & 22)

---

## 1. Executive Summary & Split Philosophy

In RCIR v8 initial, `dev.json`, `validation.json`, and `test.json` existed as declarative stubs, but were not partitioned during ablation execution. RCIR v8.1 formally codifies the three-tier split contract:

1. **Development Split (`dev.json`):**
   - Purpose: Feature experimentation, linear weight tuning, fanout threshold calibration.
   - Ground truth accessible for hyperparameter selection.
2. **Validation Split (`validation.json`):**
   - Purpose: Architecture selection (e.g. Dual-Plane vs Single-Plane, BM25 vs TF-IDF selection).
   - Never used for micro-tuning individual weights.
3. **Test Split (`test.json`):**
   - Purpose: Immutable, frozen final evaluation.
   - Evaluated once to verify the winning architecture; never used to influence ranking heuristics or traversal rules.

---

## 2. Benchmark Task Categories & Coverage

The Nextcloud evaluation benchmark covers the primary categories required by Phase 22:

| Task ID | Task Title | Category | Target Symbol | Target File | Change Operation | Ground Truth Size |
|---|---|---|---|---|---|---|
| **TASK-1** | Refactor Controller Endpoint | `controller_route` | `getThumbnail` | `apps/files/lib/Controller/ApiController.php` | `route_change` | 24 |
| **TASK-2** | Filesystem Node Contract Evolution | `interface_method` | `getId` | `lib/public/Files/Node.php` | `signature_change` | 138 |
| **TASK-3** | Event Contract Evolution | `event_contract` | `NodeDeletedEvent` | `lib/public/Files/Events/Node/NodeDeletedEvent.php` | `event_change` | 18 |
| **TASK-4** | DI Service Resolution | `dependency_injection` | `IConfig` | `lib/public/IConfig.php` | `config_change` | 538 |
| **TASK-5** | Cross-Stack API Contract Boundary | `cross_stack` | `Recent.ts` | `apps/files/src/services/Recent.ts` | `service_boundary_change` | 3 |
| **Total** | — | — | — | — | — | **721 files** |

---

## 3. Ground Truth Independence & Adjudication Rules

1. **Independent Derivation:** Ground truth relevance tiers (Tier 3 MUST_CHANGE, Tier 2 MUST_INSPECT, Tier 1 SUPPORTING) are constructed from code structure and test manifests independently of RCIR retrieval passes.
2. **No Data Leakage:** Ranker weights and traversal multipliers are not fitted to individual test files. All rules operate on generic AST relations (`calls`, `inherits`, `imports`, `implements`, `route_to_controller`, `frontend_to_route`).
3. **Audit Reproducibility:** Every ground-truth assignment is committed to `experiments/rcir_v8_1/ground_truth/graded_ground_truth.json` with machine-readable metadata.
