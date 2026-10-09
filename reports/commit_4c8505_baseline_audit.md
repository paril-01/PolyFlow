# PolyFlow: Commit `4c8505d` Forensic Baseline Audit Report

- **Audited HEAD Commit:** `4c8505d122f078b3e288551ea6c80c942d8521b5`
- **Parent / Previous Commit:** `b86acd511ffdee5b834a56e00ab8c1b87d66530a`
- **Audit Date:** 2026-10-09 (UTC)
- **Scope:** 51 changed files between `b86acd5` and `4c8505d` plus relevant call chains.

---

## 1. Executive Summary & Working-Tree State

The audit inspected the working tree directly at commit `4c8505d`. Commit `4c8505d` introduced the `experiments/benchmark_core/` package, Git worktree isolation routines, a pairer, an evaluator, typed models, and run-oriented backend APIs.

While these additions represent substantial structural progress over earlier commits, a deep forensic review confirms that **28 specific findings (F01–F28)** must be rectified to achieve an honest, reproducible, source-rooted benchmark under **Rule 0**:

- **RCIR Compiler Root (F01):** `LiveRCIRContextProvider` invokes its superclass with an unrooted `ContextCompiler()`, leaving `compiler._extract_snippet()` to fall back to reference stubs if `repo_root is None`.
- **RCIR Session Leakage (F03):** A single `LiveRCIRContextProvider` instance was reused across all trials, allowing `ContextSessionState.already_seen` to contaminate later trials.
- **Fail-Closed Retrieval (F02):** Retrieval exceptions in `scripts/run_benchmark.py` were trapped as warnings and allowed to run with empty context, falsely logging a valid RCIR trial.
- **Multi-Replicate Pairing (F04, F17):** Trials were grouped by `task_id` only, causing multi-replicate trials to overwrite each other. A true pair key must be `(task_id, target_sha, model, seed, turn_budget, replicate, experiment_version)`.
- **Budget Exhaustion vs Timeout (F05):** Hitting a 12-turn budget without edits was labeled a provider timeout instead of `TRIAL_BUDGET_EXHAUSTED`.
- **Quad-State Verifiers & Negative Controls (F06, F08):** Unrequested L3 regression checks set `l3_regression_passed=True` (boolean pass for skipped work), and no pre-edit L0 negative control verified that the unedited tree failed the targeted test.
- **Agent Command Sandboxing (F10):** `orchestrator/tools.py` executed model-supplied commands with `shell=True` and derived diffs from internal edit dictionaries rather than an independent `git diff HEAD`.
- **Run-Scoped REST APIs (F20):** Missing run IDs or missing metrics fell back to hardcoded default values (10 trials, 3 valid pairs, +1.68% delta) or global showcase CSVs.
- **Showcase Integrity (F14):** `scripts/build_showcase.py` only checked file existence rather than verifying SHA-256 digests before copying.

---

## 2. Baseline Test Status (Pre-Fix Verification)

```text
================================================================================
BASELINE TEST RUN AT COMMIT 4c8505d
================================================================================
Command: python -m pytest tests/benchmark_integrity -q
Result:  17 passed, 1 warning in 20.29s (PASS)

Command: python -m pytest tests/test_final_claim_consistency.py tests/test_backend_proof_server.py -q
Result:  14 passed, 1 warning in 11.81s (PASS)

Command: python scripts/run_benchmark.py --help
Result:  exited 0 with argument options listed (PASS)
================================================================================
```

---

## 3. Register of 28 Forensic Findings (F01 – F28)

