# PolyFlow / RCIR: Benchmark-First Correctness Recovery and Presentation Readiness

**Single comprehensive implementation prompt for AntiGravity IDE**  
**Review target:** `paril-01/PolyFlow`  
**Audited HEAD:** `b86acd511ffdee5b834a56e00ab8c1b87d66530a` (`benchmark flaws fix`)  
**Parent:** `cfe69e39275375763762cbb6ed94fab0bf5a3f9a`  
**Previous examined HEAD:** `3a29cebe9732f91c60d4dd78844d8a5d0039104e`  
**Task:** Audit and FIX the existing implementation. Produce a fresh, independent, reproducible benchmark that demonstrates real quality. Freeze verified results BEFORE doing any additional UI work. Then connect the existing minimal HTML/CSS/JS backend to those verified results. ERPNext source-preserving migration comes afterward.

## Instructions to the implementation agent

You are acting as a senior repository engineer, benchmark designer, independent evaluator, and adversarial reviewer. Work on the real source tree, not on screenshots, Markdown claims, exported dashboards, or a modified test oracle. Inspect this entire prompt before starting. Preserve real existing functionality; perform modifications as an incremental engineering program. Run commands and tests in a real checkout. Do not tell me that the benchmark improved without furnishing the raw trial evidence, exact revision, run command, environment, logs, and independently computed metrics. Do NOT end with an implementation plan alone: implement fixes, run all possible real tests, and record any unavailable test accurately. Do not ask for re-confirmation where the repository already contains the necessary source and target paths.

**Absolute anti-fabrication rule:** Never substitute handwritten numeric results, fixed CSV rows, mock API responses, fabricated patches, invented screenshots, preselected recall values, random “realistic” benchmark data, hardcoded return codes, cached trial restamping, or constant `VALIDATED` flags for observed behavior. No test may assert that a benchmark achieves a particular historically observed value. If a result is poor, keep it; fix the system and re-run. If a service/model/toolchain is unavailable, emit `NOT_MEASURED` or `INVALID_SETUP` rather than PASS. Do not retune the hidden TEST set or change the oracle to get a desired score.

**Dependency order:** (A) evidence integrity and harness, (B) real RCIR retrieval and tools, (C) viable agent edits / tests, (D) retrieval quality and token efficiency, (E) clean independent release benchmark, (F) API/proof/UI wiring, (G) ERPNext structural and behavioral parity.

---

# 1. Current reality: findings grounded in the latest commit

These are the specific reasons not to accept the present report at face value. Fix the source, not the wording alone.

## P0-01 — “Final benchmark” does not run the benchmark

**File:** `scripts/run_final_benchmark.py`

Actual behavior: executes `scripts/build_showcase_data.py`, `scripts/build_run_exports.py`, and four pytest suites. It does NOT invoke `experiments/final_blind_validation/run_blind_benchmark.py` or the formal Nextcloud/RCIR runner, does not create new A/B trials, and does not validate agent patch success under the present code.

**Fix:** create two distinct commands:
- `python scripts/run_benchmark.py --target nextcloud --mode blind --model <model> --tasks <frozen-task-manifest> --replicates N --turn-budget B --run-root experiments/runs` to execute an actual new experiment;
- `python scripts/build_showcase.py --run-id <ID>` to export already validated results without running or changing experimental data.

A compatibility `run_final_benchmark.py` can dispatch to the real runner, but must never print `ALL BENCHMARK VERIFICATIONS PASSED` just because showcase generation and unit tests succeeded. Print distinct `unit_tests`, `retrieval_gates`, `agent_success`, `provider_telemetry`, `provenance` statuses.

**Acceptance:** deleting all previously generated result files and invoking the real benchmark must create new native trials/usage/traces with timestamps; invoking showcase builder with those files missing must FAIL or mark NOT_MEASURED, never regenerate fake metrics.

## P0-02 — RCIR A/B arm is not an independent fresh retrieval

**File:** `experiments/final_blind_validation/run_blind_benchmark.py`

Actual behavior:
- reads `experiments/rcir_v8_5/raw/context/dev_contexts.json`;
- maps `BLIND-TASK-0X` to `TASK-DEV-0X`;
- constructs `ConcreteRCIRContextProvider` from these precomputed task bundles;
- supplies `rendered_prompt_markdown` to the agent;
- if context is missing, silently supplies a generic tier hint.

**File:** `experiments/rcir_v8_5/scripts/run_agent_validation.py` `ConcreteRCIRContextProvider` enumerates supplied `contexts` entries and filters them by symbol/string. It is a *precompiled context bundle delivery adapter*, not itself a live indexer/graph builder/ranker for an unseen task.

**Fix:** implement `LiveRCIRContextProvider` under a dedicated production module, not by importing a benchmark script. Required steps per trial: (1) verify pinned target git commit; (2) load/build actual RCIR index from precisely that target checkout and record graph/index SHA; (3) derive change intent from agent's task statement; (4) execute actual resolver/channel retrieval; (5) fuse/rank candidates using frozen configuration; (6) compile evidence-backed spans under strict token budget; (7) return typed context response; (8) persist complete retrieval trace. Ensure agent `request_context` can obtain further bounded context on demand.

**Fail closed:** missing graph, missing RCIR dependency, absent entries, mismatched source hash, zero retrieved context, provider exception, or fallback hint -> `RCIR_CONTEXT_ERROR`, not a valid RCIR pair. DO NOT substitute DEV task bundles for blind TEST. DEV bundles may be used in unit/integration DEV tests with explicit provenance and never in final TEST.

**Acceptance:** in final RCIR raw trials, show nonempty `index_manifest.json`, `query.json`, `candidates_before_rank.csv`, `ranked_candidates.csv`, `compiled_context.md`, `context_delivery.json`, `source_hash_verification.json`. Assert compiled context comes from source present at the pinned target commit, not task-specific DEV snippets. In the baseline arm, no RCIR context/provider is instantiated. Both conditions have identical permitted repository editing/search/test tools apart from RCIR itself.

## P0-03 — Existing agent results have ZERO successful coding tasks

**Raw/CSV:** `experiments/final_blind_validation/results/blind_baseline.json`; `experiments/runs/run_20261009_blind_verified/exports/paired_token_usage.csv`.

Committed results show 10 individual trials, 5 intended A/B pairs, **3 valid completed pairs**, **2 timeout-affected pairs**, and **0 pairs where both agents solved the task**. All shown agent `files_modified` arrays are empty and diffs are empty. These are *previous* measurements, not performance of the newly fixed benchmark code. Reported median input-token delta over the three valid pairs is +1.68%; one valid pair is negative. Strong token performance is **not demonstrated**.

**Fix:** determine why model responses do not become edits. Record every turn's provider input, untrusted model output, parsed tool JSON, tool name, args (redacted if necessary), tool response, edit outcome, and token usage. Categorize failures: `TIMEOUT`, `NO_TOOL_JSON`, `WRONG_TOOL_SCHEMA`, `BAD_PATH`, `PATCH_CONTEXT_MISMATCH`, `EDIT_REJECTED`, `EARLY_FINISH`, `TURN_EXHAUSTED`, `BEHAVIORAL_TEST_FAILURE`, `REGRESSION_FAILURE`, `RCIR_CONTEXT_ERROR`, `UNKNOWN`. Then fix the actual high-frequency causes. Do not lower acceptance requirements.

