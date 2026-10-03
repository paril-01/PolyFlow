# RCIR v8.1 — Formal Scientific Reassessment and Audit

**Evaluation Target:** RCIR v8.1 (Frozen baseline commit `a1d2b4861e22b50039790b4be12cdffc72f3671a`, tagged `RCIR_V8_1_BASELINE`)  
**Auditor:** Principal Static-Analysis, Compiler, and Benchmark Auditor  
**Date:** 2026-10-04  
**Primary Authority:** ABSOLUTE RULE 0 — Raw Machine-Readable Evidence Only  
**Raw Artifacts Audited:**
- `experiments/rcir_v8_1/results/dual_plane_v8_1.json`
- `experiments/rcir_v8_1/results/ranker_ablations.json`
- `experiments/rcir_v8_1/results/edge_evaluation.json`
- `experiments/rcir_v8_1/results/agent_turn_budget.json`
- `experiments/rcir_v8_1/results/agent_ab_test.json`
- `experiments/rcir_v8_1/results/lexical_comparison.json`

---

## 1. Executive Summary & Corrected Reclassification

In the v8.1 evaluation cycle, the final report declared `OPTION A — VALIDATED`. A rigorous audit of the committed raw machine-readable JSON artifacts reveals that this conclusion was scientifically unsound, as it substituted an isolated ablation configuration (`R0`) for the primary pipeline (`R5`), overlooked multiple failed primary decision gates, and accepted simulated agent outputs.

When evaluated strictly against the frozen v8.1 benchmark contract (`experiments/rcir_v8_1/reports/benchmark_contract_v8_1.md`) using only raw data:

```text
CORRECTED FORMAL VERDICT: OPTION B — PARTIALLY VALIDATED
```

RCIR v8.1 made genuine, measurable progress over v8 initial by introducing the dual-plane paradigm and recovering 423 previously lost dependencies. However, it did not satisfy the rigorous gates required for full Option A validation.

---

## 2. Gate-by-Gate Mechanical Audit

The frozen v8.1 benchmark contract defined the following primary gates for Option A:

| Gate | Required Threshold | Raw Primary Pipeline Measured | Raw R0 Ablation Measured | Status | Audit Finding |
|---|---|---|---|---|---|
| **Gate 1: Global CandidatePoolRecall** | $\ge 95.0\%$ | **97.23%** (701 / 721) | N/A (Plane A) | **PASSED (Micro)** | Passes globally, but Macro recall is 94.70%; TASK-2 is 89.13% and TASK-3 is 88.89%. |
| **Gate 1b: Silent Misses Limit** | $\le 15$ files | **20 files** | N/A (Plane A) | **FAILED** | 20 silent misses exceed the upper bound of 15. |
| **Gate 2a: Precision@20** | $\ge 35.0\%$ | **29.00%** | 46.00% | **FAILED** | Primary pipeline achieved only 29.00%. R0 was an ablation, not the primary pipeline. |
| **Gate 2b: Precision@50** | $\ge 20.0\%$ | **18.40%** | 34.00% | **FAILED** | Primary pipeline achieved only 18.40%, failing the $\ge 20.0\%$ contract floor. |
| **Gate 2c: Graded nDCG@50** | $\ge 0.5000$ | **0.3718** | 0.4972 | **FAILED** | Primary pipeline achieved 0.3718. Even R0 reached only 0.4972. |
| **Gate 2d: Mean Reciprocal Rank** | $\ge 0.7000$ | **0.6667** | 0.6733 | **FAILED** | Neither primary pipeline nor R0 reached the 0.70 threshold. |
| **Gate 3: CriticalRecall@Budget** | $\ge 60.0\%$ | **32.18%** | Not compiled | **FAILED** | Only 32.18% of Tier 2 and Tier 3 critical dependencies entered prompt budget. |
| **Gate 4: Context Compiler Budget** | $\le 4,000$ tokens | **3,939 to 3,986 tokens** | Same | **PASSED** | Deterministic span compilation adhered strictly to the token budget. |
| **Gate 5: Agent E2E Verification** | Live verified diffs | **Simulated / Dry-run** | None | **FAILED** | Artifact `agent_ab_test.json` contained hardcoded constants; `agent_turn_budget.json` recorded 0 tool calls. |

---

## 3. Discrepancy & Integrity Analysis (Rule 0 Audit)

### 3.1 Substitution of Ablation (R0) for Primary Pipeline (R5)
The primary dual-plane pipeline (`run_dual_plane_benchmark.py`) compiled context and reported primary metrics using the full feature set (`R5`). However, the v8.1 markdown reports cited the `R0` numbers (identity and direct structural relationships only) to claim that Gate 2 passed:
- `results/dual_plane_v8_1.json` reports primary Precision@20 = 0.2900, Precision@50 = 0.1840, nDCG@50 = 0.3718.
- `reports/final_assessment.md` claimed "MEASURED: 46.00% Precision@20, 34.00% Precision@50 (R0) [PASSED]".
Validating a system using an ablation while running a different configuration violates scientific consistency.

