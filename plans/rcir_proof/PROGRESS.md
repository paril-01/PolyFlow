# RCIR implementation progress

## Owner-authorized continuation

The owner has explicitly requested implementation of the complete master plan followed by pushing the changes. Publishing the scoped branch is now authorized; the earlier approval request below is historical. Required CI checkpoints will be published to this work branch, with no merge. No failed gate or unmeasured benchmark result is promoted to a pass. The first checkpoint publishes the existing PF-RP-01 repair and its prior provenance-fix parent for hosted verification. New CI receipts are saved under `experiments/runs/pf_rp_ci_20261126/`.

PHASE: PF-RP-00 baseline captured; PF-RP-01 local repair implemented; hosted CI/independent acceptance pending.

REPO/SHA/BRANCH/DIRTY: paril-01/PolyFlow @ 6a586e16007cb1bed123619b4494067f99eccf2f; work/pf-rp-01-proof-integrity; uncommitted scoped patch plus preserved user changes.

AUTHORIZATION: Owner's current request to evaluate then implement locally. [Exact ticket and ownership](./PF-RP-01.json).

FILES READ / EVIDENCE TABLE / PLAN / CHANGES / RISKS / PROHIBITED ACTIONS: [complete baseline and closeout](./BASELINE.md).

Implemented proof delivery with exact recorded digest, raw/delivery hash policies, all-branch path checks and explicit availability; removed static validated health; isolated mutating historical tests; repaired Windows command argv quoting; corrected the stale derived assessment while archiving its previous bytes; added Windows/Linux CI coverage and target checkout.

## Observed execution

These are separate checks, not summed into a benchmark score. Exact executable argv and all failed attempts are in [commands.jsonl](../../experiments/runs/pf_rp_01_20261126T014922/commands.jsonl).

| Check | Exit | Actual outcome | Log |
|---|---:|---|---|
| provenance-baseline | 0 | PASSED | [provenance-baseline.log](../../experiments/runs/pf_rp_01_20261126T014922/provenance-baseline.log) |
| linux-object-provenance | 0 | PASSED | [linux-object-provenance.log](../../experiments/runs/pf_rp_01_20261126T014922/linux-object-provenance.log) |
| proof-final | 0 | 52 passed, 2 skipped in 6.90s | [proof-final.log](../../experiments/runs/pf_rp_01_20261126T014922/proof-final.log) |
| linux-proof-smoke-fixed | 0 | PASSED | [linux-proof-smoke-fixed.log](../../experiments/runs/pf_rp_01_20261126T014922/linux-proof-smoke-fixed.log) |
| integrity-after | 0 | 37 passed in 191.73s (0:03:11) | [integrity-after.log](../../experiments/runs/pf_rp_01_20261126T014922/integrity-after.log) |
| historical-gates-isolated | 0 | 4 passed in 4.41s | [historical-gates-isolated.log](../../experiments/runs/pf_rp_01_20261126T014922/historical-gates-isolated.log) |
| stages-final | 0 | 79 passed in 70.74s (0:01:10) | [stages-final.log](../../experiments/runs/pf_rp_01_20261126T014922/stages-final.log) |
| core-ci-final | 0 | 30 passed in 4.82s | [core-ci-final.log](../../experiments/runs/pf_rp_01_20261126T014922/core-ci-final.log) |
| reports-after | 0 | PASSED | [reports-after.log](../../experiments/runs/pf_rp_01_20261126T014922/reports-after.log) |
| core-after | 1 | 1 failed, 27 passed in 5.89s | [core-after.log](../../experiments/runs/pf_rp_01_20261126T014922/core-after.log) |

COMMANDS / TESTS:

- `provenance-baseline`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" experiments/rcir_v8_5/scripts/validate_ground_truth_provenance.py`; exit `0`; log linked above.
- `linux-object-provenance`: `wsl -d Ubuntu --exec /usr/bin/python3 -u "/mnt/c/Users/Paril Rupani/OneDrive - Shri Vile Parle Kelavani Mandal/Desktop/project/PolyFlow/experiments/runs/pf_rp_01_20261126T014922/linux_object_provenance.py"`; exit `0`; log linked above.
- `proof-final`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/test_backend_proof_server.py tests/test_evidence_registry.py -q`; exit `0`; log linked above.
- `linux-proof-smoke-fixed`: `wsl -d Ubuntu --exec /usr/bin/python3 "/mnt/c/Users/Paril Rupani/OneDrive - Shri Vile Parle Kelavani Mandal/Desktop/project/PolyFlow/experiments/runs/pf_rp_01_20261126T014922/linux_proof_smoke.py"`; exit `0`; log linked above.
- `integrity-after`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/benchmark_integrity/ -q`; exit `0`; log linked above.
- `historical-gates-isolated`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/benchmark_integrity/test_historical_provenance_gate.py -q`; exit `0`; log linked above.
- `stages-final`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/test_stage1_core_correctness.py tests/test_stage2_submodules.py tests/test_stage3_ranking.py tests/test_stage4_agent_wiring.py tests/test_stage5_contract_and_gates.py tests/test_stage6_provenance_binding.py tests/test_stage7_contract_feasibility.py tests/test_stage8_report_truthfulness.py tests/test_stage9_discovery_no_answer_injection.py tests/test_stage10_retrieval_execution.py tests/test_stage11_run_lifecycle.py tests/test_stage12_agent_evidence.py tests/test_stage13_generalization_truthfulness.py tests/test_stage14_report_run_consistency.py tests/test_agent_loop.py tests/test_repo_tools.py -q`; exit `0`; log linked above.
- `core-ci-final`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/test_polyflow.py tests/test_feature_closure.py tests/test_ui_claims.py tests/test_final_claim_consistency.py tests/test_rcir_c0_mcp_and_bundle.py tests/test_stage8_report_truthfulness.py tests/test_stage14_report_run_consistency.py -q`; exit `0`; log linked above.
- `reports-after`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" experiments/rcir_v8_5/scripts/validate_report_consistency.py`; exit `0`; log linked above.
- `core-after`: `"C:/Users/Paril Rupani/AppData/Local/Programs/Python/Python312/python.exe" -m pytest tests/test_polyflow.py tests/test_feature_closure.py tests/test_ui_claims.py tests/test_final_claim_consistency.py tests/test_rcir_c0_mcp_and_bundle.py experiments/architecture_trials/v3/tests/test_adversarial_properties.py -q`; exit `1`; log linked above.

The Linux proof check validates all 18 frozen Git-blob proofs plus six negative controls, including real Linux symlinks. Windows proof tests skip two symlink cases because this host denies creation; Linux checks cover both. Linux source-object validation does not certify worktree cleanliness. The initial full Linux validator was deliberately stopped with exit 15 after 305 seconds in an NTFS git-status census; its failed receipt is retained.

The report-consistency pass proves agreement with stored inputs. The corrected report says INVALID because that is the saved historical gate input, not because a fresh live benchmark was run. [Previous report bytes](../../experiments/runs/pf_rp_01_20261126T014922/superseded-final_assessment.md) are preserved. Two files overwritten by pre-existing tests were archived as test-generated outputs and restored; final raw-result/manifest Git checks pass.

GATE STATUS: PF-RP-01 remains INCOMPLETE pending four hosted workflows and independent review. Existing R2 invalidation test still fails (core-after log). No architecture winner, live task success, token saving, cost reduction or native IDE credit saving is claimed.

NOT_RUN: fresh live paired/locked benchmarks; native MCP IDE A/B study; paid provider calls; clean independent package install; React build in this session; full supported Python-version matrix. Provider/generalization smoke scripts that overwrite historical results were not run directly. No GitHub workflow was launched on this uncommitted patch.

NEXT ACTION: review [scoped source patch](../../experiments/runs/pf_rp_01_20261126T014922/scoped.patch), then approve publishing the branch and a draft PR for hosted CI without merge. The branch also contains the prior committed provenance fix. [Dependency-ordered backlog](./BACKLOG.json) prepares PF-RP-02; it has not started.