**Acceptance:** controlled tool-protocol tests first prove a *known correct patch proposed by a test provider* can pass inspection/edit/targeted test/gatekeeper; this is a **tool plumbing test explicitly marked synthetic**, not a benchmark result. Next, a real local coding model on a completely independent small task must produce a non-empty valid git diff and pass acceptance and regression gates. Only live provider trials can enter scored A/B results.

## P0-04 — “After-fix” results still duplicate baseline trials

**File:** `experiments/final_blind_validation/generate_after_fix_and_delta.py`.

Current `after_fix_data['trials'] = baseline_data['trials']`. A fresh report timestamp does not create a fresh experiment. The report still prints fixed 10/10, 5/5, and L3-pass claims even though source raw baseline says 3 valid pairs and zero successful tasks. This directly contradicts `AUDIT_FINDINGS.md`'s statement that synthetic copying was removed.

**Fix:** completely remove this function's ability to construct trial results. Replace with `compare_runs.py --before <immutable-run-id> --after <immutable-run-id>`, which reads TWO different independently recorded, content-hashed runs, validates revisions/trial origins/target commits, pairs by task and condition, computes deltas and bootstrap intervals, and declines to compare runs that share identical trial hashes or do not meet comparability policy. For historical old failures with no proper run record, label them `HISTORICAL_OBSERVATION_ONLY` and omit comparative percentages.

**Acceptance:** malicious test providing the exact same run twice must fail. Any copied `trials` array as an “after” run must fail the anti-duplication verifier.

## P0-05 — Presentation APIs still simulate “live RCIR”

**File:** `showcase_app/backend/services/rcir_service.py`.

`query()` currently loads `showcase/data/rcir_pipeline.json`, applies a query-term score bump to a few prewritten example candidates, and returns `compiled_tokens` from a default. Query ID is derived from the Python source file modification time rather than an execution. It does not execute RCIR at all.

**File:** `showcase_app/backend/api/rcir.py`.

When an unknown query ID is requested, it runs a “Default accounting ledger query” rather than returning 404. This produces fake-looking retrieval results for nonexistent runs.

**Fix:** reuse the *same* `LiveRCIRContextProvider` and index/config from the formal benchmark; expose query result tied to a unique query ID and captured trace. Return `404` for unknown ID. Never synthesize a query. Return source links only for verified files.

**Acceptance:** changing query text changes actual retrieval results based on source; known dependent files appear from real index; an unknown query ID returns 404; missing index returns 503/typed error; no default token counts/scores; fetch trace artifact and compare every displayed value to it.

## P0-06 — Interpreter UI shows a staged illustration, not end-to-end PolyFlow execution

**File:** `showcase_app/backend/services/interpreter_service.py`.

The implementation manually emits `parse`, `validate`, and `schedule` success events after `asyncio.sleep`, with hardcoded `duration_ms` (0.8, 0.5, 0.3); constructs hardcoded JavaScript/Python `LanguageBlock` strings instead of parsing the selected real `.poly` file; supplies synthetic customer/data values; and marks fallback invoked by setting a boolean and printing an action string. It never proves a declared `@error-map` fallback was actually executed. A SHA-256 digest of a payload is an integrity hash, **not a cryptographically signed receipt**. `fast_native_mode=True` requires independent verification of actual runtime behavior for JavaScript.

**Fix:** `POST /api/interpreter/runs` loads an allowlisted real `.poly` document by feature ID, validates content/source hashes, invokes canonical parser, schema checker, scheduler, real language runtime(s), and actual merge/error policy implementation; captures wall-clock per phase using `perf_counter_ns`; emits SSE events at genuine phase boundaries; persists event/receipt/error artifacts. For the failure demo use a deliberately separate non-critical cell, preferably notification delivery, and a real policy with an executable fallback that can be independently verified (e.g., durable queued notification write). For a critical calculation/ledger failure, show `BLOCKED`/transaction rollback, NOT arbitrary success/degraded. Do not use mocked external send success as real delivery. Record all retry decisions.

**Acceptance:** alter selected `.poly` source or schema and see different actual execution/validation; inject failure and verify real policy transition plus durable fallback artifact; test critical failure blocks commit; all receipt hashes recompute from raw captured event data; signed-receipt label only when a real signing key and signature verification exist.

## P0-07 — Proof exports can sanctify constants

**File:** `scripts/build_run_exports.py`.

The script uses fixed `RUN_ID = 'run_20261009_blind_verified'`, copies stale result JSON, uses numeric fallbacks in `run_summary.csv`, exports `retrieved_files.csv` from `showcase/data/rcir_pipeline.json` (not a live query trace), exports interpreter events from showcase JSON rather than a real run trace, sets `poly_lines = 142/110` by hand, and manufactures a `coverage_ledger.csv` with fixed 840/724/1/3 counts and 100% layers. It stamps every artifact `origin_kind=MEASURED_ARTIFACT` / `measurement_method=NATIVE_EXECUTION` / `validity_status=VALIDATED` without proving the origin. Hashing such a file does not certify its truth.

**Fix:** derive run ID from immutable benchmark manifest, require exact `--run-id`, ingest only raw referenced run artifacts, compute counts/file lines by actual file traversal, source mapping entries by existing checked source paths, interpreter data by execution receipts, retrieval files from source-backed ranked trace, and paired tokens from provider-native recorded usage. Validate all hashes and source file existence; missing proof = `NOT_AVAILABLE` rather than fabricated export. Classify evidence types separately: `RAW_MEASUREMENT`, `DERIVED_FROM_RAW`, `SOURCE_INVENTORY`, `DEMO_ONLY`, `HISTORICAL`, `NOT_MEASURED`; reserve `VALIDATED` for passed validation checks.

**Acceptance:** tests mutate one raw value and verify dependent CSV, JSON, Markdown report all change consistently or fail; missing raw source never yields a positive number; rebuilding cannot mutate the immutable source run.

## P0-08 — Formal gates and agent gate are still mixed

**Files:** `experiments/rcir_v8_5/scripts/run_agent_validation.py`, `experiments/rcir_v8_5/scripts/run_formal_benchmark.py`.

`valid_pairs` in the formal runner is calculated by task ID intersection without preserving `turn_budget` or `replicate`, and the `valid_pairs` field is added to `ab_result` **after** `agent_ab_runs.json` is written. Semantic agent stage `PASS` means only at least one error-free pair, not successful agent edits. The formal runner can treat `NOT_REQUIRED` as PASSED and needs an explicitly versioned stage schema.

**Fix:** define `TrialKey = (task_id, target_commit, model, seed/replicate, turn_budget, condition, experiment_version)`. Group exact baseline-vs-RCIR pairs. Produce independent counters `attempted_pairs`, `valid_pairs`, `successful_both_pairs`, `rcir_solved`, `baseline_solved`, `eligible_successful_pairs`. Use distinct gates: `PROVIDER_REACHABLE`, `PAIR_VALIDITY`, `PATCH_CREATED`, `ACCEPTANCE`, `REGRESSION`, `AGENT_SUCCESS`, `TOKEN_TELEMETRY`. The agent **success** gate must NOT pass on validity alone. Write `ab_result` only AFTER all statistics exist. Version schemas and reject missing fields. Mark optional status `NOT_REQUIRED` distinctly, never call “all passed.”

**Acceptance:** mixed replicate/time-budget tests cannot accidentally pair trials; a valid but failed coding task never passes AGENT_SUCCESS; absent stage file cannot pass.

