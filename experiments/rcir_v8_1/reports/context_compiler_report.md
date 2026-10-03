# RCIR v8.1 — Context Compiler & Token Efficiency Report

**Audited Commit:** `8489ece793f4d4285258b0dcb2dbd6fb6ffdc45a`  
**Experiment Date:** 2026-10-04  
**Primary Artifact:** `results/dual_plane_v8_1.json`  
**Specification Reference:** `enhancements - 02.md` (PHASES 25, 26, 27)

---

## 1. Executive Summary & Problem Statement

In RCIR v8 initial, the context report claimed high "token-budgeted coverage" based simply on taking the top 20 files. Furthermore, the compiler extracted fixed line prefixes (first 120, 40, 35, or 25 lines of each file), which rarely contained the actual modified functions or call sites.

RCIR v8.1 eliminates this superficial heuristic:
1. **Entity-Aware Span Extraction (Phase 25):** Employs AST-located symbol boundaries (`_locate_entity_span`) to extract exact function declarations, class signatures, and route declarations rather than license headers.
2. **True Token-Budgeted Coverage (Phase 26):** Evaluates real intersection between `ContextCompiler.compile(token_budget=4000)` output and the independent graded ground truth.
3. **Multi-Granularity Synthesis:** Uses 6 distinct compilation granularities: `FULL_IMPLEMENTATION`, `ROUTE_DECLARATION`, `TEST_FRAGMENT`, `SIGNATURE`, `CALLER_SNIPPET`, and `SUMMARY`.

---

## 2. Quantitative Context Compilation Results

All figures derived directly from committed raw JSON in `results/dual_plane_v8_1.json`:

| Task ID | Domain | Budget Cap | Actual Compiled Tokens | Entries Included | Context Precision | CriticalRecall@Budget (Tiers 2 & 3) | Token-Weighted Precision |
|---|---|---|---|---|---|---|---|
| **TASK-1** | Controller Endpoint | 4,000 | 3,939 | 12 | **75.00%** | **75.00%** | **76.20%** |
| **TASK-2** | Node Contract | 4,000 | 3,972 | 14 | 21.43% | 5.56% | 22.10% |
| **TASK-3** | NodeDeletedEvent | 4,000 | 3,979 | 13 | **38.46%** | **45.45%** | **41.30%** |
| **TASK-4** | IConfig Resolution | 4,000 | 3,970 | 14 | 21.43% | 1.56% | 21.80% |
| **TASK-5** | Recent.ts Client | 4,000 | 3,986 | 11 | 18.18% | **33.33%** | 19.20% |
| **Macro Average** | — | **4,000** | **3,969** | **12.8** | **34.90%** | **32.18%** | **36.12%** |

---

## 3. Granularity Distribution & Span Efficiency

In a 4,000-token prompt payload, Context Compiler dynamically balances depth and breadth:

```text
Rank 1:       FULL_IMPLEMENTATION  (e.g., target controller method or event class, ~45 lines)
Ranks 2–4:    ROUTE_DECLARATION / TEST_FRAGMENT (e.g., direct route mapping or PHPUnit test method)
Ranks 5–8:    SIGNATURE            (e.g., interface definitions and caller signatures, ~15 lines)
Ranks 9+:     SUMMARY              (e.g., brief reference line for blast-radius awareness)
```

### Prompt Budget Adherence
- **Maximum observed token overshoot:** **0 tokens** (strictly capped at 4,000).
- **Average buffer utilization:** **99.23%** (3,969 / 4,000 tokens utilized, leaving ~31 tokens of headroom for agent instruction wrappers).
- **Zero Hallucination:** Code snippets are directly read from verified repository file paths.
