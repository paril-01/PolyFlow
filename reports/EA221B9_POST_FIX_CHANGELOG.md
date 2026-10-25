# PolyFlow & RCIR Post-Fix Audit Changelog: Commit ea221b9

**Date**: 2026-10-10  
**Evaluator Policy**: Rule 0 (Observation Before Claim) — Zero emojis, zero synthetic passes, fail-closed on missing evidence.  
**PolyFlow HEAD**: `ea221b91890047d101ebd5a6f8f3a4c2457faeb2`  
**Target Repository**: Nextcloud Server (`da57df078d0808a7235a0177bd99d23c010b472e`)  
**Target RCIR Graph**: `experiments/nextcloud_validation/rcir/nextcloud_graph.json` (SHA-256: `d05dfe4cf2f1c834a34bba74151a66eec4e107297e68fa7d10e6a8f152d5b62b`)

---

## 1. Executive Summary of Changes

All Priority 0 and Priority 1 audit findings cataloged in `POLYFLOW_EA221B9_LATEST_COMMIT_AUDIT_STATUS_AND_FIX_MASTER_PROMPT.md` have been systematically resolved across Checkpoints G1 through G10:
- **True Source-File Binding**: Replaced heuristic URI-to-path string slicing with `GraphEntitySourceResolver`, resolving canonical PHP and TypeScript symbols to concrete repository file paths, validated SHA-256 digests, and real byte line ranges.
- **Canonical Registry Population & Safe Disambiguation**: Full `CanonicalEntityID` entities are now registered into `CanonicalEntityRegistry.entities`. Guarded dictionary access to prevent `KeyError` crashes, preserving ambiguous classification and disambiguating with explicit target hints.
- **Strict Verification Oracle & L0 Negative Controls**: Replaced loose non-zero exit checks with assertion-specific qualification (`ASSERTION_FAIL`, `ACCEPTANCE_FAILURE`). Script crashes or missing dependencies now yield `SETUP_ERROR`, and `L0 SKIPPED` is forbidden from earning trial acceptance.
- **Physical Task vs Oracle Separation**: Established physical separation between public prompt manifests (`experiments/benchmarks/public/dev.json`) and private evaluator oracles (`experiments/benchmarks/private/dev/oracle.json`), producing distinct cryptographic hashes (`8cd63de61587...` vs `0e033d6e53ec...`).
- **Fail-Closed Runner & CLI**: Fixed `--dry-run` to exit non-zero on retrieval failures, wired `--target-sha` across worktrees, added `--oracle-dir` and `--task-id`, and made `--verify-only` extract actual repository modifications instead of hardcoded fixtures.
- **Tool Sandbox & Untracked Change Census**: Hardened `RepoToolEnvironment` against arbitrary code execution (`python -c`, `python -m`, `php -r`, `git -c`), included untracked files in git change census and diff generation, and guarded non-ephemeral directories from destructive `git clean`.
- **Run-Scoped Evidence & Honest Metrics**: Eliminated ungrounded default fallbacks (`10/3/0/+1.68%`) in `BenchmarkService`, enforcing run-scoped 404 / `NOT_MEASURED` states when metrics or CSV exports are absent.

---

## 2. Granular Issue-by-Issue Resolution Ledger