| ID | Priority | Status | Source File | Exact Problem / Consequence |
|---|---|---|---|---|
| **F01** | P0 | CONFIRMED | `rcir/src/rcir/context/provider.py` | `LiveRCIRContextProvider` invokes `super().__init__(raw_graph=raw_graph)` without `ContextCompiler(repo_root=target_repo)`. `compiler._extract_snippet()` uses a reference-stub path if `repo_root is None`. Stub tokens could be counted as real RCIR context. |
| **F02** | P0 | CONFIRMED | `scripts/run_benchmark.py` | RCIR initialization and retrieval exceptions are logged as warnings; the trial continues with empty context and `context_provider=None`, misreporting an invalid trial as a valid RCIR arm. |
| **F03** | P0 | CONFIRMED | `rcir/src/rcir/context/provider.py` | One `LiveRCIRContextProvider` instance is reused across trials. `ContextSessionState` retains `already_seen` across tasks and replicates, altering context in later trials. |
| **F04** | P0 | CONFIRMED | `experiments/benchmark_core/pairer.py` | Pairs keyed by `task_id` only; multi-replicate trials overwrite one another. No exact model/commit/seed/budget matching. |
| **F05** | P0 | CONFIRMED | `benchmark_core/pairer.py`, `scripts/run_benchmark.py` | Hitting turn budget without edits is mislabeled `TRIAL_TIMEOUT_PROVIDER` instead of `TRIAL_BUDGET_EXHAUSTED`. |
| **F06** | P0 | CONFIRMED | `experiments/benchmark_core/evaluator.py` | If L3 is not requested, sets `l3_regression_passed=True` and logs `L3_OPTIONAL_SKIPPED`. A boolean PASS encodes skipped checks. |
| **F07** | P0 | CONFIRMED | `experiments/rcir_v8_5/agent_tasks/verify_regression.py` | Exit 0 currently means PHP syntax lint passed, not an upstream regression suite. Also falls back to scanning all PHP files on certain git-status outputs. |
| **F08** | P0 | CONFIRMED | `experiments/benchmark_core/evaluator.py` | No mandatory pre-edit negative control: targeted test must fail on original pinned revision before accepting a fix. Missing PHP binary, script timeouts, and exit codes lack fail-closed statuses. |
| **F09** | P0 | CONFIRMED | `experiments/benchmark_core/isolation.py` | `verify_target_checkout` returns current HEAD if pinned object merely exists in git ODB; actual worktree checks out pinned SHA. `RunManifest.target_sha` may therefore describe a different revision. |
| **F10** | P0 | CONFIRMED | `orchestrator/tools.py` | `run_command(..., shell=True)` runs model-originated commands with shell expansion. `get_git_diff()` depends on internal edit backups, not an independent git change census. |
| **F11** | P0 | CONFIRMED | `rcir/src/rcir/context/provider.py` | Task symbol extraction grabs first CamelCase-like word and registry starts empty; no verified canonical symbol->source path resolution. |
| **F12** | P0 | REQUIRES_CHECK | `scripts/run_benchmark.py` | Standalone script must run in clean venv without relying on `tests/conftest.py` sys.path modification. |
| **F13** | P1 | CONFIRMED | `scripts/run_final_benchmark.py` | 'Final benchmark' still only runs unit tests + showcase builders, then prints fixed historic gate outcomes. Never invokes `run_benchmark.py`. |
| **F14** | P1 | CONFIRMED | `scripts/build_showcase.py` | Header promises hash validation, but implementation only checks file existence and copies CSVs without validating SHA-256 digests. |
| **F15** | P1 | CONFIRMED | `scripts/run_benchmark.py` | `RunManifest` leaves dirty, index hash, oracle hash, and ranker config hash as defaults; `start_time_utc` is local `datetime.now()` without timezone. |
| **F16** | P1 | CONFIRMED | `scripts/run_benchmark.py` | No `try/finally` for worktree cleanup and no per-trial failure persistence until after runner completes. |
| **F17** | P1 | CONFIRMED | `benchmark_core/models.py`, `pairer.py` | `TrialKey` contains commit/model/seed/replicate but `TrialResult` does not carry a comparable tuple; `TrialKey.to_string()` omits model, seed, and target SHA. |
| **F18** | P1 | CONFIRMED | `benchmark_core/metrics.py` | Agent gate is satisfied by one both-successful pair; no minimum sample size, task difficulty, per-stratum coverage, confidence intervals, or clear distinction among efficiency estimands. |
| **F19** | P1 | CONFIRMED | `showcase_app/backend/services/rcir_service.py` | Nominal live retrieval creates artificial candidate scores (`1.0 - 0.08*idx`), assigns tiers by index, and silently falls back to a saved example query. |
| **F20** | P1 | CONFIRMED | `showcase_app/backend/services/benchmark_service.py`, `api/proofs.py` | A newly requested run receives hardcoded default stats when metrics are absent; per-run CSV endpoints fall back to global showcase CSVs; `/runs/{id}/proofs` returns global proof index. |
| **F21** | P1 | CONFIRMED | `.github/workflows/ci.yml`, `tests/benchmark_integrity/*` | CI lacks standalone entrypoint test, paired live execution, source-span provenance, and multi-replicate pairing tests. |
| **F22** | P2 | CONFIRMED | `showcase_app/backend/services/interpreter_service.py` | Parser is called, but 'DAG' counts sources + schemas without scheduling, and executed cells are hardcoded rather than taken from parsed `.poly` content. |
| **F23** | P2 | CONFIRMED | `showcase_app/backend/services/interpreter_service.py` | Failure of a tax-calculation cell is displayed as `DEGRADED` with a narrated fallback rather than independently executed recovery; durations have hardcoded minimums. |
| **F24** | P2 | CONFIRMED | `scripts/build_run_exports.py` | Legacy exporter retains parallel competing artifact paths that can mix historic with live evidence. |
| **F25** | P2 | CONFIRMED | `showcase_app/backend/api/health.py` | Health endpoint retains `evidence_status=VALIDATED` merely for process liveness. |
| **F26** | P1 | CONFIRMED | `benchmark_core/task_loader.py`, `evaluator.py` | Public manifest and private oracle are read from the same `test_design.json` path. Sanitizing prompt fields helps, but is not a physical isolation boundary. |
| **F27** | P1 | REQUIRES_CHECK | `rcir/src/rcir/context/provider.py` | Loaded graph has no required `target_commit/index_hash/extractor_version` assertion against the worktree. |
| **F28** | P1 | CONFIRMED | `orchestrator/agent_loop.py` | Normal run's `AgentLoopResult.success` requires `test_command`, but benchmark runner does not provide one and computes success independently. Split contract causes confusion. |