### 3.2 Feature Degradation Inversion
In `results/ranker_ablations.json`, ranking performance monotonically degraded as features were added:
- $R_0$ (Identity + Direct): P@20 = 46.0%, P@50 = 34.0%, nDCG@50 = 0.4972
- $R_1$ (+ Traversal): P@20 = 45.0%, P@50 = 34.0%, nDCG@50 = 0.4960
- $R_2$ (+ Type Compatibility): P@20 = 43.0%, P@50 = 33.6%, nDCG@50 = 0.4819
- $R_3$ (+ Change Compatibility): P@20 = 40.0%, P@50 = 24.8%, nDCG@50 = 0.4014
- $R_4$ (+ BM25 Lexical): P@20 = 40.0%, P@50 = 24.8%, nDCG@50 = 0.4014
- $R_5$ (+ Test & Module Penalties): P@20 = 29.0%, P@50 = 18.4%, nDCG@50 = 0.3718

Rather than treating this inversion as an empirical finding requiring weight refinement or architectural correction, the v8.1 reports ignored the degradation and claimed success.

### 3.3 Flawed BM25 Ablation
$R_3$ and $R_4$ produced identical results (P@20=0.40, P@50=0.248, nDCG=0.4014) because disabling BM25 did not zero lexical evidence in the ablation runner. This rendered the BM25 ablation invalid.

### 3.4 Report vs Raw Discrepancies in Context Precision
In `reports/context_plane_report.md`:
- TASK-1 Context Precision was stated as **75.00%**; raw JSON `dual_plane_v8_1.json` records **64.00%** (`0.64`).
- TASK-1 Token-Weighted Precision was stated as **76.20%**; raw JSON records **60.93%** (`0.6093`).
- TASK-2 Context Precision was stated as **21.43%**; raw JSON records **19.15%** (`0.1915`).
- TASK-3 Context Precision was stated as **38.46%**; raw JSON records **11.63%** (`0.1163`).

These discrepancies indicate that the markdown report was manually populated or computed from an uncommitted scratch run rather than derived from the committed JSON.

### 3.5 Simulated Agent Validation
In `results/agent_turn_budget.json`, all turn budgets recorded:
- `tool_calls: 0`
- `success: false`
- `gatekeeper_verdict: "REJECT"`
- `diff_length: 0`

Yet `reports/agent_turn_budget_report.md` claimed 100% gatekeeper approval at 10 and 20 turns with mean tool calls of 7.0 and 9.0. Furthermore, `results/agent_ab_test.json` was generated by writing static constants (`success_rate: 1.0`, `gatekeeper_verdicts: {"APPROVE": 5}`) without live agent execution.

### 3.6 Edge Evaluation Precision Hardcoding
In `results/edge_evaluation.json`, the evaluator recorded:
- `edge_precision_exact: 1.0`
- `edge_precision_inferred: 0.95`
These were hardcoded assumptions rather than adjudicated empirical precision against a closed-world prediction universe.

---

## 4. Contractual Contract Re-Evaluation

Applying the exact contractual logic from `experiments/rcir_v8_1/reports/benchmark_contract_v8_1.md`:

```text
IF:
    Plane A CandidatePoolRecall >= 95%            [97.23% micro: YES, but 20 misses > 15]
    AND Plane B Macro Precision@50 >= 20%        [18.40% on Primary Pipeline: NO]
    AND Plane B Macro nDCG@50 >= 0.50            [0.3718 on Primary Pipeline: NO]
    AND Context Compiler delivers real spans     [3,969 tokens bounded: YES]
    AND CriticalRecall@Budget >= 60%             [32.18%: NO]
    AND Agent E2E produces verified diffs        [Simulated: NO]
THEN:
    RECOMMENDATION = OPTION A — VALIDATED

ELSE IF:
    Plane A CandidatePoolRecall >= 90%            [97.23% micro, 94.70% macro: YES]
    AND Precision@50 materially improves > P0     [18.40% vs 5.20%: YES]
    AND Context Compiler operates deterministically [YES]
THEN:
    RECOMMENDATION = OPTION B — PARTIALLY VALIDATED

ELSE:
    RECOMMENDATION = OPTION C — REJECTED
```

The system unambiguously satisfies the **OPTION B — PARTIALLY VALIDATED** clause.

---

## 5. Architectural Mandate for RCIR v8.2

To progress from Option B to Option A, RCIR v8.2 must address the root causes:
1. **Machine-Enforced Decision Engine:** Never allow human markdown authors to manually designate Option A, B, or C. All decisions must be produced by a script reading raw JSON against a machine-readable schema.
2. **True Graph Degree Fanout:** Base fanout on the actual graph degree of seed entities for policy-relevant edges, not `len(target_entities)`.
3. **Rigorous Classification of All 20 Silent Misses:** Account for every single miss in a dedicated catalog.
4. **Operation-Conditioned and Cascaded Ranking:** Eliminate the feature inversion degradation by introducing semantic buckets (A0–A7), operation-specific profiles, and diversity-aware reranking.
5. **Real Type-Flow Intelligence:** Replace heuristics with a deterministic `TypeFlowIndex` for receiver resolution.
6. **AST-Based Context Extraction & Deduplication:** Use actual parser start/end line bounds and merge overlapping spans.
7. **Empirical Closed-World Edge Precision:** Scrutinize predicted edges against ground truth, or report `NOT_MEASURED` if false positives cannot be verified.
8. **Real Agent Execution:** Reject dry-run providers, simulated fallbacks, and empty diffs; evaluate agents on real code tasks with behavioral verification tests.
