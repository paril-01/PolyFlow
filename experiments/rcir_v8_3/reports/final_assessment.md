# RCIR v8.3 — Formal Final Assessment & Gatekeeper Decision

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Final Decision**: **OPTION B — PARTIALLY VALIDATED**  
**Contract Version**: `8.3` (`experiments/rcir_v8_3/contract/benchmark_contract.json`)

## 1. Executive Gate Decision
The RCIR v8.3 benchmark execution pipeline has completed all formal evaluations across the DEV, VALIDATION, and TEST splits.
Under the frozen benchmark contract:
- **OPTION A (Fully Validated)**: Failed because Macro Candidate Recall (70.56%) is below 95% and live agent completion rate was not fully exercised across 100 trials.
- **OPTION B (Partially Validated)**: **PASSED**.
  - Global Pool Recall: **93.20%** (Contract minimum: 90.00%) — **PASS**
  - Precision@50 Improvement over P0: **+34.53%** (Contract minimum: +15.00%) — **PASS**
  - Context Compiler Determinism: **TRUE** — **PASS**

## 2. Key Achievements in v8.3
1. **Rule 0 Leakage Guard**: Ground truth answer key completely removed from retrieval summarizer and compiler. 0 leakage violations.
2. **Canonical Graph Fabric**: 12,621 canonical entities and 143,225 typed edges normalized under `php://` and `ts://` schemes.
3. **Endpoint Disambiguation**: Resolved the `IConfig` degree anomaly (0 -> 1,470 incoming calls).
4. **Leakage-Free Ranker Selection**: Selected strictly using the VALIDATION dataset without touching the TEST dataset.
5. **Semantic Role Quota Context Planning**: Context compiled under 2k, 4k, and 8k token budgets.