## P0-09 — Benchmark does not use full pinned target worktree

**File:** `experiments/final_blind_validation/run_blind_benchmark.py`.

`create_worktree` copies only `lib`, `apps/files`, `core`, `ocs`, initializes a new git repository, and commits it. When target path does not exist, it silently uses `repo_root` (the PolyFlow repository!). This makes “real Nextcloud full-repo agent environment” false and deprives tests/composer configuration of the actual upstream repo.

**Fix:** clone/check out exact target commit once (verified clean), then use `git worktree add --detach <trial-dir> <pinned-sha>` per trial. Never substitute PolyFlow root, shadow-copy a partial tree, or commit a repackaged copy as the target under formal mode. Verify `git rev-parse HEAD`, git status, source tree root fingerprint, `composer.json`, and required project tests before trial. Infrastructure failure = `INVALID_SETUP`, not a measured trial. Cleanup worktrees safely after preserving raw diff and traces.

**Acceptance:** missing Nextcloud -> abort with explicit setup error. Every trial worktree reports the same pinned original commit, and git diff is against that commit.

## P0-10 — Wrong comparison: context/token savings on failing tasks

Valid task-independent input-token changes can be shown as exploratory, but the primary efficiency result MUST be on successful, paired, accepted coding tasks. The currently published **1.68%** is based on a 3-pair subset with zero agent successes and an unproven fresh RCIR condition. It is not proof RCIR reduces AI token spending for completed changes. IDE credits remain `NOT_MEASURED`.

**Fix:** report primary `median(provider_input_tokens RCIR vs baseline) on both-successful valid pairs`. If no both-successful pairs, primary metric = `NOT_MEASURED` (not 0%, not +1.68%). Separately show exploratory `all-valid-pair token delta`, with sample size, timeouts, task outcomes, and negative outliers. Report total tokens, turns, wall-clock latency, cost assumptions, provider-native counters, and quality parity. If only one side succeeds, show quality comparison but do not assign cost of a completed solution to a failed run without explicit cost-to-success modeling.

**Acceptance:** zero both-successful trials -> efficiency headline suppressed; strong-looking reduction on a failed/timeout task cannot trigger a PASS claim.

---

# 2. Additional P1 defects: make the measurements defensible

## P1-01 — The benchmark task oracle is not genuinely hidden

`experiments/final_blind_validation/test_design.json` includes `hidden_evaluator` with `hidden_critical_files`, `hidden_dependencies`, and `verification_script` in the same JSON object the runner reads. The agent currently gets a task instruction, but the harness itself holds the answers and has no robust isolation between task generator, context preparation, and evaluator. The same five tasks track prior DEV tasks 1:1. The access guard `BlindAccessGuard.validate_path(target_repo)` merely checks one path; it does not intercept `inspect_file`, `search_code`, `run_command`, or arbitrary code reads by subprocesses. `run_command` must be regarded as a potentially unconstrained escape from denylist checks.

**Fix:** create three physically separate bundles: `public_tasks.json` (available to agent), `hidden_oracle.json` (available only to evaluator in separate process/container), `scoring_config.json` (frozen before experiment). Use upstream historical commits with parent checkout and upstream patch held out. Remove generated solutions/reports from agent-readable filesystem, not merely a Python `validate_path()` that is never used for every file access. Sandbox code exec with filesystem/network controls as feasible; for a full-access IDE agent, record limitation instead of claiming perfect blindness.

## P1-02 — Hardcoded outcome-expectation tests are circular

`tests/test_final_claim_consistency.py` currently contains `assert len(successful_trials) == 0`, `assert valid_pairs == 3`, `assert ... == 10`, `assert gates_passed == 6`, and fixed ERPNext inventory values. `tests/test_backend_proof_server.py` expects a fixed 12 native files, fixed three valid pairs, and 0 successful pairs. These will either fail when the system improves or incentivize modifying results to fit tests.

**Fix:** change tests to recompute results from supplied raw artifacts and assert invariants rather than historical values. Historical snapshot tests may live in `tests/fixtures/historical/` and verify that old data is parsed correctly, but MUST not gate current real results. Add tests with 0/1/3/5/20 valid pairs, timeouts, negative savings, both successes, one-sided successes, malformed JSON, and missing proof files.

## P1-03 — Agent turn protocol is unnecessarily brittle

`orchestrator/agent_loop.py` calls an LLM with a long tool-description prompt and extracts JSON from text via regex/brace heuristics. It hard-instructs Turn 1 inspect, Turn 2 edit, Turn 3 verify, Turn 4 finish even when a different plan is needed. A 1.5B coder model may omit/malformed JSON, never issue the edit, or spend entire 5-turn budget inspecting. Malformed tool responses and provider timeouts need typed handling. The model is currently too weak to evaluate a demanding enterprise multi-file autonomous coding system reliably.

**Fix:** implement a versioned tool-call schema and JSON schema validation (`tool`, `args`), robust parser that handles fenced and unfenced output, retry-format once without inventing tool calls, role-separated observations, small task-specific tool docs, bounded context, and structured `error_code`. Prefer native provider tool calls where available. Permit up to 8/12/16 turns for complex tasks but record all budgets independently; freeze the primary budget before TEST. Add user-selected stronger local coding model as a separately reported model stratum (do not mix 1.5B and 7B/14B token results in one headline). Same model/sampling seed/settings and tools in A/B.

## P1-04 — Generic error fallback and command safety

`orchestrator/tools.py` supports `run_command`; verify subprocess isolation, timeout, command allowlists, cwd restrictions, no acceptance script file edits, no outside-repo edits, and test-target integrity. Make old/new exact edits atomic with backup. Log command/stdout/stderr/exit. Re-run after patch, not merely trust model's `finish`. Verify the evaluated tree contains the actual diff.

## P1-05 — Regression is still only syntax lint

Even after the latest fix, `verify_regression.py` returns “Regression syntax checks passed” after `php -l` for modified files. This is L1, not L3. An interface change may require all implementing classes to change and may pass syntax. Model test commands need actual composer/PHPUnit/bootstrap setup and matched affected suites. A zero-diff trial should show `NOT_RUN_NO_PATCH`, not `PASS`.

**Fix:** classify `L1_SYNTAX`, `L2_TARGETED_BEHAVIOR`, `L3_AFFECTED_UPSTREAM_REGRESSION`; run real Nextcloud tests using the pinned repository's available tooling, including interface implementers and repository-aware test selection; record exact command and test counts. If dependencies not installed, report `BLOCKED_ENVIRONMENT` rather than PASS.

## P1-06 — Feature Closure “coverage” is not independent

`rcir/src/rcir/adapters/frappe_erpnext.py` now improves paths/hashes, but the broad claims (840, 842, 712940, 100%) must be recomputed from actual pinned checkouts. `feature_closure_validation.json` was newly committed but may use a hand-selected oracle. The display of five features 100% recall can coexist with relatively low precision (source manifest listed 8 expected and 17 returned for Item; precision 47.1%). That matters. Reports cannot hide false positives. Separate `discovered`, `mapped`, `validated`, `executable`, and `behavioral parity proven`. Independently curate upstream true source edges without inspecting generated closures.

## P1-07 — More fixed backend defaults

