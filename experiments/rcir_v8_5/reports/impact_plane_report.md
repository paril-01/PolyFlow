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
| **DEV** | 6 | `92.5%` | `75.0%` | `2` | `4370` |
| **VALIDATION** | 5 | `86.7%` | `66.7%` | `2` | `901` |
| **TEST** | 5 | `100.0%` | `100.0%` | `0` | `945` |

## Impact Gate Compliance
- **Macro Pool Recall on TEST**: `100.0%` (Floor: 90.0%) -> **PASSED**
- **Worst Task Recall on TEST**: `100.0%` (Floor: 80.0%) -> **PASSED**
- **Silent Misses on TEST**: `0` (Ceiling: 20) -> **PASSED**
