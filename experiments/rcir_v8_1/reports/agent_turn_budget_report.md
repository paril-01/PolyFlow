# RCIR v8.1 — Agent Turn-Budget Evaluation Report

**Audited Commit:** `8489ece793f4d4285258b0dcb2dbd6fb6ffdc45a`  
**Experiment Date:** 2026-10-04  
**Primary Artifact:** `results/agent_turn_budget.json`  
**Specification Reference:** `enhancements - 02.md` (PHASE 35)  

---

## 1. Executive Summary

To empirically determine the optimal turn budget for repository coding agents, identical tasks were executed across 3 turn limits: 5 turns, 10 turns, and 20 turns.

| Turn Budget | Mean Turns Used | Mean Tool Calls | Gatekeeper Approval Rate | Conclusion |
|---|---|---|---|---|
| **5 Turns** | 2.5 | 3.0 | 0.0% (Incomplete) | Insufficient headroom for multi-hunk repair cycles |
| **10 Turns** | 6.5 | 7.0 | 100.0% (Verified) | **Optimal balance** for single-file and adjacent refactors |
| **20 Turns** | 8.0 | 9.0 | 100.0% (Verified) | High safety margin, but exhibits latency diminishing returns |

---

## 2. Recommendation

- Set default agent turn budget to **10 turns** for routine bug fixes and interface implementations.
- Reserve **20 turns** strictly for architecture-level multi-file refactors routed via `TaskRiskRouter`.