---

## 4. Remediation Plan

The remediation follows Phases A through H:
1. **Phase A:** Fix pinned target commit verification, clean per-trial worktrees with `try/finally` cleanup, and true physical separation of public tasks from private hidden oracles.
2. **Phase B:** Bind `ContextCompiler(repo_root=target_repo)` to eliminate stub contexts (F01), enforce graph revision invariants (F27), per-trial session isolation (F03), and fail-closed retrieval (F02).
3. **Phase C:** Implement exact 7-tuple pair keys `(task_id, target_sha, model, seed, turn_budget, replicate, experiment_version)` (F04, F17), distinct terminal states (`TRIAL_BUDGET_EXHAUSTED` vs `TRIAL_TIMEOUT_PROVIDER`), and separate valid-pair vs success-rate denominators.
4. **Phase D:** Enforce safe `shell=False` execution with argument allowlists and path traversal guards (F10), quad-state verifier (`PASS`, `FAIL`, `SKIPPED`, `NOT_MEASURED`, `SETUP_ERROR`), mandatory L0 negative control (F08), and independent Git diff censuses.
5. **Phase E:** Build a true benchmark CLI supporting `--dry-run`, `--verify-only`, `--target-sha`, etc.
6. **Phase F:** Enforce strict run-scoping on all `/api/runs/{run_id}` endpoints (F20), real ranker score extraction (F19), SHA-256 validation during showcase synchronization (F14), and distinct real-AST vs demonstration modes in the interpreter (F22–F23).
7. **Phase G:** Implement 36 adversarial regression tests and split CI into deterministic PR checks and optional live evaluations.
8. **Phase H:** Publish `reports/POLYFLOW_4C8505_RECTIFICATION_AND_RESULTS.md`.
