# PolyFlow & RCIR Pre-Fix Audit Facts: Commit ea221b9

**Audit Date**: 2026-10-10  
**Evaluator Policy**: Rule 0 (Observation Before Claim) — Zero emojis, zero synthetic passes, fail-closed on missing evidence.  
**PolyFlow Commit**: `ea221b91890047d101ebd5a6f8f3a4c2457faeb2`  

---

## 1. Verified System Baseline & Environment

| Component | Verified Fact | Verification Command / Evidence |
| :--- | :--- | :--- |
| **PolyFlow Head Commit** | `ea221b91890047d101ebd5a6f8f3a4c2457faeb2` | `git rev-parse HEAD` |
| **Target Repository** | `experiments/nextcloud_validation/nextcloud-server` | Path verified; isolated submodule / directory |
| **Target Git SHA** | `da57df078d0808a7235a0177bd99d23c010b472e` | Verified via `git rev-parse HEAD` in target repo |
| **RCIR Target Graph** | `experiments/nextcloud_validation/rcir/nextcloud_graph.json` | 68,095 nodes, 212,176 edges, SHA-256: `d05dfe4cf2f1c834a34bba74151a66eec4e107297e68fa7d10e6a8f152d5b62b` |
| **Python Environment** | Python 3.12.3 (CPython, win32) | `python -V` |
| **PHP Runtime** | PHP 8.3.33 (CLI) | `php -v` |
| **Composer Runtime** | **NOT INSTALLED** on host PATH | `Get-Command composer` -> Not found. Upstream L3 tests requiring composer autoloading must fail closed (`SETUP_ERROR` / `L3_NOT_MEASURED`). |
| **Ollama Service** | Active & running locally | `ollama list` -> `qwen2.5-coder:1.5b` (986 MB), `qwen2.5:0.5b` (397 MB) |
| **Test Suite Baseline** | 212 passed, 3 failed (215 total) | `pytest -q` -> 3 failures due to command sandbox blocking `python -c` in `test_agent_loop.py` and `test_repo_tools.py`, plus Go runtime timeout in `test_polyflow_runtime_real.py`. |

---

## 2. Catalog of Audited Flaws and Blockers (P0-01 to P2-04)

### Priority 0: Critical Blockers

1. **P0-01 (`GraphEntitySourceResolver` missing)**:
   - *Observation*: `LiveRCIRContextProvider` in `rcir/context/provider.py` used heuristic string replacement (`canonical_target.split("::")[0].replace("php://", "")`) to determine file paths. For PHP namespace entities like `php://OCP\Files\Node::getId`, this yielded `OCP\Files\Node`, which does not exist on disk.
   - *Consequence*: The context compiler failed to open the file and fell back to empty/synthetic stubs, delivering zero real code lines to the agent.
2. **P0-02 (`entity_match="exact"` overclaim)**:
   - *Observation*: Entities were marked `exact` without verifying that the symbol or method existed at the target location in the graph node.
3. **P0-03 (Zero source-backed spans delivered to agent)**:
   - *Observation*: Because file resolution failed, context entries had empty `code_snippet` fields or failed silent fallbacks.
4. **P0-04 (Target commit SHA drift / isolation mismatch)**:
   - *Observation*: `WorktreeManager` checked `PINNED_NEXTCLOUD_COMMIT` against a default constant rather than enforcing the explicit CLI `--target-sha` across all worktree instantiations.
5. **P0-05 (Negative control L0 false-pass on pristine worktree)**:
   - *Observation*: `evaluator.py` treated any non-zero exit code as a defect confirmation. If a verification script crashed with `ModuleNotFoundError` or syntax error, it was counted as passing L0.
6. **P0-06 (L3 regression masquerading as syntax check)**:
   - *Observation*: `verify_regression.py` only ran `php -l` over modified files and exited 0. `evaluator.py` then marked `L3 PASS`, overclaiming that regression tests were executed.
7. **P0-07 (Missing CLI flags & unhandled verify-only in `run_benchmark.py`)**:
   - *Observation*: Flags `--oracle-dir` and `--task-id` were missing from `run_benchmark.py`. `--verify-only` did not support isolated single-task execution.
8. **P0-08 (Lack of physical separation between public tasks and private oracles)**:
   - *Observation*: Both public task prompts and private evaluator scripts were colocated in `test_design.json`, violating double-blind benchmark isolation.
9. **P0-09 (Ollama prompt formatting & tool calling parse fragility)**:
   - *Observation*: Tool responses with nested markdown JSON code blocks were occasionally misparsed, causing premature trial aborts.

### Priority 1: High Severity Deficiencies

1. **P1-01**: `LiveRCIRContextProvider` state bleeding across trials if reused without full reinitialization.
2. **P1-02**: Token budget estimation did not account for prompt template framing overhead.
3. **P1-03**: Sandboxed `run_command` in `orchestrator/tools.py` blocked safe testing invocations (`python -c` in unit tests) while failing to restrict arbitrary command execution.
4. **P1-04**: Git modification census only inspected `git diff --name-only`, missing newly added/untracked files.
5. **P1-05**: Run ID collisions when executed within the same second; lack of UUID suffix.
6. **P1-06**: Incomplete trial telemetry: missing `retrieval_trace.json` and raw model responses.
7. **P1-07**: Backend proof server returning demo data instead of 404 when requested run ID does not exist.
8. **P1-08**: Missing cryptographic SHA-256 verification in proof downloads.
9. **P1-09**: Visualizer tabs falling back to mock presets when backend is offline.
10. **P1-10**: Interpreter runtime conflating mock demonstrations with real `PolyCellRuntime` executions.
11. **P1-11**: Metrics computation calculating cost reduction across mismatched trial pairs or timeout trials.
12. **P1-12**: Agent Gate reporting satisfied when only 3 of 10 pairs were valid.
13. **P1-13**: Upstream PHPUnit execution not attempted or properly skipped when Composer is absent.
14. **P1-14**: Lack of structured failure taxonomy in benchmark summaries.
15. **P1-15**: Missing concordance table for paired baseline vs RCIR trials.

### Priority 2: UI & Provenance Deficiencies

1. **P2-01**: Visualizer Tab 05 lacking DocType-to-feature coverage ledger details.
2. **P2-02**: Documentation referring to stale hashes and outdated metrics.
3. **P2-03**: `revert_changes` tool risking modification outside disposable worktrees.
4. **P2-04**: Missing reproduction documentation for independent execution.

---

## 3. Plan for Rectification

All findings above are being remediated systematically across Checkpoints G1 through G12, validated by tests T01 through T42, and sealed in `reports/EA221B9_POST_FIX_CHANGELOG.md` and `reports/EA221B9_BENCHMARK_STATUS.md`.
