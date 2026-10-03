# RCIR v8 — Deterministic Ranking & Pruning Report (PHASE 10)

**Status:** APPROVED  
**Date:** 2026-10-04  
**Data Artifacts:** `experiments/rcir_v8/results/policy_p5.json`, `experiments/rcir_v8/results/policy_p0.json`  
**Specification Reference:** `enhancemts - 01.md` (PHASE 10)

---

## 1. Objective & Methodology

The goal of the RCIR v8 ranking engine is to convert a high-recall candidate pool into an ordered sequence where relevant files appear in the top-5 to top-50 positions, suitable for prompt injection into coding agents.

Prior to v8, candidates were sorted by an ad-hoc combination of uncalibrated TF-IDF and raw hop decay ($0.5^{\text{hop}}$), resulting in relevant files being buried at ranks 50 to 500.

The v8 **Deterministic Multi-Factor Ranker** uses transparent linear features, explicit penalty dampening, and hard contradiction pruning without unexplainable neural heuristics.

---

## 2. Linear Scoring Model & Weights

Each candidate's score is computed as:

$$\text{Score} = \sum w_i \cdot f_i - \sum p_j \cdot c_j$$

### Positive Feature Weights

| Feature | Weight ($w_i$) | Rationale |
|---|---|---|
| `exact_entity_match` | **+100.0** | Explicit target entity named in change specification |
| `boundary_contract` | **+40.0** | Direct route declaration, API endpoint, or cross-stack client mapping |
| `static_exact_edge` | **+35.0** | AST-verified compile-time static binding |
| `change_type_compat_high` | **+30.0** | Edge matches semantic operation (e.g. event dispatcher for event change) |
| `direct_test_relationship`| **+25.0** | Direct test class targeting the modified unit |
| `static_inferred_edge` | **+15.0** | Typed inference (e.g. DI container type hint) |
| `change_type_compat_med` | **+10.0** | General transitive dependency |
| `lexical_relevance` | **+8.0 $\times$ TF-IDF** | Term frequency / inverse document frequency match |
| `test_utility` | **+5.0** | General test framework utility |

### Penalty Weights

| Penalty | Value ($p_j$) | Rationale |
|---|---|---|
| `hop_penalty` | **-12.0 per hop** | Penalizes distant transitive dependencies |
| `module_penalty` | **-15.0 per boundary** | Cross-app/core boundary crossing penalty |
| `ambiguity_penalty` | **-25.0** | Applied when symbol has $\ge 5$ distinct class owners |
| `hub_penalty` | **-3.0 $\times \log_{10}(\text{in-degree})$** | Suppresses hub contamination from generic utility classes |

### Hard Contradiction Pruning
Candidates carrying hard contradictions are immediately pruned:
- `vendor_external_code`: Code in `vendor/` or `3rdparty/` when scope is internal.
- `incompatible_route`: HTTP method or route pattern contradiction.
- `wrong_receiver_type`: Method call matching query name on unrelated class hierarchy.

---

## 3. Empirical Comparative Ranking Results (P0 vs. P5)

| Task ID | Target Domain | Baseline P0 Recall@20 | Baseline P0 Recall@50 | v8 P5 Recall@20 | v8 P5 Recall@50 | Baseline MRR | v8 P5 MRR |
|---|---|---|---|---|---|---|---|
| **TASK-1** | Controller (`getThumbnail`) | 0.0000 | 0.0000 | **0.5000** | **0.5000** | 0.0154 | **0.5000** |
| **TASK-2** | Interface (`getId`) | 0.0362 | 0.0580 | **0.1449** | **0.2319** | 0.5000 | **0.5000** |
| **TASK-3** | Event (`NodeDeletedEvent`) | 0.2222 | 0.2222 | **0.4444** | **0.5556** | 1.0000 | **1.0000** |
| **TASK-4** | DI (`IConfig`) | 0.0000 | 0.0000 | **0.3903** | **0.7305** | 0.0141 | **0.6429** |
| **TASK-5** | Cross-Stack (`Recent.ts`) | 0.3333 | 0.3333 | **0.3333** | **0.3333** | 1.0000 | **1.0000** |
| **Macro Average** | — | **0.1183** | **0.1227** | **0.3636** | **0.4703** | **0.5059** | **0.7286** |

---

## 4. Key Ranking Triumphs

1. **TASK-1 (Controller Endpoint):**
   Under P0, Recall@50 was **0.0%**. Under v8 P5, routes and preview providers rank immediately in top-10, yielding **Recall@20 of 50.0%** and **MRR jumping from 0.0154 to 0.5000**.
2. **TASK-4 (Dependency Injection):**
   Under P0, `IConfig` was buried by 3,475 BFS candidates, with Recall@50 = **0.0%**. Under v8 P5, Recall@50 reached **73.1%**, and MRR rose from **0.0141 to 0.6429**.
3. **Macro Quality Metric (nDCG@50):**
   nDCG@50 improved from **0.1924 to 0.5425** (a 2.8x improvement across the benchmark).
