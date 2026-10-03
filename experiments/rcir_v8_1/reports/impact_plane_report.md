# RCIR v8.1 — Plane A (Change Impact Plane) Evaluation Report

**Audited Commit:** `8489ece793f4d4285258b0dcb2dbd6fb6ffdc45a`  
**Experiment Date:** 2026-10-04  
**Primary Artifact:** `results/dual_plane_v8_1.json`  
**Specification Reference:** `enhancements - 02.md` (PHASES 4, 5, 6, 18, 36)

---

## 1. Executive Summary & Gate Status

Plane A (Change Impact Plane) is the foundational audit layer of RCIR v8.1. Its sole purpose is **exhaustive dependency discovery** across the repository graph without premature candidate caps.

In the v8 baseline, candidate caps (`max_candidates = 60..150`) caused catastrophic recall collapse (38.56% pool recall, 443 silent misses). RCIR v8.1 repairs this architecture by:
1. Guaranteeing protection of **ALL direct exact and direct inferred relationships**.
2. Deploying **Adaptive Fanout Control** (LOW, MEDIUM, HIGH) to govern indirect traversals.
3. Enabling cross-boundary and event companion discovery.

### Frozen Gate Evaluation
- **Target Gate:** $\text{Global CandidatePoolRecall} \ge 95.0\%$
- **Measured Result:** **97.23% Global Pool Recall** (701 / 721 dependencies recovered)
- **Silent Misses:** Reduced from **443** in v8 initial down to **20** across all 5 benchmark tasks.
- **GATE STATUS: PASSED**

---

## 2. Cross-Architecture Impact Comparison

All figures derived directly from committed raw JSON evaluation artifacts:
- Baseline P0: `results/baseline_p0.json`
- Initial v8 (P5): `results/rcir_v8_initial_p5.json`
- RCIR v8.1 Plane A: `results/dual_plane_v8_1.json`

| Architecture | Candidate Pool Size | Ground Truth | Silent Misses | Candidate Pool Recall | Mean Latency | Mean Memory |
|---|---|---|---|---|---|---|
| **RCIR v7 (P0 Baseline)** | 7,988 | 721 | 10 | 98.61% | 11,925 ms | 94.6 MB |
| **RCIR v8 Initial (P5)** | 1,018 | 721 | 443 | 38.56% | 1,098 ms | 6.5 MB |
| **RCIR v8.1 Plane A** | **2,799** | **721** | **20** | **97.23%** | **481 ms** | **3.7 MB** |

### Key Architectural Takeaways
1. **Recall Recovery:** RCIR v8.1 restores the high reachability of RCIR v7 (97.23% vs 98.61%), recovering 423 of the 443 files that v8 silently lost.
2. **Noise Reduction:** Compared to v7's uncontrolled 7,988 BFS candidate blast radius, Plane A discovers 2,799 highly structured, audit-proven candidates (65.0% reduction in blast radius).
3. **Execution Efficiency:** Mean retrieval latency dropped to **481.22 ms** with a peak memory footprint of only **3.71 MB**.

---

## 3. Per-Task Granular Breakdown

| Task ID | Domain / Change Type | Ground Truth | Pool Size | Pool Recall | Silent Misses | Nature of Misses |
|---|---|---|---|---|---|---|
| **TASK-1** | Route refactor (`getThumbnail`) | 24 | 80 | **95.83%** | 1 | `GeneratorHelper.php` (indirect trait) |
| **TASK-2** | Contract evolution (`Node::getId`) | 138 | 1,329 | **89.13%** | 15 | Distant background audit listeners |
| **TASK-3** | Event contract (`NodeDeletedEvent`) | 18 | 469 | **88.89%** | 2 | `autoload_classmap.php`, `autoload_static.php` (Composer auto-generated files) |
| **TASK-4** | Service resolution (`IConfig`) | 538 | 795 | **99.63%** | 2 | 2 peripheral 3rd-party integration adapters |
| **TASK-5** | Cross-stack client (`Recent.ts`) | 3 | 126 | **100.00%** | 0 | None (100% full recovery) |

Note on `TASK-3`: All 16 actual Nextcloud PHP source files in the ground truth were recovered; the only 2 omitted items were vendor Composer autoload mapping files (`lib/composer/composer/autoload_*.php`), which are build artifacts rather than developer-edited source code.

---

## 4. Root Architectural Repairs

1. **Resolution of Seed Entity Qualification:**
   In v8 initial, `CandidateGenerator` passed bare symbol strings (`IConfig`, `Node::getId`), which failed to match graph edges indexed with fully qualified names (`OCP\IConfig`, `OCP\Files\Node::getId`). v8.1 utilizes `EntityRegistry.by_file` and `lookup_name` to expand symbols to their canonical graph identities.

2. **Removal of Destructive Traversal Truncation:**
   Traversal rules now declare `preserve_all_direct_exact = True`. Even if thousands of direct consumers import a core service interface, BFS never truncates direct exact relationships.

3. **Adaptive Fanout Control:**
   Branching factor dynamically selects the traversal mode:
   - For `IConfig` (high degree > 50), all direct consumers are preserved, while second-hop indirect expansion is disabled, avoiding combinatorial explosion.
   - For `Recent.ts` (low degree <= 10), full 2-hop bidirectional traversal is enabled, linking frontend components through TypeScript services to backend routes.
