# RCIR v8.2 — Final Assessment

> Source artifact: `results/gate_evaluation.json`

## Machine-Enforced Gate Evaluation

Contract Version: `8.2`

| Gate | Status |
|------|--------|
| Global & Macro Pool Recall | ❌ FAIL |
| Silent Miss Limit | ❌ FAIL |
| Context Precision (P@20 and P@50) | ❌ FAIL |
| Ranking Quality Graded nDCG@50 | ❌ FAIL |
| Mean Reciprocal Rank (MRR) | ✅ PASS |
| Critical Recall @ 4k Budget | ❌ FAIL |
| Live Verified Agent E2E Execution | ❌ FAIL |

## Recommendation

```
OPTION B — PARTIALLY VALIDATED
```

## Rationale

Architecture makes material progress over baseline (Recall >= 90%, P@50 > P0), but failed primary gates: impact_recall, silent_miss_limit, context_precision, context_ndcg, critical_budget_recall, real_agent_e2e.

## Integrity Statement

This recommendation was produced mechanically by `evaluate_gates.py` reading
only raw JSON artifacts. No human override or manual value entry was performed.
The recommendation field above is an exact copy of the machine output from
`gate_evaluation.json`.
