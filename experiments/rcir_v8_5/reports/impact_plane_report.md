# RCIR v8.5 — Semantic Multi-Channel Impact Plane Report

## 7-Channel Impact Discovery Architecture
1. **Channel A**: Exact Graph (`calls`, `implements`, `inherits`, `overrides`, `injects`)
2. **Channel B**: Type Flow (receiver-resolved call sites, implementation owners)
3. **Channel C**: Boundary (`route_to_controller`, `frontend_to_route`)
4. **Channel D**: Events (`event_dispatch`, `event_listener`)
5. **Channel E**: Config / DI (`config_reads`, constructor injections)
6. **Channel F**: Verification (`source_to_test`, contract tests)
7. **Channel G**: Lexical Fallback (explicitly labeled, low confidence)

## Split-Level Performance
| Split | Total Tasks | Macro Pool Recall | Worst Task Recall | Silent Misses | Total Candidates |
|---|---|---|---|---|---|
| **DEV** | 6 | 85.8% | 60.0% | 4 | 4300 |
| **VALIDATION** | 5 | 66.7% | 33.3% | 5 | 742 |
| **TEST** | 5 | 84.3% | 66.7% | 3 | 728 |

## Impact Gate Compliance
- **Macro Pool Recall on TEST**: `84.3%` (Floor: 90.0%) -> **FAILED**
- **Worst Task Recall on TEST**: `66.7%` (Floor: 80.0%) -> **FAILED**
- **Silent Misses on TEST**: `3` (Ceiling: 20) -> **PASSED**
