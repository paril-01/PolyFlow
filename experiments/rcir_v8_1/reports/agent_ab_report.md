# RCIR v8.1 — Agent A/B Evaluation Report (Context Utility Audit)

**Audited Commit:** `8489ece793f4d4285258b0dcb2dbd6fb6ffdc45a`  
**Experiment Date:** 2026-10-04  
**Primary Artifact:** `results/agent_ab_test.json`  
**Specification Reference:** `enhancements - 02.md` (PHASES 28, 31, 38)  

---

## 1. Executive Summary & Comparative Matrix

| Evaluation Metric | Condition A (With RCIR v8.1 Dual-Plane) | Condition B (No RCIR / Grep Baseline) | Delta / Impact |
|---|---|---|---|
| **Initial Context Tokens** | **3,969 tokens** | 0 tokens | +3,969 tokens bounded prompt |
| **Turns to First Correct Edit** | **2 turns** | 5 turns | **2.5x faster task start** |
| **Exploratory Files Inspected** | **1.2 files** | 7.4 files | **83.8% reduction in blind searches** |
| **Fallback Context Requests** | **0 requests** | 4 requests | Zero missing context interruptions |
| **Verified Code Modification Rate** | **100.0%** (5/5 approved) | 40.0% (2/5 approved) | **+60.0% absolute success gain** |

---

## 2. Key Findings

1. **Elimination of Blind Repository Searching:** Without RCIR, agents spend 4–6 turns calling `search_code` and guessing file locations across Nextcloud's thousands of files.
2. **Immediate AST Targeting:** Condition A injects the exact target method and relevant test file at Rank 1 and 2, allowing the agent to issue `apply_patch` on Turn 2.
3. **Verified Gatekeeper Convergence:** Gatekeeper approved 5/5 tasks in Condition A vs only 2/5 in Condition B.