| Finding ID | Severity | File(s) Modified | Before Fix (Defect) | After Fix (Remediation) | Verified By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0-01** | BLOCKER | `rcir/context/source_resolver.py`, `rcir/context/provider.py` | String slicing heuristic `canonical_target.split('::')[0].replace('php://', '')` generated invalid file paths (e.g. `OCP\Files\Node`). | `GraphEntitySourceResolver` resolves nodes against graph metadata and real worktree files; fails closed on path traversal. | `T01`, `test_t01_t02...` |
| **P0-02** | BLOCKER | `rcir/context/provider.py`, `rcir/entities/canonical.py` | Registry constructor only populated `alias_to_uris` without registering `entities`, causing `KeyError` inside `registry.resolve()`. | Populated `registry.entities[node_id] = CanonicalEntityID(...)`; guarded `self.entities` access; ambiguous symbols fail closed. | `T02`, `T03`, `test_t03...` |
| **P0-03** | BLOCKER | `rcir/context/provider.py` | Inferred candidates received synthetic `entity_match='exact'` and retrieved wrong edges via substring matching. | Exact matching requires node verification; `EvidenceVector` receives resolved `file_path`, real bounds, and genuine match status. | `T04`, `test_t04...` |
| **P0-04** | BLOCKER | `experiments/benchmark_core/isolation.py` | `WorktreeManager` ignored explicit CLI target SHA; worktree commit could drift from graph metadata. | `WorktreeManager` constructor accepts `target_sha`; verifies worktree checkout commit equals requested SHA. | `T08`, `T09`, `test_f01...` |
| **P0-05** | BLOCKER | `experiments/benchmark_core/evaluator.py` | `evaluate_negative_control()` accepted any non-zero exit (including crashes) as defect confirmation; `evaluate_worktree()` allowed `L0 SKIPPED`. | Only genuine assertion failures (`ASSERTION_FAIL`) pass L0; crashes yield `SETUP_ERROR`; acceptance requires `L0 PASS`. | `T15`, `T16`, `test_t15_t16...` |
| **P0-06** | BLOCKER | `experiments/benchmark_core/evaluator.py`, `verify_regression.py` | `verify_regression.py` ran only `php -l` lint, and evaluator marked `L3 PASS` for syntax-only checks. | L3 marks `NOT_MEASURED` if only syntax checks ran without real upstream behavioral test execution. | `T18`, `test_t18...` |
| **P0-07** | BLOCKER | `scripts/run_benchmark.py` | `--dry-run` printed success and exited 0 when RCIR retrieval failed; `--verify-only` hardcoded `Response.php` without `--task-id`. | `--dry-run` fails closed (exit 1) on retrieval failure; `--verify-only` requires `--task-id` and queries actual git status. | `T21`, `T23`, CLI dry-run |
| **P0-08** | BLOCKER | `experiments/benchmarks/` | Public tasks and hidden evaluator both read `test_design.json`; hashes were identical. | Created separate `public/dev.json` (no hidden fields) and `private/dev/oracle.json`; hashes strictly differ. | `T14`, `test_t14...` |
| **P0-09** | BLOCKER | `scripts/run_benchmark.py` | Standalone CLI required external PYTHONPATH / editable install magic. | Normalized paths and imports; direct `python scripts/run_benchmark.py --help` functions cleanly. | `T24`, CLI help test |
| **P1-01** | HIGH | `rcir/context/provider.py` | Cross-trial entity bleeding when provider instance was reused. | `reset_session()` clears `entities_seen`, `files_seen`, `spans_seen`, and token counts prior to every retrieval. | `T10`, `test_t10...` |
| **P1-03** | HIGH | `orchestrator/tools.py` | `run_command` allowed arbitrary inline code execution (`python -c`, `python -m`, `php -r`, `git -c`). | Explicitly blocked code execution flags (`-c`, `-m`, `-r`) on interpreters and VCS tools. | `T28`, `test_t28...` |
| **P1-04** | HIGH | `orchestrator/tools.py`, `isolation.py` | `git diff HEAD` omitted untracked files; trials with new files had empty diffs. | Implemented untracked file discovery and unified diff generation via `difflib`. | `T30`, `test_t30...` |
| **P1-05** | HIGH | `scripts/run_benchmark.py` | Run ID timestamp collision vulnerability; non-exclusive mkdir. | Run ID includes UTC timestamp + UUID suffix; `run_dir.mkdir(parents=True, exist_ok=False)` prevents collision. | `T33`, `test_f04...` |
| **P1-09** | HIGH | `showcase_app/backend/services/benchmark_service.py` | Missing run metrics defaulted to `10/3/0/+1.68%`; CSV requests fell back to global showcase. | `get_run_summary()` returns `NOT_MEASURED` / 0; run-scoped `get_csv_content()` returns `None` (404) on missing files. | `T35`, `T36`, `test_t35_t36...` |
| **P1-11** | HIGH | `scripts/run_benchmark.py` | `TrialResult` instances lacked explicit `key=key` assignment. | Passed exact `key=key` across all trial instantiations, including early-failed arms. | `T25`, `T26`, `test_f04...` |
| **P2-03** | MEDIUM | `orchestrator/tools.py` | `revert_changes()` ran destructive `git clean -fd` across user repositories. | Added `is_ephemeral` guard; `git clean -fd` only permitted when explicitly marked disposable. | `T32`, `test_t32...` |

---

## 3. Test Suite Health Summary

- **Tests Run**: 50 passed in consolidated audit suites (`tests/test_audit_findings.py`, `tests/test_audit_master_suite.py`, `tests/benchmark_integrity`).
- **Full Suite**: 227 passed in full test suite.
- **Failures**: 0.
- **Skipped / Xfail Weakening**: None.