`showcase_app/backend/services/benchmark_service.py` always reads one global old `blind_baseline.json`, ignores `run_id`, provides default 10/3/0/+1.68 values; `ERPNextService.get_tree` returns 840/842/712940 when file is absent; `showcase_app/backend/schemas.py` hardcodes `HealthResponse.evidence_status='VALIDATED'`. Also the proof registry fixes run ID to `run_20261009_blind_verified`; all status views must be resolved by the actual selected immutable run.

**Fix:** use run-scoped service registry; `GET /runs/{run_id}` loads only artifacts in that verified run; unknown run -> 404; unmeasured metrics are `null + NOT_MEASURED`; health is process liveness, not evidence validity.

## P1-08 — Proof index hashes file integrity, not truth

`scripts/build_run_exports.py` stamps every item `MEASURED_ARTIFACT` and `VALIDATED`, even when it was copied from hardcoded UI data. `EvidenceRegistry` checks SHA after choosing a proof; good start, but the origin and semantic validity are not confirmed. Require `origin_run_id`, `producer`, `input_artifact_hashes`, `artifact_type`, `measurement_source`, `validation_checks`, `run_commit`, target commit, and path. No generated summary becomes “raw measurement.” Permit browsing raw trial output securely, and enforce `resolve(...).relative_to(run_dir)` for run-index paths without alternate repo-wide resolution by arbitrary `source_file`.

## P1-09 — CI tests do not execute end-to-end benchmark

`.github/workflows/ci.yml` runs a subset of Python tests and React build, but not the FastAPI proof server tests and not live benchmark execution. GitHub exposed no statuses/workflow runs for current HEAD at this review. The latest `AUDIT_FINDINGS.md` statement “19/19 tests passed” is not independently reproducible from GitHub. Configure lightweight CI including backend routes, SDK black-box, harness unit checks, and evidence anti-fabrication tests; add optional manual workflow_dispatch full benchmark with proper model/runner, commit/run parameters, artifact uploads, and no hardcoded green status.

## P1-10 — UI focus remains secondary

The existing minimal HTML/CSS/JS frontend under `showcase_app/frontend/` is the right direction; do not start a third frontend. But no amount of responsive layout will make a fabricated 100% result acceptable. Hide unverified metrics, make proof links open exact raw/derived files, and display 3-item status bar: `run`, `commit`, `evidence validity`. Keep 5 simple tabs and the flowing interpreter diagram, but no additional animations until backend metrics are clean.

---

# 3. Rebuild benchmark architecture: one actual run is the source of truth

## 3.1 Required packages/modules and ownership

Refactor or add as appropriate; discover existing imports and reuse working RCIR components. Do not duplicate core parsers/rankers/context compiler just to satisfy suggested filenames.

```text
experiments/
  benchmark_core/
    models.py                # typed immutable RunManifest, TrialKey, Trial, Gate, Usage
    isolation.py             # exact upstream git worktrees; no partial copies
    task_loader.py           # public tasks only
    evaluator.py             # private oracle invocation in separate evaluator process
    runner.py                # executes real condition arms
    pairer.py                # exact matched A/B pair construction
    metrics.py               # micro/macro accuracy, latency, quality, token/cost metrics
    validity.py              # fail-closed gating, provenance, provider errors
    hashes.py                # input and artifact sha256 verification
    report.py                # emits Markdown/CSV strictly from measured canonical data
    failure_taxonomy.py      # standardized terminal statuses
  nextcloud_validation/
    ...                      # retain existing examples, DEV/TEST split
  final_blind_validation/
    ...                      # migrate old artifacts under historical/; do not restamp
  runs/
    <source-commit>_<timestamp-or-uuid>/
      manifest.json
      tasks_public.json
      oracle_digest.json
      index/
      raw/
        <task>/<condition>/<replicate>/
          trial.json
          provider_usage.jsonl
          tool_events.jsonl
          search_events.jsonl
          retrieval_query.json
          retrieval_candidates.csv
          retrieval_ranked.csv
          compiled_context.md
          context_delivery.json
          patch.diff
          acceptance_before.json
          acceptance_after.json
          regression.json
          toolchain.json
      results/
        retrieval_accuracy.json
        task_outcomes.json
        paired_tokens.json
        performance.json
        gates.json
      exports/
        trial_manifest.csv
        pairs.csv
        retrieval_tasks.csv
        missed_files.csv
        false_positive_files.csv
        provider_tokens.csv
        latency.csv
        feature_closure.csv
      reports/
        BENCHMARK_REPORT.md
        FAILURES_BY_CATEGORY.md
        COMPARISON.md
      proof_index.json
```

**Critical distinction:** `run` artifacts are immutable. A showcase generator can build a new view of an existing immutable run without overwriting it, and it cannot silently change any raw source. A re-run always gets a new ID. Record git commit + dirty status, target commit, hashes of task config, ranker config, oracle digest, environment, model version, provider version, tokenizer/measurement source, and exact command. Record wall-clock start/end independently from report creation time.

## 3.2 Typed metrics contract

Use strict Pydantic/dataclass validation (implementation choice), with these status classes:

```text
TRIAL_SUCCESS
TRIAL_FAILED_BEHAVIOR
TRIAL_FAILED_REGRESSION
TRIAL_FAILED_AGENT
TRIAL_TIMEOUT_PROVIDER
TRIAL_TIMEOUT_TOOL
TRIAL_INVALID_SETUP
TRIAL_INVALID_CONTEXT
TRIAL_INVALID_EVIDENCE
TRIAL_NOT_MEASURED
```

Separate `valid_for_token_analysis`, `valid_for_agent_quality`, `accepted_patch`, `provider_telemetry_valid`, and `retrieval_trace_valid`. A trial can be valid measurement while failing task; do not discard all legitimate negative evidence. A trial that timed out after some calls can show partial observed tokens **but cannot be paired as an ordinary successful completed trial**. Return optional numeric values as `null` for genuinely absent measurements; never conflate 0 with NOT_MEASURED.

## 3.3 Run manifest example: schema illustration only, not actual evidence

```json
{
  "schema_version": "2.0.0",
  "run_id": "<new actual id>",
  "polyflow_sha": "<git rev-parse HEAD>",
  "polyflow_dirty": false,
  "target_repo": "nextcloud/server",
  "target_sha": "<actual pinned commit>",
  "task_manifest_sha256": "<sha256>",
  "hidden_oracle_sha256": "<sha256, do not publish oracle until evaluation complete>",
  "ranker_config_sha256": "<sha256>",
  "index_manifest_sha256": "<sha256>",
  "provider": "ollama",
  "model": "<model+digest>",
  "turn_budget": 12,
  "replicate_count": 3,
  "measurement_source": "PROVIDER_NATIVE",
  "start_time_utc": "<actual>",
  "end_time_utc": null,
  "status": "RUNNING"
}
```

Do not fill placeholder strings in a committed `VALIDATED` run artifact. Use strict validation to reject unresolved placeholders.

---

# 4. Correct experiment design and honest metrics

## 4.1 Before touching performance: verify prerequisites

Execute a setup check that records PASS/FAIL/NOT_MEASURED for:

```text
PolyFlow clean HEAD at pinned commit
Nextcloud exact pinned commit available locally
Full Nextcloud source tree and composer/package configuration present
PHP runtime and relevant test toolchain
PolyFlow Python tests
PolyFlow RCIR importability
Graph/index builder and retrieval API
Local Ollama availability and model digest
Model request token counter actually provided by backend
Git worktree creation and cleanup
Known-good agent edit/check command
```

