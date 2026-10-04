# RCIR v8.3 — PHP Type-Flow Receiver Resolution Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Analyzed Call Sites**: 635 across core controllers and node systems  
**Receiver Coverage**: 19.84%  
**Precision Among Resolved**: 78.57%  

## 1. Confidence Breakdown
- **Proven Exact**: 99 (15.6%)
- **Interface Bound**: 0 (0.0%)
- **Heuristic Inferred**: 27 (4.3%)
- **Explicitly Ambiguous**: 497 (78.3%)
- **Unknown / Dynamic**: 12 (1.9%)

## 2. Prevention of False Exacts
In accordance with Rule 21 and Phase 27, unresolved or ambiguous calls (e.g. `$node->getId()` where `$node` could refer to multiple class types) are classified as `AMBIGUOUS` rather than emitting false exact edges. This preserves high precision among proven receivers.
