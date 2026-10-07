# RCIR v8.5 — Honest Failure Catalog & Negative Findings

## Catalog of Empirical Limitations
1. **Mathematically Impossible Ranking Thresholds**:
   - The contract specified P@20 >= 0.35 and P@50 >= 0.20 on the TEST split.
   - Ground truth analysis demonstrates that the mean number of relevant dependencies per task is only 2-4 items, producing theoretical metric ceilings of P@20 = 0.15 and P@50 = 0.06.
   - Result: Contract Feasibility Validator flagged the contract as **INVALID_CONTRACT**.
2. **Local Small-Model Coding Capability**:
   - `qwen2.5-coder:1.5b` achieved 0% task completion on complex Nextcloud PHP controller refactoring despite full context delivery.
   - Finding: Sub-3B models struggle with multi-turn parameter edits in large classes.
3. **Edge Precision Adjudication**:
   - Edge precision remains `NOT_MEASURED` (marked ADVISORY_ONLY). Exhaustive negative labeling requires human ground-truth adjudication across 140k+ edges.
4. **Benchmark Integrity Enforcement**:
   - Historical v8.5 runs permitted reused constant run IDs and dirty worktrees.
   - Under hardened v8.5.1 provenance rules, runs with mismatched artifact hashes or dirty git trees are strictly marked `INVALID`.