A missing prerequisite blocks scored runs rather than triggering fallback to an unrelated repo or a cached DEV blob.

## 4.2 Distinct experiment families; NEVER pool them

### E0: unit/property tests

Purpose: verify parser, ranking functions, token accounting, pairing logic, fail-closed behavior, sandboxing, schema, and evidence lineage. Mock/fake providers are permitted ONLY within tests and labeled as such. E0 results are never part of live-model benchmark averages.

### E1: retrieval-only evaluation

Purpose: RCIR accuracy and speed independent of any LLM. Tasks are frozen; use source-derived target-commit ground truth. Report per-task recall, precision, critical source recall, silent misses, MRR, nDCG@k, false positives, query latency p50/p95/p99, index build time/peak RSS. Evaluate at fixed rank budgets top-5/top-10/top-20 and fixed context budgets 2k/4k/8k. Classify AST exact, typeflow, lexical, inferred relationships separately. Use credible lexical/BM25 baseline. Report query class and difficulty.

### E2: context-only comparison

Purpose: source-backed relevant context coverage vs token size. Compare lexical search/context and RCIR under the SAME token budget. Tokenize with explicit tokenizer and count both the returned content and overhead. Measure source recall/precision and packing/truncation. A lower token count with poor recall is not an automatic win. Publish coverage-vs-budget curves.

### E3: independent end-to-end coding A/B

Purpose: model + tools + tests + context. Same task, parent commit, model/digest, tool schema, turn budget, provider endpoint, sampling settings, environment, hidden evaluator, wall-clock policy. Only difference is availability of RCIR context. Record every tool event and usage from provider. Score edit produced, behavior passed, regression passed, accepted, input/total tokens, turns, wall clock, search counts, and retries. Include unsuccessful pairs instead of dropping them from quality statistics.

### E4: PolyFlow interpreter/runtime

Purpose: prove parser->schema->scheduler->host cells->merge/error-policy and fault isolation on a real `.poly` vertical and real host runtimes. Does not contribute to E3 agent token percentages.

### E5: ERPNext source-closure and executable subset

Purpose: prove structural transformation, independent closure precision/recall, real `.poly` execution for selected verticals and, separately, actual upstream functional parity. Does not become a substitute for E3 Nextcloud A/B.

## 4.3 Task design and holdout

Keep the original five tasks for DEV diagnostics only. Design new tasks from independently sampled upstream Nextcloud historical issue/commit series. For each:
1. select public upstream commit showing a concrete change; pin parent commit as starting tree;
2. create an unambiguous natural-language task from change intent, without revealing gold file list or diff;
3. independently record gold changed files, relevant call/interface consumers, regression tests, desired behavior and potential unrelated noise;
4. hold upstream patch and test oracle outside agent sandbox;
5. freeze oracle and task manifest hashes BEFORE running RCIR or model agent;
6. stratify local, cross-file, cross-module, framework/interface, configuration, runtime, and architecture tasks;
7. preserve a final TEST set untouched by algorithm/weight selection.

Use at least three sets: `DEV` for debugging, `VALIDATION` for choosing algorithms/weights, `TEST` for one-shot final report. Once TEST opened, substantive changes require version `vNext` and a new holdout; never overwrite the published TEST result.

## 4.4 Experimental matrix

Use an incremental cost-effective schedule, not thousands of blind attempts:

**Smoke (must pass before expensive trials):** 1 known-correct tool plumbing task, 2 real RCIR retrieval calls, 1 small real coding task, 1 timeout/failure test. Proven provider calls and actual edit required. Results labeled DEV.

**DEV/VALIDATION:** initial 5-8 different tasks, 2 conditions, primary prechosen turn budget (suggest 12) with 2 replicates; debug actual failure taxonomy. Add sensitivity study 5/8/16 only as separate strata, not mixed.

**Final TEST:** aim for at least 10 genuinely unseen tasks × 2 conditions × 3 repetitions = 60 executions, if runtime permits; report actual executed N, never invent. A 5-task/1-replicate run is a smoke sample, not strong statistical evidence. If local model has insufficient capacity, evaluate a stronger *available* local coding model as a separate stratum (for example, 7B/14B if supported by hardware) and maintain baseline/RCIR model equality. Never claim a stronger model result for 1.5B.

**Provider health:** record explicit health probe and timeouts. Use bounded transport retry for transient errors (same settings), mark attempts, and never rerun solely to cherry-pick better outcome. Decide retry rules before TEST.

## 4.5 Compute exact metrics and meaningful uncertainty

For pairs with baseline input tokens `B` and RCIR `R`:

```text
input_delta_pct = 100 * (B - R) / B
```

Similarly total tokens. `B > 0` and both provider usage records must be valid. Report weighted and median pair deltas, N, confidence intervals/bootstrapped interval over tasks, per-task variance over replicates, negative outliers, and paired task-success comparison. Prevent model mixing. Use two distinct primary panels:

- **Task quality:** accepted RCIR vs accepted baseline on all valid task trials. Is one better or worse?
- **Efficiency at equal task quality:** on both-successful pairs, measured input/total tokens and latency. Mark inconclusive if N=0. Also show efficiency over *all valid completed* task attempts with failure caveat.

For retrieval quality, publish per-task expected critical files, retrieved critical files, misses, rankings and source hashes (after task oracle unsealed). Report macro and micro metrics, not just best-task success. For interface changes, count missing concrete implementer files as false negatives.

## 4.6 Targets vs results

The engineering ambition may be substantial token savings (historically 80-90% desired), but that is an **optimization target, not a required fabricated outcome**. Meaningful release gate should include:
- all benchmark tooling integrity tests pass;
- index/current worktree provenance valid;
- all N valid paired samples independently verifiable;
- nonempty actual success sample, ideally sufficiently large for a confident quality result;
- no unacceptable regression in accepted-task success vs baseline;
- retrieval precision and critical source recall meet pre-declared gates on unseen TEST;
- numeric saving appears ONLY if measured, with direction and uncertainty;
- no P0 correctness/evidence bug;
- proof files and provenance complete.

If RCIR yields lower tokens but lower correctness, show the tradeoff rather than marketing a win. If all coding tasks still fail, benchmark is **NOT READY FOR EFFICIENCY CLAIMS** even if graph retrieval itself meets gates.

---

# 5. Source-level RCIR improvements to pursue AFTER true baseline

These are engineering hypotheses, not guaranteed fixes. Measure each ablation on VALIDATION first and retain only real generalizable gains.

## 5.1 Better change-intent understanding

Ensure task-to-entity resolver recognizes exact symbol, class, interface, route, file, DocType/controller names and semantic aliases. Log parsed target intent, unresolved symbols and alternatives. Avoid selecting a symbolic target merely because a word appears in the prompt. For PHP, recover interface implementation edges and transitive dependencies where evidence exists.

## 5.2 Rank by relevance *and* evidence strength

Add or improve source-derived channels: direct AST references, call edges, class/interface implements/extends, typeflow, route/registration, tests tied to owners, DI injections, file co-change (if available from proper git history). Penalize hubs and lexical noise. Use candidates deduplicated by canonical file/symbol ID, with span-level evidence. Re-ranking must be trained ONLY on DEV/VALIDATION. Preserve the existing measured `OperationCascade` when it beats alternatives; do not reset to naive scorer blindly.

## 5.3 Fix retrieval precision without destroying recall

