# RCIR v8.5 — Typed Edge Evaluation Report

## Methodology
The edge evaluator performs strict exact canonical endpoint equality between graph edges and ground truth edges across:
- `implements`, `inherits`, `calls`, `route_to_controller`, `event_listener`, `injects`, `source_to_test`.

## Evaluation Results
- **Ground Truth Positive Edges**: `22`
- **Hard Negative Edges**: `3`
- **Exact Canonical Recall**: `31.8%`
- **Relaxed File-Pair Recall**: `63.6%`
- **Hard Negative Rejection Rate**: `100.0%`
- **Precision**: `NOT_MEASURED` (in accordance with Phase 85).

## Formal Gate Status
In strict adherence to **Phase 85**, the edge gate is marked **ADVISORY_ONLY**. Edge evaluation requires exhaustive edge extraction adjudication before being promoted to a blocking gate.
