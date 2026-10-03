# RCIR v8.2 — Edge Quality Report

> Source artifact: `results/edge_evaluation.json`

## Summary

| Metric | Value |
|--------|-------|
| Total Edges Evaluated | N/A |
| Exact Match | N/A |
| Inferred Match | N/A |
| Wrong Relation | N/A |
| No Match | N/A |
| Precision | NOT_MEASURED |

## Taxonomy Breakdown

| Category | Count | Exact | Inferred | Wrong Rel | No Match |
|----------|-------|-------|----------|-----------|----------|
| inherits | 0 | 0 | 0 | 0 | 0 |
| implements | 0 | 0 | 0 | 2 | 0 |
| imports | 0 | 0 | 0 | 0 | 0 |
| calls | 0 | 0 | 0 | 0 | 2 |
| injects | 0 | 0 | 0 | 2 | 0 |
| route_to_controller | 0 | 0 | 0 | 0 | 0 |
| frontend_to_route | 0 | 0 | 0 | 0 | 1 |
| event_dispatch | 0 | 0 | 0 | 0 | 1 |
| event_listener | 0 | 0 | 0 | 0 | 1 |
| config_reads | 0 | 0 | 0 | 0 | 1 |
| source_to_test | 0 | 0 | 0 | 0 | 2 |

## Notes

Edge precision is intentionally reported as `NOT_MEASURED` per Phase 38: the current
evaluation methodology cannot reliably count false positive edges across the full graph.