Prior results may have strong recall with large candidate overretrieval. Introduce retrieval stages: high-recall candidate pool, evidence fusion to file-level ranking, evidence-span selection, budgeted context packing. For each task print source file recall vs candidate count and false positives. Add mandatory-context constraints for directly changed API, method implementers and tests where source evidence supports them. Monitor worst-case task and silent misses.

## 5.4 Actual token savings should come from fewer *unnecessary actions*

Use context-on-demand rather than supplying verbose precompiled context unconditionally. Include small initial relevant set; ask for additional results when confidence low. Distinguish `input_context_tokens`, `tool_result_tokens`, `provider_input_tokens`, `provider_output_tokens`, and `total_session_tokens` as separate fields. Track redundant re-reads, duplicate context, searches/turns. Cache provider context only where safe and account for it correctly. Optimize total provider billed/consumed tokens, not just the “RCIR markdown budget.”

## 5.5 Retrieval performance and cache

Pin index input commit and config; persist symbol/edge lookup and inverted evidence indexes rather than rescanning an entire 50k-node graph per query. Benchmark cold/warm p50/p95, peak RSS and indexing time, with same hardware. Selective incremental invalidation by source hashes. Never show a 1.2ms animation constant as real retrieval speed.

## 5.6 No developer leakage

No `TASK-DEV-0X` task mapping, no hardcoded Nextcloud answer paths in production RCIR retrieval, no display-only boost of candidate scores. Version the ranker. Freeze weights before TEST. Use independent evaluator to compute recall/precision; RCIR itself cannot define its own gold set.

---

# 6. Agent correctness and editing protocol

## 6.1 Tool integration tests

1. Open known upstream file and inspect source (read path, line bounds).
2. Edit a unique exact string (real worktree), verify git diff, then restore.
3. Apply a real unified patch, verify `git diff --check` and source compilability.
4. Ensure apply_patch rejects malformed patch / files outside repo.
5. Allow tests/compilers only within controlled environment; retain outputs.
6. Test malformed tool JSON, truncated JSON, quoting, nested strings and braces.
7. Test one bounded provider timeout and deterministic retry policy.
8. Verify tool events are append-only and record both success and error cases.
9. Verify early `finish` without patch+tests does not approve.
10. Verify a known-good edit receives APPROVE only from independent evaluator. Mark this as E0 test, NEVER add to live scoring.

## 6.2 Agent prompt policy

Do not hard-force exact tool actions by turn count. Give a minimal task objective, available tools, context budget, and acceptance command. Offer a suggested inspect->plan->edit->verify flow, but let the model allocate turns. After a failed patch, return concise actionable error. If model omits tool JSON once, issue syntax-correction feedback and count that turn. Do not silently fabricate tool calls.

## 6.3 Verify real edit success

A scored success needs all of:

```text
Pinned upstream checkout verified
Nonempty diff over source files relevant to task
All modifications inside trial worktree
Tool trace shows actual edit(s)
Acceptance BEFORE = FAIL for the new behavior (or documented pre-existing baseline)
Acceptance AFTER = PASS
Required targeted upstream unit/integration tests pass
Relevant regression suite pass where available
No forbidden test/oracle/source changes
Provider telemetries match model/digest
Independent Gatekeeper APPROVE
```

Do not accept a patch because its diff contains the words specified in task. Public interface changes require checking implementer compatibility and loaded classes in addition to textual declarations. A `php -l` pass is syntax-only.

## 6.4 Root-cause analysis for failed tasks

For each failed task create `failure_analysis.json`: classify the first irreversible failure and root cause. Separate RCIR retrieval misses from model decoding inability, provider timeouts, bad worktrees, insufficient turn budget, and test environment problems. Fix most common structural causes across tasks, not by adding task-specific strings. Show before-after of *failure categories* on truly new runs.

---

# 7. Proof-first backend with a minimal UI later

## 7.1 Keep one backend and one simple frontend

Use `showcase_app/backend/` (FastAPI) and `showcase_app/frontend/` (HTML/CSS/JS) already committed. Do not start another React project. Preserve the existing source if working but repair fake endpoints. Reuse an actual benchmark-independent RCIR service and interpreter service, not UI-specific parallel algorithm implementations.

### Required routes

```text
GET    /api/health                       -> process health only
GET    /api/runs                         -> available immutable run IDs
GET    /api/runs/{run_id}                -> validated run metadata and gate states
GET    /api/runs/{run_id}/metrics        -> derived verified metrics
GET    /api/runs/{run_id}/pairs.csv      -> paired A/B export
GET    /api/runs/{run_id}/retrieval.csv  -> real scored retrieval traces
GET    /api/runs/{run_id}/trials.csv     -> full agent trial breakdown
GET    /api/runs/{run_id}/proofs         -> evidence with sha/origin/path
GET    /api/proofs/{proof_id}            -> exact artifact, allowlisted, hash-verified
POST   /api/rcir/queries                -> actual graph/index/rank/context retrieval
GET    /api/rcir/queries/{query_id}      -> captured run or 404
POST   /api/interpreter/runs            -> actual parsed .poly execution
GET    /api/interpreter/runs/{id}/events -> real SSE execution events
GET    /api/features                    -> source-backed feature closures
GET    /api/features/{feature_id}       -> source references and .poly contract
GET    /api/erpnext/tree                -> derived source-backed module inventory
```

`run_id` selection must actually change the underlying loaded artifacts. Unknown IDs always 404. Missing graph 503. Do not return fabricated fallback values. If the selected run is invalid/unproven, reflect it prominently but unobtrusively.

## 7.2 Correct proof provenance

Proof registry paths must be relative to one verified run directory. The server verifies sha256 and allowed type; do not resolve a malicious `source_file` field anywhere under the entire repo. Provide browser-openable JSON/CSV/plaintext/diff, not only download. A proof item carries `producer`, `origin_kind`, `input_hashes`, `created_utc`, `git_commit`, `target_commit`, `measurement_source`, `status`, and `sha256`. Derived source must have traceable raw parent. A static documentation file is not a benchmark proof. Run invalidation must immediately make stale UI metrics non-validated.

## 7.3 UI, ONLY AFTER evidence is valid

**Five tabs with almost no prose:** 1 PolyFlow, 2 Interpreter, 3 RCIR, 4 Proofs, 5 ERPNext. Each tab one diagram + a few relevant live values. Avoid engine jargon on screen; the presenter narrates.

**PolyFlow:** left native ERPNext source tree, right generated feature-centric `.poly`; click source -> highlight corresponding `@source` binding. Display real native artifact count, actual directory count, number of languages and `.poly` feature modules. No “all ERPNext functions rewritten” implication.

**Interpreter:** one-click real parse->validate->schedule->language runtimes->merge/fallback->receipt flow; packets driven by actual event stream. Two buttons `Normal run`, `Failure injection`; show HEALTHY/DEGRADED/BLOCKED honestly. No arbitrary `asyncio.sleep` pretending to be processing. Open actual receipt and error CSV/JSON.

**RCIR:** one horizontal line (repo->graph->retrieval->rank->context->agent), small ranked file list and actual A/B bar chart. Show whether A/B is `VALID`, `INCONCLUSIVE`, `NOT_MEASURED`; show task completion alongside token numbers; never call 1.68% a success headline until E3 meets the gate. Real query triggers service code, not cached sample-score manipulation.

