# RCIR v8.5 — End-to-End Reproduction Guide

## Prerequisites
- Python 3.10+
- Git
- Nextcloud Server submodule at `experiments/nextcloud_validation/nextcloud-server` (commit `da57df078d0808a7235a0177bd99d23c010b472e`)
- Ollama running locally at `http://127.0.0.1:11434` with `qwen2.5-coder:1.5b`

## Step-by-Step Reproduction Pipeline
```bash
# 1. Verify environment sentinels and git commit
python experiments/rcir_v8_5/scripts/environment.py

# 2. Reconstruct ground truth and manifests
python experiments/rcir_v8_5/scripts/reconstruct_ground_truth.py

# 3. Validate ground truth provenance against disk and git
python experiments/rcir_v8_5/scripts/validate_ground_truth_provenance.py

# 4. Evaluate canonical graph integrity and endpoints
python experiments/rcir_v8_5/scripts/evaluate_canonical_graph.py

# 5. Evaluate canonical entity resolution corpus
python experiments/rcir_v8_5/scripts/evaluate_canonicalization.py

# 6. Evaluate typed edges against hard negatives
python experiments/rcir_v8_5/scripts/evaluate_edges.py

# 7. Evaluate source-order PHP type-flow analyzer
python experiments/rcir_v8_5/scripts/evaluate_type_flow.py

# 8. Run 7-channel semantic discovery and validation-selected ranker
python experiments/rcir_v8_5/scripts/retrieval_runner.py

# 9. Compile context and evaluate saturation curve
python experiments/rcir_v8_5/scripts/context_runner.py

# 10. Run formal determinism evaluation (N=5 trials)
python experiments/rcir_v8_5/scripts/evaluate_determinism.py

# 11. Run live agent validation in isolated worktrees
python experiments/rcir_v8_5/scripts/run_agent_validation.py

# 12. Run performance and memory footprint benchmark
python experiments/rcir_v8_5/scripts/benchmark_performance.py

# 13. Evaluate generalization readiness matrix
python experiments/rcir_v8_5/scripts/evaluate_generalization.py

# 14. Execute formal contract gate evaluation
python experiments/rcir_v8_5/scripts/evaluate_gates.py

# 15. Generate all formal markdown reports
python experiments/rcir_v8_5/scripts/generate_reports.py

# 16. Validate report consistency and byte invariance
python experiments/rcir_v8_5/scripts/validate_report_consistency.py
```
