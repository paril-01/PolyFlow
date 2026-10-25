# PolyFlow & RCIR Benchmark Status: Commit ea221b9

**Date**: 2026-10-10  
**Evaluator Policy**: Rule 0 (Observation Before Claim) — Zero emojis, zero synthetic passes, fail-closed on missing evidence.  
**PolyFlow Commit**: `ea221b91890047d101ebd5a6f8f3a4c2457faeb2`  
**Target Repository**: Nextcloud Server (`da57df078d0808a7235a0177bd99d23c010b472e`)  

---

## 1. Truthful Status by Verification Tier

| Stage | Description | Measured Outcome | Evidence / Reason |
| :--- | :--- | :--- | :--- |
| **E0** | Unit, Integrity & Negative Control Tests | **PASS (100%)** | 50/50 audit tests pass (`test_audit_master_suite.py`, `test_audit_findings.py`, `benchmark_integrity`); 227/227 tests pass across repository. |
| **E1** | Live RCIR Target Retrieval | **PASS (VERIFIED)** | Real source spans extracted from pinned Nextcloud commit; 5,348 characters compiled for `BLIND-TASK-01` with zero stubs and verified line bounds. |
| **E2** | Multi-Task Retrieval Quality | **PASS (VERIFIED)** | All 5 blind validation tasks resolve real source entities; unambiguous symbols bind to disk; ambiguous symbols fail closed without target hint. |
| **E3** | Single Solvable A/B Task Trial | **NOT_MEASURED** | Upstream L3 Composer dependencies unavailable on host PATH (`composer` not found on PATH). Evaluator strictly marks L3 as `NOT_MEASURED`. |
| **E4** | 5 Diverse Tasks x 2 Replicates | **NOT_MEASURED** | Blocked by missing host Composer toolchain for full L3 behavioral regression. No synthetic scores injected. |
| **E5** | Held-Out Blind Evaluation | **FROZEN** | Public tasks (`experiments/benchmarks/public/dev.json`) and private oracle (`experiments/benchmarks/private/dev/oracle.json`) sealed with distinct hashes. |

---

## 2. Pinned Environment Telemetry

- **Python Runtime**: `Python 3.12.3` (CPython, win32)
- **PHP CLI**: `PHP 8.3.33` (cli)
- **Composer**: `NOT INSTALLED` on host PATH (`Get-Command composer` returns not found)
- **Ollama**: Active and accessible locally (`qwen2.5-coder:1.5b`, `qwen2.5:0.5b`)
- **Nextcloud Target SHA**: `da57df078d0808a7235a0177bd99d23c010b472e`
- **RCIR Graph Nodes**: 68,095 nodes, 212,176 edges (SHA-256: `d05dfe4cf2f1c834a34bba74151a66eec4e107297e68fa7d10e6a8f152d5b62b`)
- **Public Task Manifest SHA-256**: `8cd63de6158784d142ca138bebfcb655d8f993f350c3d9feaa2c60c7f3b89b4f`
- **Private Oracle Manifest SHA-256**: `0e033d6e53ec1a196728eb712dc86c52a353fe2d3258c704259b3d0b25e83ec9`

---

## 3. Mandatory Engineering Verdict

> **Implemented:** `GraphEntitySourceResolver`, `CanonicalEntityRegistry` full entity registration, quad-state `EvaluatorOracle` with strict L0 assertion checks, physical public task / private oracle separation, fail-closed `run_benchmark.py` CLI with `--oracle-dir` and `--task-id`, hardened `RepoToolEnvironment` sandbox with code-execution flag denial, untracked git diff census, run-scoped `BenchmarkService`.  
> **Verified on real tasks:** Real source retrieval on `BLIND-TASK-01` (`apps/appstore/lib/Controller/ApiController.php`), L0 negative control reproduction on pristine Nextcloud commit `da57df078d0808a7235a0177bd99d23c010b472e`.  
> **Context efficiency on successful tasks:** `NOT_MEASURED` (0 both-successful live coding task pairs on commit `ea221b9`).  
> **Next engineering milestone:** Install Composer on host PATH or run in an isolated Linux container with Composer to unlock full L3 PHPUnit behavioral test execution during live model agent trials.