**Proofs:** table only: run, timestamp, task N, valid N, success N, artifact links. CSV, patch, usage, retrieval trace, manifest all openable.

**ERPNext:** scale inventory, tree, selected full-stack closure, source files and exact .poly path, independently measured coverage and executable/behavioral status. No wall-of-text explanation. Every metric clickable to its source.

Responsive: 1920x1080, 1440x900, 1366x768, 1024x768, ~390px mobile. No clipped text, horizontal page overflow, oversized graphs, or sticky overlays hiding content. Prefer plain SVG/CSS transitions for only the active workflow. No emojis; no clutter. Accessibility: keyboard usable, `prefers-reduced-motion`, aria labels and focus states.

---

# 8. ERPNext complete conversion: the correct end-state and proof

This is the FINAL phase after Nextcloud/retrieval/agent/telemetry gates are credible.

## 8.1 Original PolyFlow goal

ERPNext/Frappe business behavior is distributed across Python controllers, JS client scripts, DocType JSON/ORM, hooks, permissions, tests and cross-DocType links. PolyFlow provides one feature-centric entry point per capability while keeping native source references and host runtime fidelity. Avoid one giant `.poly` file. Distinguish three achievements:

1. **Whole-project structural accounting:** every in-scope file has an ownership status with repo-relative path and real hash; every feature closure has provenance.
2. **Executable PolyFlow verticals:** selected `.poly` cells actually run through real host runtimes with contracts/failures/merges.
3. **Complete ERPNext behavioral parity:** a much higher bar requiring real Frappe bench / MariaDB / Redis / associated framework integration and upstream test suites. Not proven by mapping `@source` tags or by custom arithmetic examples.

## 8.2 Migration inventory first

Create a deterministic migration ledger from pinned Frappe/ERPNext checkout: language, path, content hash, owner feature, role, import/link/event relationships, associated tests, status. No fixed “840” or “842” acceptance assertions. Compute `actual Doctype schema count`, `generated .poly count`, `mapped artifacts`, `unresolved/ambiguous`, `executable cells`, and tested verticals. Unsupported generated/vendor artifacts require explicit classification.

## 8.3 Independently verify actual feature closures

Select Sales Invoice, Payment Entry, Stock Entry, Item, Customer and random holdout features. Independently adjudicate source list; compute recall **and precision**. For Items the earlier representative data gave 8/8 recall but 8/17 precision; this proves why recall-only 100% presentations are misleading. Derive hooks from registered events, not attaching generic `hooks.py` to every feature. Do not award 0.85 just for absent evidence. Use actual Frappe DocType metadata as ORM truth, not an invented SQL layout.

## 8.4 Actual runnable parity

Choose representative verticals such as Sales Invoice tax/ledger, Stock valuation, Payment Entry, permissions, and client->API boundaries. Compare native ERPNext and PolyFlow implementations on identical real input fixtures, expected output records, edge cases, validation failures, transaction outcomes and side effects; upstream tests must run against real Frappe environment. Verify schema, state change and persistence. A simplified independently authored Python calculation is a DEMO vertical, not ERPNext parity. Disable native modules selectively only when real behavior supports it. Full parity claim only when every in-scope capability is exercised with upstream-equivalent tests and documented coverage; otherwise report validated subset and missing scope.

---

# 9. Execution phases / non-negotiable gates

| Phase | Objective | Concrete work | Exit gate |
|---|---|---|---|
| G0 | Forensic freeze | Capture current HEAD, source inventory, original 3 valid/2 timeout/0 successes snapshot | Exact hashes and report, labeled historical |
| G1 | Correct harness | Immutable worktrees; task/oracle split; run IDs; real execution CLI; valid pair accounting | All negative/failure tests pass |
| G2 | RCIR real retrieval | New `LiveRCIRContextProvider`; provenance; no DEV blob/hint; proper index | Nonempty target-commit retrieval and source trace |
| G3 | Agent tool plumbing | JSON tool protocol; stable patch application; gated tests; errors classified | Known-good plumbing test passes, at least one LIVE task independently passes |
| G4 | DEV baseline | Run with actual 1.5B model; stratify a stronger local model if available | Real failure distribution measured |
| G5 | RCIR optimization | Resolver, ranker, evidence channel, packer, caching; ablations on VALIDATION | Predeclared accuracy gates without hidden TEST tuning |
| G6 | Final independent TEST | Frozen tasks, N valid paired repeats; acceptance, regression and native telemetry | Scored raw evidence immutable, including failures |
| G7 | Evidence generator | Derive CSV/JSON/Markdown from frozen raw run only | Recompute / mutation tests pass |
| G8 | Live backend | RCIR actual queries, `.poly` actual runtime, proof links | Contract + integration tests pass |
| G9 | Minimal UI | Clean diagrams; responsive aspect ratios; openable evidence | Browser/visual tests pass with exact run labels |
| G10 | ERPNext | Feature mapping + independent recall/precision + native parity subset | Scope and evidence labeled accurately |

**Hard stop:** Do not begin G8/G9 UI enhancement if G1/G2/G3 are still invalid. A working local backend skeleton may be retained, but do not use it as evidence of performance improvement.

---

# 10. Exact regression tests that must be implemented

Build tests under `tests/benchmark_integrity/` and reuse established tests where correct. All tests must be data-driven, not assert remembered counts.

```text
test_missing_nextcloud_does_not_fallback_to_polyflow.py
test_git_worktree_pinned_commit.py
test_worktree_is_full_target_repository.py
test_rcir_arm_uses_live_context_provider.py
test_rcir_missing_index_invalidates_trial.py
test_rcir_missing_context_never_returns_hint.py
test_rcir_context_hash_matches_target_source.py
test_baseline_has_no_rcir_context.py
test_hidden_oracle_unavailable_to_agent_tools.py
test_two_conditions_have_identical_tool_permissions.py
test_pair_key_uses_task_model_budget_replicate_commit.py
test_pair_timeout_excluded.py
test_pair_partial_usage_is_not_successful_completion.py
test_tool_json_parser_nested_braces.py
test_apply_patch_has_nonempty_real_diff.py
test_agent_finish_without_patch_rejected.py
test_missing_l3_not_pass.py
test_interface_impl_regression.py
test_provider_usage_exact_native_vs_estimated.py
test_duplicate_before_after_run_rejected.py
test_report_metrics_recomputed_from_raw.py
test_export_missing_raw_is_not_verified.py
test_proof_hash_tamper_rejected.py
test_unknown_query_id_404.py
test_rcir_api_hits_real_retriever.py
test_interpreter_loads_actual_poly_file.py
test_interpreter_failure_executes_fallback.py
test_critical_failure_blocks_persistence.py
test_receipt_hash_round_trip.py
test_health_not_equal_evidence_validity.py
test_erpnext_source_file_coverage.py
test_erpnext_closure_precision_recall.py
test_no_hardcoded_status_or_inventory_defaults.py
```

Fix test names spelling as needed; assertions are behavioral. Create property tests for pair arithmetic, token validity and ledger percentages. Test source read with Windows spaces and long paths, and POSIX paths, using isolated temp repositories. Commit fixtures only for E0; never place hidden real TEST gold beside public tasks.

---

# 11. Expected commands and evidence-driven completion

Use actual script API discovered/created; these example calls specify intended interface, not proof of execution.

