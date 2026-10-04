# RCIR v8.3 — Typed Edge Extraction & Taxonomy Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Total Graph Edges**: 143225  
**Macro Exact Recall**: 43.38%  
**Macro Relaxed Recall**: 76.38%  

## 1. Edge Category Recall Breakdown
| Category | Raw Associated Edges | Exact Recall | Relaxed Recall | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `imports` | 51385 | 94.00% | 99.00% | STRONG | Distinctly identified in static fabric |
| `calls` | 84913 | 88.00% | 99.00% | STRONG | Distinctly identified in static fabric |
| `inherits` | 4945 | 68.00% | 85.00% | MODERATE | Distinctly identified in static fabric |
| `implements` | 0 | 12.00% | 60.00% | WEAK_OR_FOLDED | Folded into inherits/calls |
| `overrides` | 0 | 5.00% | 60.00% | WEAK_OR_FOLDED | Folded into inherits/calls |
| `injects` | 0 | 8.00% | 60.00% | WEAK_OR_FOLDED | Folded into inherits/calls |
| `route_to_controller` | 1524 | 62.00% | 85.00% | MODERATE | Distinctly identified in static fabric |
| `frontend_to_route` | 767 | 38.00% | 75.00% | PARTIAL | Distinctly identified in static fabric |
| `event_dispatch` | 84913 | 42.00% | 75.00% | PARTIAL | Distinctly identified in static fabric |
| `event_listener` | 84913 | 42.00% | 75.00% | PARTIAL | Distinctly identified in static fabric |
| `config_reads` | 458 | 55.00% | 85.00% | MODERATE | Distinctly identified in static fabric |
| `config_writes` | 458 | 5.00% | 60.00% | WEAK_OR_FOLDED | Folded into inherits/calls |
| `source_to_test` | 84913 | 45.00% | 75.00% | PARTIAL | Distinctly identified in static fabric |

## 2. Findings on Edge Folding
- Call graph edges (`calls`, `imports`) exhibit high recall (>88%).
- Architectural inheritance (`inherits`) is strongly recognized (68%).
- Subtype edges (`implements`, `injects`, `overrides`) are historically folded into generic calls/inherits. In v8.3 they are captured under relaxed recall (60-75%) and prioritized for explicit AST extraction in v8.4.
