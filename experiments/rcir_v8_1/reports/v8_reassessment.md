# RCIR v8 — Baseline Reassessment & Scientific Audit

**Audited Commit:** `8489ece793f4d4285258b0dcb2dbd6fb6ffdc45a` (`RCIR_V8_INITIAL`)  
**Audit Date:** 2026-10-04  
**Auditor:** Principal Static-Analysis & Repository-Intelligence Auditor  
**Formal Reclassification:** **OPTION B — PARTIALLY VALIDATED** (Overturns previously claimed "Option A — Validated")

---

## 1. Executive Summary & Core Verdict

The RCIR v8 final report (`experiments/rcir_v8/reports/final_assessment.md`) concluded with:
> `OPTION A — v8 ARCHITECTURE VALIDATED (CORE POLICY P5 SELECTED)`

A rigorous scientific audit of the committed raw evaluation artifacts (`experiments/rcir_v8/results/policy_p0.json` through `policy_p6.json`) demonstrates that **this conclusion is invalid and unsupported by the data**.

While RCIR v8 introduced crucial architectural concepts—entity disambiguation, multi-view graphs, operation-specific traversal, and context compilation—it achieved higher Precision@50 and nDCG@50 primarily by applying aggressive, early candidate caps (`max_candidates = 60..150`). In doing so, it suffered catastrophic dependency coverage collapse, discarding **443 out of 721** ground-truth dependencies before the ranker even saw them.

Per Rule 0 (Evidence Before Success Claims) and the frozen benchmark contract, RCIR v8 must be formally reclassified as:

```text
B — PARTIALLY VALIDATED
```

---

## 2. Empirical Proof: The Candidate Pool Collapse

The v8 reports emphasized Top-50 precision gains and candidate volume reduction, but omitted the critical metric: **Candidate Pool Recall**.

$$\text{CandidatePoolRecall} = \frac{\text{GroundTruth} - \text{SilentMisses}}{\text{GroundTruth}}$$

### Cross-Policy Comparison Table (Raw Data)

| Policy | Description | Candidates | Ground Truth | Silent Misses | **Candidate Pool Recall** | Macro Recall@50 | Macro Precision@50 | nDCG@50 | MRR |
|---|---|---|---|---|---|---|---|---|---|
| **P0** | v7 Baseline (2-hop BFS + TF-IDF) | 7,988 | 721 | **10** | **98.61%** | 12.27% | 5.20% | 0.1924 | 0.5059 |
| **P1** | Core Traversal Rules | 1,059 | 721 | **436** | **39.53%** | 40.75% | 18.00% | 0.5186 | 0.7286 |
| **P2** | P1 + Entity Disambiguation | 984 | 721 | **445** | **38.28%** | 39.50% | 19.60% | 0.5233 | 0.7286 |
| **P3** | P2 + Directional Graph Views | 984 | 721 | **445** | **38.28%** | 39.50% | 19.60% | 0.5233 | 0.7286 |
| **P4** | P3 + Deterministic Ranker | 1,018 | 721 | **443** | **38.56%** | 47.03% | 22.40% | 0.5425 | 0.7286 |
| **P5** | P4 + Boundary & Test Graph | 1,018 | 721 | **443** | **38.56%** | 47.03% | 22.40% | 0.5425 | 0.7286 |
| **P6** | P5 + Git Co-Change (simulated) | 1,018 | 721 | **443** | **38.56%** | 47.03% | 22.40% | 0.5425 | 0.7286 |

### Critical Takeaway
- In baseline **P0**, 711 of 721 true dependencies were reached by the candidate generator (98.61% pool recall), though ranking was noisy.
- In **P5**, **443 dependencies were discarded before ranking**. The candidate generator retained only 278 true dependencies (38.56% pool recall).
- **61.44% of ground-truth dependencies were silently lost.** A static intelligence engine that misses 61.4% of affected files cannot be considered "validated" for change-impact analysis.

---

## 3. Root Cause Analysis

1. **Destructive Traversal Caps:**
   `TraversalPolicy` imposed hard limits (`max_candidates` = 60, 80, 100, 150). For wide changes (e.g., `TASK-4` with $|R| = 538$ relevant files), breadth-first search stopped prematurely after reaching the limit, truncating entire subtrees of direct exact consumers.

2. **Unenforced `min_resolution`:**
   `TraversalRule.min_resolution` was declared in code but was never enforced during traversal filtering.

3. **Suboptimal Hop Distance Calculation:**
   Path aggregation took the last or maximum encountered hop instead of the true minimum supported geodesic distance, unfairly penalizing entities that had multiple paths.

4. **Conflating Change Impact with Agent Context:**
   v8 attempted to force a single candidate list to serve two fundamentally conflicting purposes:
   - *Change Impact Analysis* (requires exhaustive, high-recall discovery of all affected consumers).
   - *Agent Context Compilation* (requires compact, high-precision context within 4k-8k token budgets).

5. **Benchmark Metric Flaw:**
   The v8 contract specified $\text{Recall@50} \ge 90\%$, which is mathematically impossible for tasks where $|R| > 50$ (such as `TASK-4` with 538 files, where maximum theoretical Recall@50 is $50 / 538 = 9.29\%$).

---

## 4. Reclassification & Transition to RCIR v8.1

Under the corrected rubric:
- **Option A (Validated):** Requires candidate pool recall $\ge 95\%$, substantial ranking improvement, valid context compiler, and verified E2E code modifications.
- **Option B (Partially Validated):** Architecture proves sound ranking, precision, and efficiency improvements, but suffers coverage gaps or benchmark contract flaws requiring corrective re-engineering.
- **Option C (Rejected):** Redesign fails to improve over baseline or introduces irrecoverable degradation.

**Verdict: OPTION B — PARTIALLY VALIDATED.**

RCIR v8.1 is chartered to resolve these defects by establishing a **Dual-Plane Architecture**:
- **Plane A (Change Impact Plane):** Guarantees high dependency coverage ($\ge 95\%$ candidate pool recall), retaining all direct exact relationships without early candidate caps.
- **Plane B (Agent Context Plane):** Performs disciplined ranking, adaptive filtering, and entity-span context compilation for downstream coding agents.
