# RCIR v8.4 Typed Edge Recall & Precision Report

**Ground Truth Edge Tuples**: 15 verified Nextcloud architectural edges  
**Evaluated Against**: Canonical Graph built from `nextcloud_graph.json`  

## 1. Empirical Results
| Metric | Measured Score | Contract Floor | Status |
| :--- | :--- | :--- | :--- |
| **Exact Typed Edge Recall** | **86.67%** | 80.0% | **PASSED** |
| **Relaxed Edge Recall** | **86.67%** | 80.0% | **PASSED** |
| **Total Matches Found** | 13 / 15 | - | - |

## 2. Edge Type Mapping
Raw edge strings from extractors are mapped to strongly typed enum endpoints:
- `calls` -> `CanonicalEdgeType.CALLS`
- `imports` -> `CanonicalEdgeType.IMPORTS`
- `inherits` -> `CanonicalEdgeType.INHERITS`
- `route` -> `CanonicalEdgeType.ROUTE_TO_CONTROLLER`
- `config` -> `CanonicalEdgeType.CONFIG_READS`
- `source_to_test` -> `CanonicalEdgeType.SOURCE_TO_TEST`
