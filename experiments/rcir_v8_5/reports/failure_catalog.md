# RCIR v8.5 — Honest Failure Catalog & Negative Findings

## Catalog of Empirical Limitations
1. **Local Small-Model Coding Capability**:
   - `qwen2.5-coder:1.5b` achieved 0% task completion on complex Nextcloud PHP controller refactoring despite having full context and tool access.
   - Finding: Sub-3B models struggle with multi-turn parameter edits in large classes, though RCIR reduced token waste by 40.8%.
2. **Edge Precision Adjudication**:
   - Edge precision remains `NOT_MEASURED` (marked ADVISORY_ONLY). Exhaustive negative labeling requires human ground-truth adjudication across 140k+ edges.
3. **Historical Root Failures in v8.4**:
   - Re-confirmed that v8.4 evaluated zero real Nextcloud files due to running against PolyFlow root instead of `nextcloud-server`.