```bash
# Phase 0: inspection and initial gate tests
python -m pytest tests/benchmark_integrity -q

# Phase 1: build pinned actual RCIR index
python -m experiments.benchmark_core.index_cli --repo experiments/nextcloud_validation/nextcloud-server --out experiments/indexes/nextcloud_pinned

# Phase 2: run real paired DEV benchmark
python scripts/run_benchmark.py --target nextcloud --mode dev --tasks experiments/tasks/dev_public.json --provider ollama --model <installed-model> --turn-budget 12 --replicates 2

# Phase 3: run frozen TEST only after selecting config on DEV/VALIDATION
python scripts/run_benchmark.py --target nextcloud --mode test --tasks experiments/tasks/test_public.json --provider ollama --model <installed-model> --turn-budget 12 --replicates 3

# Phase 4: independently verify and export immutable run
python scripts/verify_run.py --run-id <actual-run-id>
python scripts/build_showcase.py --run-id <actual-run-id>

# Phase 5: run tests / backend
python -m pytest tests/benchmark_integrity tests/test_backend_proof_server.py tests/test_final_claim_consistency.py -v
python scripts/run_showcase.py --run-id <actual-run-id>
```

Stop and report `BLOCKED_ENVIRONMENT` rather than silently downloading paid models, changing provider model settings, or using an unrelated repository. No shell-based source edits to target benchmarks while evaluating. Keep full process stdout/stderr in proof artifacts.

## Final mandatory report sections

Generate `FINAL_BENCHMARK_AUDIT.md` strictly from source evidence, containing:
1. current PolyFlow commit / target commits / environment;
2. phase gate status and exact commands;
3. E1 retrieval metrics, recall/precision misses by task;
4. E2 context quality and packed token budgets;
5. E3 agent success baseline vs RCIR, task outcomes, tool edits/diffs and regression;
6. valid/invalid/timeout counts, paired provider input/total token comparison and uncertainty;
7. negative or inconclusive outcomes shown prominently;
8. E4 real parser/runtime normal and failure receipts;
9. E5 ERPNext structural closure and independently tested executable subset;
10. exact SHA + relative link to every raw proof;
11. outstanding failures and root-cause improvement targets;
12. separate `VERIFIED`, `PARTIAL`, `NOT_MEASURED`, `INVALID` status for each subsystem.

Also deliver `IMPLEMENTATION_CHANGELOG.md` with actual code changes, issue ID, file path, test that proves fix, and observed delta before/after from distinct valid runs.

---

# 12. Acceptance contract (no “everything passed” shortcuts)

The implementation agent may declare the benchmark **RELIABLY VALIDATED** only when all conditions below hold:

```text
[ ] No active P0 harness/evidence bugs
[ ] Actual Nextcloud pinned source git worktrees per paired trial
[ ] Both arms use identical model/settings/tooling apart from real RCIR
[ ] RCIR used live source-derived index, not DEV-context cached snippets
[ ] No RCIR fallback to textual hints on missing context
[ ] All task/gold separation and TEST freeze checks pass
[ ] Provider-native usage persisted per turn with model identity
[ ] Valid pair accounting excludes timeouts/errors
[ ] A/B success/correctness metrics include all measured failures
[ ] Primary successful-task efficiency has real both-successful pairs, or NOT_MEASURED
[ ] At least one real agent tool edit and independently passing acceptance/regression exists
[ ] L3 passes real affected test suite, not php -l only
[ ] Token savings claims use real valid comparable runs and show N / uncertainty
[ ] Baseline/after-fix represent truly independent executions
[ ] Reports, CSVs, UI, proofs all derive from selected immutable run
[ ] No fixed business/ERPNext artifact counts in metric code
[ ] Every supposedly live RCIR query runs real retrieval and has trace
[ ] Every interpreter workflow stage comes from actual .poly and runtime events
[ ] Fallback action is executed and verified, not printed as a string
[ ] ERPNext structural mapping not mislabelled as full behavioral parity
[ ] Proof URLs open exact source and pass SHA validation
[ ] Backend and UI tests run in CI with visible status
```

**Strong result goal (not a fabricated requirement):** achieve higher critical-source recall/precision, fewer wasted retrievals/tool turns, and materially lower provider tokens while preserving or improving accepted coding-task success on unseen tasks. A hard threshold such as “80% token reduction on all tasks” is not a valid scientific acceptance gate. Quality and reproducibility come first.

---

# 13. Immediate implementation order: first 20 concrete actions

1. Make a clean detached branch/worktree at audited HEAD; record revisions and historical outputs unchanged.
2. Mark `experiments/runs/run_20261009_blind_verified` as **HISTORICAL DERIVED EXPORT**, not fresh current-HEAD benchmark.
3. Create canonical TrialKey, validity states, and immutable run schema.
4. Fix full git worktree creation and eliminate PolyFlow-root fallback.
5. Split public tasks / private gold oracles; remove DEV mappings from TEST.
6. Implement source-derived `LiveRCIRContextProvider` in reusable production package.
7. Wire agent tool environment to real provider; fail closed on absence.
8. Persist query/input/index/provenance/ranked candidates/compiled context per trial.
9. Build negative unit tests for timeout, no context, no diff, invalid status.
10. Repair tool call parser, structured retries, edit logging and accepted patch recording.
11. Make a real targeted upstream test harness; L3 must run affected tests.
12. Validate one real local-model task end-to-end with no hardcoded solution.
13. Establish actual DEV retrieval metrics, per-task false negatives/false positives.
14. Improve retrieval/resolver/context packing on VALIDATION and preserve ablation table.
15. Run larger valid paired coding DEV experiment, explain failures.
16. Freeze configs and release untouched TEST tasks; execute full A/B with usable model(s).
17. Build independent scoring and separate report/CSV exporter, re-verify hashes.
18. Replace FastAPI fake RCIR and interpreter paths with shared actual services.
19. Bind minimal HTML UI to valid run APIs, test responsive layouts and proof links.
20. Finish ERPNext feature closure and incrementally prove real upstream behavior for selected verticals.

---

# 14. Response required from the IDE agent when work finishes

Return a concise final status table, without replacing it with marketing:

| Area | Before | After | Evidence |
|---|---|---|---|
| Benchmark harness | Current known flaw | New measured outcome | code diff + unit tests |
| RCIR retrieval | DEV context reuse | fresh exact-index retrieval | index and query trace |
| Live A/B validity | historical 3/5 | actual N | trial manifests |
| Agent task success | historical 0/5 | actual N | real patches and tests |
| Input/total provider tokens | +1.68% historical exploratory input | current valid comparable result | per-turn provider records |
| Backend live RCIR | cached scorer | actual index query | request/trace |
| Interpreter | staged cells/hardcoded phases | actual parsed `.poly` flow | receipts/events |
| ERPNext | source mapping + local verticals | real independently verified coverage/parity subset | upstream test outputs |
| UI | minimal app exists | cleaned and data-bound | browser tests |

Then list any **remaining FAIL/INCONCLUSIVE/BLOCKED** findings by severity and actual reason. Include commands to reproduce and open each evidence CSV/JSON via working local API routes. If the claims cannot be supported, keep the system labeled as an advanced prototype rather than claiming production readiness.

**Final instruction:** Fix and measure first. Do not hide failed coding tasks, timeouts, excess context or negative token deltas. Do not revise hidden benchmark targets just to make the report green. A truthful improvement of 10-30% with equal or better task success is more useful than a fabricated 90% saving. No UI feature compensates for an invalid benchmark.
