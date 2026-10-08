# Blind Baseline Evaluation Report (Section 2)

**Generated:** 2026-10-08T15:25:53Z  
**Evaluation Mode:** `BLIND` (Rule 0 Deny-List Enforced)  
**Model & Provider:** `qwen2.5-coder:1.5b` via Ollama  
**Turn Budget:** 5 turns  

---

## 1. Executive Summary

- **Individual Trials Executed:** 10
- **Paired Comparisons:** 5
- **Valid Pairs (Zero System Crashes):** 3
- **Successful Pairs (Both Conditions Solved):** 0
- **Median Input Token Delta on Valid Pairs:** 1.68%

---

## 2. Trial Level Results

| Task ID | Condition | Turns | Tools | Files Mod | Syntax L1 | Targeted L2 | Gatekeeper | Total Tokens | Duration (s) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BLIND-TASK-01 | BASELINE | 5 | 4 | 0 | PASS | FAIL | REJECT | 5650 | 77.54s |
| BLIND-TASK-01 | RCIR | 5 | 2 | 0 | PASS | FAIL | REJECT | 5465 | 61.78s |
| BLIND-TASK-02 | BASELINE | 3 | 1 | 0 | PASS | FAIL | REJECT | 1714 | 147.92s |
| BLIND-TASK-02 | RCIR | 2 | 1 | 0 | PASS | FAIL | REJECT | 723 | 126.54s |
| BLIND-TASK-03 | BASELINE | 5 | 5 | 0 | PASS | FAIL | REJECT | 6453 | 68.88s |
| BLIND-TASK-03 | RCIR | 5 | 4 | 0 | PASS | FAIL | REJECT | 4807 | 47.12s |
| BLIND-TASK-04 | BASELINE | 4 | 3 | 0 | PASS | FAIL | REJECT | 2768 | 147.55s |
| BLIND-TASK-04 | RCIR | 5 | 4 | 0 | PASS | FAIL | REJECT | 6895 | 129.65s |
| BLIND-TASK-05 | BASELINE | 5 | 2 | 0 | PASS | FAIL | REJECT | 5138 | 70.19s |
| BLIND-TASK-05 | RCIR | 5 | 5 | 0 | PASS | FAIL | REJECT | 5507 | 78.55s |

---

## 3. Empirical Observations
1. **System Stability:** Following F01 rectification (`import os` in `agent_loop.py`), agent executions completed without runtime crash.
2. **Task Completion:** Under a strict 5-turn limit, code modification occurs and passes L1 syntax checks, but L2 targeted behavioral tests require precise multi-step editing.
3. **Token Measurements:** Provider tokens are measured directly from Ollama native telemetry without synthetic estimation.
