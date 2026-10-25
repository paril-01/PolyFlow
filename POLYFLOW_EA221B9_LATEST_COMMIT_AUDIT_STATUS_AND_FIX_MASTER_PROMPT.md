# POLYFLOW / RCIR — LATEST COMMIT AUDIT, ACTUAL STATUS & CORRECTIVE MASTER PROMPT

**For:** AntiGravity IDE coding agent / independent implementing engineer  
**Audited repository:** `https://github.com/paril-01/PolyFlow`  
**Audited HEAD:** `ea221b91890047d101ebd5a6f8f3a4c2457faeb2` (`benchmark fixes`)  
**Parent:** `4c8505d122f078b3e288551ea6c80c942d8521b5`  
**Audit date:** 2026-10-10 (Asia/Kolkata)  
**Audit basis:** GitHub HEAD/parent comparison, direct source inspection of critical production/benchmark components, existing reports and test source, and remote status query. **No new live Ollama/Nextcloud benchmark was executed by this audit.**  
**Purpose:** Deliver a truthful project progress snapshot plus a specific, source-directed implementation program to produce *reproducible, successful, evidence-backed* end-to-end tests.

---

## 0. Read this first: implementation rules

You are an expert engineering agent, not a report-writing agent. **Make actual source fixes and run real tests**, preserving user data and existing architecture. Do not fake results, pad reports, copy historical metrics into new runs, inject synthetic success events into the backend, or add a new UI instead of repairing execution.

1. Check out the exact HEAD above, confirm repository clean/dirty state and commit. If HEAD has changed, record differences and target the current head without blindly overwriting newer changes.
2. **Before edits** create an evidence-only `reports/EA221B9_PRE_FIX_FACTS.md`: root SHA, target SHA, Python/PHP/Composer/Ollama availability, precise existing test outcomes, and existing run provenance. Mark missing evidence **NOT_MEASURED**.
3. Implement changes in the order listed; do not bypass a blocking failure by weakening a test or softening an error to a warning.
4. Do not claim an RCIR efficiency win before BOTH arms of several independent *successful* coding-task pairs pass the same behavioral acceptance oracle.
5. Distinguish a unit test passing from a live benchmark, a source graph from delivered code, a syntax check from behavioral regression, a .poly feature inventory from a full ERPNext replacement, and a simulated UI demo from a real native execution trace.
6. Keep the default/no-paid-external-services requirement; run with local tools where feasible. Missing toolchains must yield a setup error, not silently synthesized results.
7. Preserve backward compatibility with validated components and recorded historical runs. Historical immutable artifacts are read-only; produce new run IDs rather than rewriting old numbers.
8. Do not force a predetermined benchmark score. If results are poor after fixes, report precise failure causes, costs, and the next experiment.

**Final completion means:** real source-backed RCIR context, correct independent worktrees, strict true behavioral checks, full raw telemetry, no mixed-run data, passing negative/adversarial tests, and at least one independently verified nontrivial agent change before any broad performance claim.

---

# PART I — PROJECT STATUS: WHAT EXISTS, WHAT HAS ACTUALLY BEEN ACHIEVED

## 1. Latest commit delta (confirmed from GitHub compare)

**New HEAD `ea221b9` is one commit ahead of `4c8505d`; 13 changed files.** Significant updated files:

- `experiments/benchmark_core/evaluator.py`
- `experiments/benchmark_core/isolation.py`
- `experiments/benchmark_core/metrics.py`
- `experiments/benchmark_core/models.py`
- `experiments/benchmark_core/pairer.py`
- `experiments/rcir_v8_5/agent_tasks/verify_regression.py`
- `orchestrator/agent_loop.py`
- `orchestrator/tools.py`
- `rcir/src/rcir/context/provider.py`
- `scripts/run_benchmark.py`
- `tests/test_audit_findings.py` (new)
- `reports/commit_4c8505_baseline_audit.md` (new)
- previously authored audit prompt added to repository.

**Important:** the latest commit did **not** include a newly produced real benchmark run result/paired trial artifact in the compared files. GitHub combined commit statuses were empty, and the connector's PR-scoped workflow lookup returned no runs; these observations **do not establish CI passed or failed**.

## 2. Achieved implementation versus experimental proof

| Layer | Implemented in source / present | What the evidence supports | Remaining status |
|---|---|---|---|
| **Feature-centric PolyFlow / `.poly`** | Canonical `.poly` parser and AST, contracts, schema/source/link metadata; feature closure extraction and Frappe/ERPNext adapter | Working structural representation and source organization exist in code. Inventory/coverage claims require checking against immutable source/reports. | **Architecture implemented; full ERPNext behavior parity not established.** |
| **Custom interpreter** | `PolyCellRuntime` with host-language cell execution; parser used in showcase; execution events/receipts | A native cell-runtime implementation exists; showcase still injects example JavaScript/Python business cells and reports fallback rather than executing the actual parsed feature DAG. | **Partial execution proof; exact feature-to-runtime integration unfinished.** |
| **RCIR indexing/ASG-style graph** | Canonical entity registry, graph extraction, typed edges, ranking, context planner/compiler; PHP/Nextcloud adapters | Historical v8.3 committed report cites **12,621 entities, 143,225 edges**. Those are **historical report numbers**, not independently rerun statistics for this HEAD. | **Graph and retrieval machinery implemented; graph-to-real-path contract still suspect.** |
| **Live RCIR provider** | Compiler now instantiated with `ContextCompiler(repo_root=target_repo)`; graph hash and optional target check; per-task session reset; stub-only rejection | These are genuine code-level improvements over `4c8505d`. | **Not yet reliable end-to-end:** graph identifiers can still be mistaken for source paths and graph metadata checks are optional. |
| **Agent loop / Agent Pool** | ReAct loop, tools for inspect/search/edit/patch/test/context, evidence-oriented trial runner. The multi-agent roles are part of broader PolyFlow design/showcase. | Actual tool-calling implementation is present. **Do not conflate the four-role conceptual Agent Pool diagram with independent demonstrated maker/reviewer/rectifier/gatekeeper runtime traces.** | **Tool and safety improvements; real task success remains the decisive missing proof.** |
| **Benchmark harness** | Isolated worktrees, typed trials, per-replicate pairer, provider token records, L0/L1/L2/L3 schema, CSV/JSON exports | Structural fixes to 7-tuple pairing and terminal statuses made at HEAD. | **Scientific validity still blocked by oracle semantics, context resolution, dry-run false passes and missing new live successful pairs.** |
| **Showcase / evidence API** | FastAPI and UI, run/proof APIs, artifact exports | Can visualize architecture and historical data. | **UI still contains stale fallbacks and simulated scores/receipts in some paths.** |
| **CI / unit regression tests** | Existing Python/React CI workflow and new `tests/test_audit_findings.py` | New tests were added. The repository report claims **17 passed** at *previous* commit `4c8505d` for benchmark-integrity tests, **not an independently observed HEAD result**. | **Latest HEAD CI outcome unverified by this audit.** |

### Historical benchmark evidence, not a claim about latest HEAD

Committed earlier `run_20261009_blind_verified/exports/paired_token_usage.csv` and prior audit documented **5 task pairs**, **3 valid completed pairs**, **2 timeout-affected pairs**, and **0 both-successful coding-task pairs**. The **+1.68% median input-token savings** is an exploratory median over valid comparisons, *not successful-task efficiency*. This audit has **not** established a new success percentage or live token gain for `ea221b9`.

### Plain-language progress conclusion

**PolyFlow is beyond an architectural prototype:** the `.poly` representation, interpreter engine, RCIR graph/ranker/compiler, agent tool loop, experiments, evidence APIs and showcase are real source modules. However, it is **not yet defensible to call the integrated system an empirically validated efficient coding agent**. The missing milestone is a trusted A/B experiment where RCIR supplies actual target-file source spans and the coding agent produces a correct patch that independently passes tests. The current priority is engineering validation, **not further UI work**.

---

# PART II — NEW HEAD: CONFIRMED IMPROVEMENTS (DO NOT UNDO)

1. **Worktree/target label correction:** `WorktreeManager.verify_target_checkout()` now returns the pinned SHA if the pinned object exists even when source HEAD differs. Preserve honest recorded target revision. Improve its behavior per P0-07 below.
2. **Real compiler root:** `LiveRCIRContextProvider` now constructs `ContextCompiler(repo_root=self.target_repo)` instead of the previous unrooted compiler.
3. **Context session reset:** `compile_task_context()` calls `reset_session()` to avoid a major source of cross-task seen-entity leakage.
4. **Stub-only validation:** Rejects a context package where no entry claims an existing source-backed span.
5. **More precise pairing:** `pair_trials()` now groups exact 7-tuples when trial metadata supports it and marks duplicate/incomplete arms.
6. **Terminal taxonomy:** Added `TRIAL_BUDGET_EXHAUSTED` and distinct invalid-context/setup statuses.
7. **Verifier taxonomy:** `CheckStatus` distinguishes PASS, FAIL, SKIPPED, NOT_MEASURED, SETUP_ERROR; L0 negative-control code added.
8. **Tool execution:** Changed `run_command` to `shell=False` and initial command allowlist; Git status/diff used more broadly.
9. **Runner:** Added `--dry-run`, `--verify-only`, trial `try/finally`, manifest hashes and raw output writes.
10. **Regression-focused test file:** `tests/test_audit_findings.py` added with issue-specific unit tests.

These improvements are **code changes, not passing live benchmark evidence**. Build on them rather than recreating them.

---

# PART III — OPEN FINDINGS AT `ea221b9` (PRIORITIZED)

Status tags: **CONFIRMED SOURCE** = supported by directly reviewed code; **VERIFY RUNTIME** = high-risk consequence requiring actual execution; **UNMEASURED** = result not provided. Fix by behavior, not by renaming a status.

| ID | Severity | Area / file(s) | Fault and precise consequence | Classification |
|---|---|---|---|---|
| P0-01 | BLOCKER | `rcir/src/rcir/context/provider.py` | `retrieve()` synthesizes file paths via `canonical_target.split('::')[0].replace('php://','')` instead of graph node source metadata; PHP canonical namespaces aren't repository-relative paths. Rooted compiler can still return `SOURCE_UNAVAILABLE` and no useful source spans. | CONFIRMED SOURCE |
| P0-02 | BLOCKER | same + canonical registry | Registry constructor only populates `alias_to_uris`; it does not `register()` actual entity objects. `registry.resolve()` expects `entities[uri]` for disambiguation. Ambiguous aliases can break; unregistered target loses actual source metadata. | CONFIRMED SOURCE |
| P0-03 | BLOCKER | same | `retrieve()` emits a synthetic `entity_match='exact'` target for unverified symbol, uses `if symbol in tgt` substring edge matching; can retrieve the wrong entities and label them exact. | CONFIRMED SOURCE |
| P0-04 | BLOCKER | `scripts/run_benchmark.py` + `provider.py` + `isolation.py` | RCIR compiles snippets from parent target checkout which may be **different** from pinned trial worktree. Graph target SHA check is optional if metadata absent, so task context may refer to a different revision. | CONFIRMED SOURCE |
| P0-05 | BLOCKER | `evaluator.py` | L0 negative control treats **any nonzero** verifier exit as defect reproduced (could be missing dependency/import/setup error); `evaluate_worktree()` accepts `L0 SKIPPED` as sufficient. Broken or absent L0 can lead to false acceptance. | CONFIRMED SOURCE |
| P0-06 | BLOCKER | `verify_regression.py` + `evaluator.py` | L3 remains PHP syntax scanning, returns exit zero after PHP lint, then evaluator marks L3 PASS. This is not behavioral regression. | CONFIRMED SOURCE |
| P0-07 | BLOCKER | `scripts/run_benchmark.py` | `--dry-run` prints success and exits zero when RCIR init/retrieval fails; `--target-sha` argument not applied by worktree manager; `--target` is mostly display-only; `--verify-only` selects first task and hardcodes modified file, without validated L0. | CONFIRMED SOURCE |
| P0-08 | BLOCKER | `run_benchmark.py`, `task_loader.py`, `evaluator.py` | Public agent tasks and hidden evaluator both read the same `test_design.json` path; `hidden_oracle_sha256=tasks_sha256`; physical blind-oracle separation is not implemented. | CONFIRMED SOURCE |
| P0-09 | BLOCKER | `run_benchmark.py`, `rcir/context/provider.py` | Direct standalone CLI inserts repo root, not `rcir/src`; `from rcir.context.provider ...` may depend on editable install/PYTHONPATH/pytest `tests/conftest.py`. CI lacks clean-venv full CLI smoke. | VERIFY RUNTIME |
| P1-01 | HIGH | `rcir/context/provider.py` | `reset_session()` occurs in `compile_task_context()` but shared provider persists across all trials; query caches/trace and current source root remain shared. Reset alone is weaker than new provider per trial. | CONFIRMED SOURCE |
| P1-02 | HIGH | `provider.py` | Stub-only rejection only asks that **one** `SOURCE_SPAN` entry is present. Other entries can remain summaries/stubs, and no explicit snippet line/content hash verification occurs at delivery. | CONFIRMED SOURCE |
| P1-03 | HIGH | `orchestrator/tools.py` | `shell=False` + executable allowlist is not a sandbox: `python -c`, `python -m`, Git subcommands or installer script flags can perform arbitrary side effects. Security boundary still open. | CONFIRMED SOURCE |
| P1-04 | HIGH | `orchestrator/tools.py` | `get_git_diff()` uses `git diff HEAD`, which omits untracked files; `get_modified_files()` may count them, so accepted trials can have nonempty modification list but empty/incomplete patch evidence. Rename/status parsing also needs robust handling. | CONFIRMED SOURCE |
| P1-05 | HIGH | `run_benchmark.py`, `TrialKey.to_string()` | Run ID uses local time to nearest second; `run_dir.mkdir(exist_ok=True)` allows accidental collision/overwrite. Trial IDs truncate model name and source SHA; risks ambiguous identity in distributed runs. | CONFIRMED SOURCE |
| P1-06 | HIGH | `run_benchmark.py` | Invalid setup/RCIR retrieval branch records are appended in memory but **not written** to per-trial raw artifacts. Unexpected exception can skip final run manifest; cleanup alone is insufficient. | CONFIRMED SOURCE |
| P1-07 | HIGH | `scripts/run_final_benchmark.py` | Still prints hard-coded architecture/context/agent gate statuses and does not execute live A/B benchmarks. This entrypoint can mislead during demo. | CONFIRMED SOURCE |
| P1-08 | HIGH | `showcase_app/backend/services/rcir_service.py` | Nominal live API invents `score=1.0-i*.08`, hardcodes repo file count, and silently falls back to saved ranked candidates if live fails. | CONFIRMED SOURCE |
| P1-09 | HIGH | `showcase_app/backend/services/benchmark_service.py`, `api/proofs.py` | Missing run metrics replaced by 10/3/0/+1.68%; a requested run's CSV may silently fall back to global showcase, and `/runs/{id}/proofs` reads global registry. | CONFIRMED SOURCE |
| P1-10 | HIGH | `scripts/build_showcase.py`, `scripts/build_run_exports.py` | Showcase copying lacks strict manifest digest verification and atomic publication. Legacy exporter may write unrelated historical values. | CONFIRMED SOURCE |
| P1-11 | HIGH | `run_benchmark.py`, `models.py`, `pairer.py` | Exact match pairing exists, but `TrialResult` does not receive `key=key`; fallback comparator infers defaults and hardcoded experiment version. Add explicit canonical identity, enforce uniqueness before pairing. | CONFIRMED SOURCE |
| P1-12 | HIGH | `run_benchmark.py`, `orchestrator/agent_loop.py` | `runner.run(...)` receives no `test_command`, thus its own success contract is false/conditional; benchmark may call `verified_success` independently. Dual definitions must be explicit and reconciled. | CONFIRMED SOURCE |
| P1-13 | HIGH | `evaluator.py` | No explicit language-specific behavior for non-PHP changes; L1 can mark PASS when no PHP files changed, and L2/L3 scripts are not always explicitly prescribed. Avoid implicit checks/denominators. | CONFIRMED SOURCE |
| P1-14 | HIGH | `.github/workflows/ci.yml`, `tests/test_audit_findings.py` | HEAD introduces more mocked/temporary-path tests, but no observed end-to-end successful Nextcloud agent run or provider-native A/B telemetry. Some tests skip when Nextcloud checkout missing. | CONFIRMED SOURCE / UNMEASURED |
| P1-15 | HIGH | `metrics.py` | `>=3` both-successful pairs is a useful nonzero guard but insufficient for robust generalization, confidence bounds or challenge stratification. Inconclusive must stay inconclusive. | CONFIRMED SOURCE |
| P2-01 | MEDIUM | `showcase_app/backend/services/interpreter_service.py` | `.poly` is parsed, but business cells are hardcoded, DAG is count-based, recovery narrated and timings partly fixed. Should separate `DEMO` and measured execution. | CONFIRMED SOURCE |
| P2-02 | MEDIUM | `showcase_app/backend/api/health.py` | Health still has `evidence_status='VALIDATED'` even though health does not validate benchmarks. | CONFIRMED SOURCE |
| P2-03 | MEDIUM | `orchestrator/tools.py` | Revert path invokes broad `git checkout .` and `git clean -fd` on repo root. Restrict destructive operations to validated ephemeral trial worktrees, not user working directories. | CONFIRMED SOURCE |
| P2-04 | MEDIUM | feature closure / ERPNext reporting | Inventory breadth, `@source` linkage, behavioral equivalence and live interpreter execution remain distinct metrics. Avoid converting feature counts into 100% replacement claims. | CLAIM HYGIENE |

**Priority:** Address P0-01 through P0-09 before running expensive local-model benchmarks. Other P1 controls must be resolved before a credible performance headline. P2 demo/UI polish comes last.

---

# PART IV — EXACT IMPLEMENTATION INSTRUCTIONS

## Phase A (P0): True graph entity → source-file binding

### A1. `rcir/src/rcir/context/provider.py`: use graph node evidence, not URI string heuristics

**Current defect to remove:**

```python
file_path=canonical_target.split("::")[0].replace("php://", "").replace("ts://", "")
```

This is not a valid path resolver for PHP namespaced classes/methods. Implement an explicit `GraphEntitySourceResolver` (new module e.g. `rcir/src/rcir/context/source_resolver.py`) with:

- Input canonical `entity_id`, exact graph node metadata, target checkout root, pinned target SHA, optional supported path-normalization rules.
- Output typed `SourceLocation(entity_id, relative_path, absolute_path, sha256, start_line, end_line, resolution_class, graph_hash, target_sha)` or typed `UNRESOLVED` error.
- Use `node['file']`, `node['source_file']`, `node['file_path']` after inspecting actual graph schema. Do not guess `namespace -> path`. If graph has spans, validate numeric bounds; if not, resolve AST span from real file.
- Normalize separators, reject `..`, absolute paths, symlink escapes and references outside root. Assert `Path.is_relative_to(root)` after resolution and realpath.
- Resolve symbol through **registered canonical entities**: `CanonicalEntityRegistry.register(CanonicalEntityID.from_uri(uri, file_hint=graph_node_path, ...))` where metadata is available. If a graph object schema has different fields, implement explicit adapter and schema tests instead of an untyped guess.
- Register full entity and alias mappings, not only `alias_to_uris`. Test ambiguous aliases across two namespaces with different files. Do not choose arbitrary alias on ambiguity.
- Resolve only `static_exact` or explicitly supported inferred edges; when unresolved/inferred, record which fact was not proven.
- De-duplicate candidates by canonical identity and source span; rank using real graph evidence, not synthetic `entity_match='exact'` for unknown target.

**Acceptance:** Given `php://OCP\\Files\\Node::getId` with graph node pointing to `lib/public/Files/Node.php`, returned context quotes real bytes from `lib/public/Files/Node.php`, never a made-up `OCP\\Files\\Node` pseudo-file. Changing source file changes snippet hash or triggers staleness failure. Ambiguous and unknown symbols fail explicitly, not silently select a wrong implementation.

### A2. `RCIRContextProvider.retrieve()`: exact matching and target validation

- Before constructing a candidate, confirm a canonical entity exists in the graph or a unique alias resolves to one.
- Do not set `entity_match='exact'` until exact graph identity has been verified.
- Replace substring membership (`symbol in target`) with canonical endpoint identity matching; support explicitly typed equivalences only after normalized registry resolution.
- Preserve graph edge evidence (edge type, resolution class, extractor version, source location, confidence). Unsupported and dynamic unresolved remain separate statuses.
- Supply the resolved relative `file_path` to each `EvidenceVector` so the `ContextCompiler` gets a real file.
- Reject zero source-backed spans; reject any included context described as `SOURCE_SPAN` when `source_exists=False`, span is unresolved or calculated hash mismatches the current source content.
- If the compiled package contains summaries and source spans, label summaries separately; do not count a summary as a verified code excerpt or include it in source-span precision denominators.
- Ensure rendered token count is calculated from the actual final prompt (including headers/metadata), not merely sum of per-entry snippet approximations. Abort if budget exceeded.

**Proposed tests:**

```text
test_php_canonical_id_resolves_graph_node_file_path
test_ts_entity_uses_source_module_path
test_registry_entities_populated_not_just_alias_sets
test_ambiguous_alias_fails_or_requests_hint
test_unknown_symbol_never_gets_synthetic_exact_match
test_graph_substring_collision_does_not_match
test_source_span_content_equals_file_bytes_at_pinned_commit
test_out_of_root_graph_path_is_rejected
test_missing_node_file_fails_closed
test_source_changed_after_index_marks_stale
test_compiled_budget_includes_rendered_envelope
test_summary_only_context_not_counted_as_source_span
```

## Phase B (P0): Snapshot and graph consistency

### B1. `experiments/benchmark_core/isolation.py`

- Accept `target_sha` as an explicit constructor argument. Avoid global hardcoded SHA inside `create_trial_worktree`; use the resolved exact validated pinned SHA.
- `git cat-file -t <sha>` must show commit; verify full checkout containing `composer.json`, `lib`, `core`, `apps`, relevant test framework. No silent partial copy, new fake git repo, or worktree fallback to PolyFlow root.
- Prefer one **read-only graph/source snapshot** at the exact target SHA and two independent mutable baseline/RCIR worktrees at that SHA. If source checkout HEAD differs from pinned SHA, use a detached read-only pinned worktree for index/symbol resolution.
- Assert `git rev-parse HEAD` for every trial worktree equals manifest target SHA and graph metadata target SHA.
- Cleanup only the trial-specific worktree in a `finally` after all raw evidence is persisted; recover safely from partial clones/worktree creation failure.

### B2. `LiveRCIRContextProvider.__init__()`

- Require graph `target_commit` and `extractor_version`/schema information for **formal benchmark mode**; absence must be `TRIAL_INVALID_CONTEXT` or setup failure, not accepted as a valid index.
- Record `graph_sha256`, source SHA, `index_sha256`, ranker-config hash, exact compile version.
- Create a **new RCIR provider/session per trial**, not one mutable provider for all requests. Keep per-task iterative retrieval session inside each trial only.
- Ensure every source read is from exact frozen target SHA (never accidentally changed by baseline arm or previous RCIR arm).

**Tests:** same hash for both trial arms, mismatch rejects, graph metadata missing rejects in strict mode, no cross-trial seen-entity state, graph file mutated after run setup detected.

## Phase C (P0): Oracle isolation + scientifically correct verification

### C1. Separate public task and private evaluator physically

Current `scripts/run_benchmark.py`:

```python
public_tasks = load_public_tasks(tasks_file)
evaluator = EvaluatorOracle(tasks_file, REPO_ROOT)
hidden_oracle_sha256 = tasks_sha256
```

Replace with independent paths/ACL boundaries:

- `--tasks experiments/benchmarks/public/<split>.json` supplies only prompts, public affected-area hints and task scope.
- `--oracle-dir experiments/benchmarks/private/<split>/` opened only by a verifier process in a read-only restricted execution environment (not mounted in agent tools/worktree).
- Public tasks must never expose hidden tests/gold patches, hidden script paths, assertions or acceptance details to the model.
- Fail on absent oracle, mismatch task IDs, duplicate task IDs, incomplete split metadata or oracle tasks that could leak into public task descriptions.
- `RunManifest.hidden_oracle_sha256` and `task_manifest_sha256` MUST differ when inputs differ; each computed from the distinct actual bytes.
- L0 should operate on a clean pinned snapshot **before any edits** for each task (may cache outcome only with exact task+SHA+oracle hash).

### C2. `evaluate_negative_control()` must prove a real failing assertion

Non-zero is NOT sufficient. Classify:

- Expected assertion failure = **L0 PASS** (target issue reproduced).
- Script crash, missing dependency, import error, missing extension, invalid command, timeout, permission error, PHP unavailable = **SETUP_ERROR** or **NOT_MEASURED**, never PASS.
- Unedited baseline passes behavior test = **L0 FAIL** (task is ineligible / already solved, unless explicitly a feature-add task with a different reproducible validity oracle).
- Missing L0 script/criteria = **L0 NOT_MEASURED/SKIPPED**, and **cannot satisfy** a strict accepted benchmark.
- Record stdout/stderr/exit code, selected assertion/test IDs, exception class and test environment version.

Modify `evaluate_worktree()` acceptance to require `l0_status == CheckStatus.PASS` for regression-repair tasks, not `PASS or SKIPPED` (provide separately justified task-type exceptions only with oracle-defined policy).

### C3. L1 / L2 / L3 separation must be real

- **L1** = `php -l` or language-appropriate syntax/type check, with explicit timeout and error status.
- **L2** = independently runnable targeted behavioral test that demonstrates required change, fails on clean tree, passes on changed tree.
- **L3** = genuine relevant upstream test runner (e.g. pinned Nextcloud `phpunit`/appropriate Composer test target with verified dependencies); **never** delegate to `verify_regression.py` that only repeats `php -l`.
- `verify_regression.py` may remain the **syntax smoke** helper, but return `L3_NOT_MEASURED` when no behavioral regression command configured. Exit 0 must not imply upstream tests ran.
- For unsupported environment, status is setup error, and no acceptance. Keep log IDs and coverage scope.
- Ensure the acceptance oracle checks the intended functional change, not an unrelated patched file or a dummy diff.

**Tests:** intentionally broken import cannot pass L0, skipped L0 cannot approve, lint-only cannot pass L3, L2 no-op patch fails, missing PHP/Composer fail setup, altered tests themselves cannot earn acceptance, actual behavior regression causes rejection, all L3 commands logged exactly.

## Phase D (P0/P1): Honest benchmark runner and trial identity

### D1. `scripts/run_benchmark.py` CLI must actually perform what flags claim

- Parse and validate `--target`, `--target-sha`, `--tasks`, `--oracle-dir`, `--model`, `--provider`, `--replicates`, `--turn-budget`, `--run-root`, `--mode`, `--dry-run`, `--verify-only`, `--task-id`, `--worktree`.
- A `--dry-run` success requires: pinned full checkout, graph metadata valid and source spans from pinned checkout, public/hidden isolation, local provider connectivity (or explicitly `SKIPPED_PROVIDER` if requested), PHP/Composer/targeted test availability and negative control viability. If any mandatory stage fails, exit nonzero and print its code. **Never print success after a failed retrieval.**
- `--verify-only` must take explicit task ID and compute actual changed files from worktree; no `public_tasks[0]`, no hardcoded `Response.php`, no fake modifications. Never validate user working-tree outside approved isolated path.
- `--target-sha` must drive worktree creation, graph identity and all manifests rather than merely appear in help output.
- Ensure script works via `python scripts/run_benchmark.py --help` and `--dry-run` in a clean venv without pytest magic. Add packaging (`pyproject.toml` editable install or controlled explicit `sys.path` setup for `rcir/src`, `polyflow-sdk`) and CI smoke.
- Detect local Ollama model availability or missing model; report setup error, not empty successful arm. Record exact provider/model IDs and generation configuration.

### D2. Every trial has a stable globally unique identity

- Use `TrialKey` unchanged for both arms: `(task_id, target_sha, model, provider, seed, turn_budget, replicate, experiment_version)` or keep provider in immutable manifest if a 7-tuple core is required; assert matching provider before pairing.
- Assign `key=key` into every `TrialResult`. Refuse use of hidden fallback default target SHA for modern records; missing identity is `INVALID_SETUP`.
- Distinguish `TRIAL_BUDGET_EXHAUSTED`, `TRIAL_TIMEOUT_PROVIDER`, `TRIAL_TIMEOUT_TOOL`, `TRIAL_INVALID_CONTEXT`, `TRIAL_INVALID_SETUP`, `TRIAL_FAILED_AGENT`, and behavioral/regression failure.
- Use UUID/UTC nanoseconds with exclusive directory creation (`exist_ok=False`) or an atomic create-and-lock; never reuse/collide an immutable run ID.
- Fail/abort if dirty PolyFlow checkout unless user explicitly allows and logs complete patch/hash; never pretend dirty tree SHA represents uncommitted code.

### D3. Independent changeset census and actual tool safety

**`orchestrator/tools.py`:** `shell=False` and executable allowlist alone are NOT a sandbox. Implement structured tool contracts, explicit allowed subcommands, flag policy, working-directory restriction, no arbitrary interpreter `-c`/`-m` nor package-manager arbitrary postinstall scripts without approved isolated mode, optional network isolation, explicit time/memory bounds, capped output.

- Never run arbitrary model-produced `python -c`, `php -r`, `git -c ...`, `npm run ...`, `composer exec ...` on host outside controlled test sandbox. Build trusted test commands at orchestrator side, not from model text.
- Use POSIX-equivalent restrictions on Linux and Windows-safe command quoting; test injection and Unicode/quoted path handling.
- For state changes, derive `modified_files`, added, deleted, renamed and file-level bytes from actual Git status **including untracked files** (git diff HEAD does not include untracked data). For a new file, export a full patch (`git diff --no-index /dev/null <newfile>` or a safe equivalent), record before/after SHA-256 and source path.
- Do not use internal edit backup as the primary change census; log any fallback distinctly and deny accepted benchmark when diff evidence is incomplete.
- `revert_changes` must not call broad `git clean -fd` / `git checkout .` on arbitrary user repositories; only on explicitly tagged disposable benchmark worktrees.
- Persist raw trial even on exception with failure status, traceback classification and partially observed telemetry. Use atomic per-trial JSON writes and `try/finally` cleanup.

### D4. Agent loop consistency and baseline fairness

- `orchestrator/agent_loop.py` must report `agent_workflow_completed` separately from `verified_success` and accurately retain tool-output/status histories.
- Agent `finish` is not test acceptance; only evaluator can decide verified success. Avoid dual contradictory `success` fields; use `AgentLoopResult.agent_completed`, `trial.verification.accepted`, and documented semantics.
- Both A/B arms use same base model/version, seed where provider supports it, turn budget, timeout, prompts other than explicit RCIR context, tool capabilities, test command exposure rules and stopping policy.
- Record original task prompt, RCIR context source spans/hash, per-turn provider request/response token records, timeout, edits, commands executed, denial reason and final patch.
- If failures cluster around small models, do not silently swap model midrun. Add a second **predefined** local model stratum if hardware permits and report results separately.

## Phase E (P1): Pairing, metrics and experimental design

### E1. `experiments/benchmark_core/pairer.py`

- Preserve fixed 7-tuple matching, but require complete explicit trial identity (`key`). Duplicate/missing arms should be retained in diagnostics and **never** counted as valid.
- Verify same task specification hash, target, provider, model, prompt-policy, turn budget, seed and oracle hash across both arms.
- Mark any RCIR invalid-context arm as `INVALID_CONTEXT_PAIR` and exclude it from credible token-efficiency denominators.
- Include task success and failure causal taxonomy; don't silently discard failures from success rate. Maintain an intention-to-treat success denominator for all attempted eligible tasks and separate complete-case efficiency denominator.

### E2. `metrics.py`

Report at minimum:

1. All trials / planned trials, missing trial count, complete pairs, invalid/timeout/budget-exhausted pairs.
2. Baseline successful tasks / attempted, RCIR successful tasks / attempted, BOTH-successful count; paired discordance table: both pass, baseline-only, RCIR-only, neither.
3. Provider-native *input*, *output*, *total* tokens, and latency medians with provenance and uncertainty intervals; include cached tokens if provider supports it.
4. Primary cost efficiency over **both-successful** pairs, only when sample/gates are preregistered, otherwise `INSUFFICIENT_SAMPLE` or `NOT_MEASURED`; never rebrand exploratory 1.68% as improvement on successful work.
5. Retrieval metrics: target-file recall, *true* critical source-span recall at budget, top-k precision, graph-edge precision on independent oracle, context token overhead and unresolved-source counts.
6. Failure categorization by task, replicate, subsystem; at least a few distinct difficulty tiers and repositories when possible, but never cross-pollinate DEV / held-out TEST.

Publish uncertainty even at small N. `len(successful_pairs) >= 3` is only a minimal visibility gate, not proof of robust generality. Clarify any statistical significance or lack thereof.

### E3. Run matrix

Execute stages only after above controls:

- `E0`: 100% local deterministic unit/negative/security tests.
- `E1`: realistic source-backed RCIR retrieval on pinned Nextcloud target, report resolved versus unresolved source spans.
- `E2`: real retrieval context quality on multiple actual changed tasks, under 2k/4k/8k token budgets.
- `E3`: single known solvable task for baseline and RCIR, independent L0-L3 gates, full source trace and exact diff.
- `E4`: 5 diverse tasks x minimum 2 replicates (10 complete A/B pairs), more only after proving there are no setup failures; include one previously failing hard task.
- `E5`: held-out TEST, preregister scoring and budgets before opening hidden evaluator, use immutable run folder and frozen selections.

**STOP** if `E1` lacks source spans or `E3` has no accepted patch. Fix root cause rather than spinning model cycles for another glossy report.

## Phase F (P1/P2): Honest evidence backends, interpreter and showcase

### F1. Source-of-truth run APIs

Files:
- `showcase_app/backend/services/benchmark_service.py`
- `showcase_app/backend/services/rcir_service.py`
- `showcase_app/backend/api/proofs.py`
- `showcase_app/backend/services/evidence_registry.py`
- `scripts/build_showcase.py`
- `scripts/build_run_exports.py`
- `scripts/run_final_benchmark.py`

Changes:

- Require real run ID, verified manifest and `results/metrics.json`; if missing, return 404/`NOT_MEASURED` with status, never default 10/3/0/+1.68.
- `/runs/{run_id}/pairs.csv`, `/runs/{run_id}/retrieval.csv`, `/benchmarks/{run_id}/pairs.csv`, proofs and summary MUST resolve only files under that exact verified run. Missing file is 404, never global showcase CSV.
- RCIR `/queries` must emit actual ranker score breakdowns and real source spans; no artificial `1.0 - 0.08*idx`, fixed repo file count or silently loaded `rcir_pipeline.json` as if live.
- Tag historical snapshot endpoints `DEMO/HISTORICAL`, not `LIVE`; prevent exporting demo records into benchmark run directories.
- `build_showcase.py --run-id <ID>` verifies SHA-256 for every source artifact against sealed manifest/proof index; refuses partial, missing or tampered run; writes snapshot atomically and includes source run ID.
- `run_final_benchmark.py` should accept explicit `--run-id` for verification or `--execute` for genuine benchmark. Unit tests alone cannot print “context gate satisfied” or historic completed-task counts.
- `/api/health` communicates process health only; report evidence state separately and sourced to selected run.

### F2. Interpreter

`showcase_app/backend/services/interpreter_service.py` currently calls `PolyParser`, but then runs hardcoded JavaScript/Python examples (`client_adapter`, `schema_guard`, `tax_calculation`), counts `sources+schemas` as scheduler nodes, and announces tax fallback without executing a recovery function. Fix as follows:

- Two explicit service modes: `DEMO_SCENARIO` (current scripted example, unmistakably labeled) versus `REAL_FEATURE_EXECUTION` (read validated `.poly` selected by feature ID, parse exact source, compile dependency DAG, execute actual declared cell code, verify schemas, merge outputs, apply real error policy).
- A critical tax/ledger failure must **fail closed**; do not silently treat negative tax as a valid degraded accounting result.
- For recoverable optional cells, implement and actually run a declared fallback and log its output.
- Use measured `perf_counter_ns()` for parse/validation/schedule/cell/fallback/merge; exclude artificial sleep; receipts hash source file + config + actual outputs + toolchain versions. SHA-256 receipt is an integrity digest, **not automatically a signed receipt**.
- Tests must cover happy path, invalid AST, schema rejection, cyclic DAG, missing runtime, timeouts, critical failure, optional fallback and tampered receipt.

### F3. Feature closure and agent pool positioning

- Report `extracted native features`, `source-linked features`, `verified sample executable features`, and `full behavioral parity` separately for ERPNext.
- If agent pool (Maker → Reviewer → Rectifier → Gatekeeper) is depicted as a live product, provide actual corresponding agent traces and handoff artifacts. If only ReAct agent loop executed, label the agent pool as a proposed orchestration layer in presentation and API.
- Keep existing presentation/architecture UI. Do not divert fixes into stylistic redesign.

---

# PART V — REQUIRED TEST AND ACCEPTANCE MATRIX

Create or extend tests under `tests/benchmark_integrity/`, `tests/test_audit_findings.py`, `tests/integration/`, `tests/security/`. Every issue must get a regression test that **would fail before the fix and pass after it**. Re-run all existing tests. Don't weaken tests or mark them `xfail` solely to get CI green.

| Test ID | Exact intended assertion |
|---|---|
| T01 | Canonical PHP symbol yields `lib/...php` real path from graph metadata; not namespace-as-path. |
| T02 | Registered graph entity appears in registry `.entities` and resolves an alias without KeyError. |
| T03 | Two same-short-name entities produce an explicit ambiguity requiring hint. |
| T04 | Unknown symbol never receives `static_exact`/`entity_match=exact`. |
| T05 | Substring overlaps in edge IDs do not create false direct edges. |
| T06 | Source excerpt bytes match expected pinned Git object/source file SHA. |
| T07 | Missing file, malicious `../`, symlink escape, graph/SHA mismatch fail closed. |
| T08 | Graph without target SHA rejected in formal benchmark mode. |
| T09 | Same task two arms read identical pinned sources while edits remain separate. |
| T10 | Fresh RCIR provider per trial: no `seen_entities` bleed, same initial context. |
| T11 | Stub-only / summary-only context invalid and excluded from efficiency. |
| T12 | Mixed context tracks valid-span versus summary token metrics separately. |
| T13 | Final prompt token envelope always within exact configured budget. |
| T14 | Baseline test oracle is physically inaccessible to model/agent workspace. |
| T15 | L0 negative control distinguishes assertion fail from module/import crash. |
| T16 | L0 skipped/not measured cannot yield accepted repair trial. |
| T17 | Clean pristine target passing behavior test invalidates task. |
| T18 | L1 syntax-only runner never reports L3 PASS. |
| T19 | Real upstream regression command is executed and logged for L3. |
| T20 | L3 unavailable / PHP missing / Composer setup missing causes non-PASS. |
| T21 | `--dry-run` exits nonzero on failed RCIR retrieval. |
| T22 | `--target-sha` actually changes verified selected commit (or fails on mismatch). |
| T23 | `--verify-only --task-id X` uses actual changed files; no hardcoded Response.php. |
| T24 | Direct `python scripts/run_benchmark.py --help` works in clean venv. |
| T25 | 2 replicates x 2 conditions produce exactly two distinct complete pairs. |
| T26 | Wrong model/seed/target/turn budget or duplicate arm never forms valid pair. |
| T27 | Budget exhaustion stays distinct from provider/tool timeout. |
| T28 | `run_command` denies `python -c`, unsafe subcommands and path escapes. |
| T29 | Legitimate trusted PHP syntax test command executes with shell=False. |
| T30 | Untracked added file is counted, hashed and exported in full patch evidence. |
| T31 | Renamed/deleted files and paths with spaces are censused correctly. |
| T32 | Repo revert cannot delete arbitrary user data outside ephemeral worktree. |
| T33 | Run ID collision is rejected; manifest and artifacts cannot overwrite. |
| T34 | Every failed arm has a raw trial JSON and fatal error classification. |
| T35 | Missing run metrics yields 404/NOT_MEASURED, not 10/3/+1.68. |
| T36 | Wrong run ID cannot receive another run's CSV or proofs. |
| T37 | Proof/export tampering blocks showcase publication. |
| T38 | API live retrieval returns actual ranker score/source and no snapshot fallback. |
| T39 | `.poly` real mode executes parsed cells, not hardcoded demo functions. |
| T40 | Critical tax failure blocks; optional failure executes real fallback. |
| T41 | Minimal real RCIR A/B task passes independent L0-L3 with file hashes/diffs. |
| T42 | Missing genuine coding success keeps primary token-efficiency NOT_MEASURED. |

**Test fixture guidance:** Use small **real temporary Git repositories** for E0 path/identity/negative/security tests. Use an actual pinned Nextcloud checkout for E1–E5. Tiny isolated test fixtures are appropriate for correctness tests, but are not evidence that Nextcloud enterprise performance is solved.

---

# PART VI — IMPLEMENTATION ORDER, CHECKPOINTS AND EXECUTION COMMANDS

## Ordered tasks (implement exactly, make commits by checkpoint)

1. **G0** Verify HEAD/source environment; document pre-fix truth, limitations and dependency availability.
2. **G1** Fix canonical graph entity→source-path and registry mapping; real snippet and hash tests.
3. **G2** Enforce graph/source/target SHA consistency and per-trial isolated provider.
4. **G3** Physically isolate oracle, make L0 assertion-specific and mandatory for repair tasks.
5. **G4** Replace pseudo L3 with real upstream test runner and separate L1/L2/L3 outputs.
6. **G5** Fix runner dry-run/verify-only/target-sha/CLI and stable immutable run IDs.
7. **G6** Harden command sandbox, untracked/rename change census and raw trial persistence.
8. **G7** Enforce full pair identity and separate E1 retrieval vs E3 task success metrics.
9. **G8** Run one nontrivial solvable end-to-end task in both arms, show real diffs/logs.
10. **G9** Scale to 5 diverse tasks x 2 reps on local toolchain, publish confidence/validity/failure table.
11. **G10** Repair run-scoped evidence API and only sync verified run artifacts to UI.
12. **G11** Complete genuine `.poly` interpreter integration or label demo explicitly.
13. **G12** Freeze held-out test and produce final technical report and demo-ready proof index.

## Suggested commands (adapt package/tool paths after inspecting repository)

```bash
# Identity and environment (no claims until actually executed)
git rev-parse HEAD
git status --short
python --version
php -v
composer --version
ollama list

# Existing regression tests
python -m pytest tests/benchmark_integrity -q
python -m pytest tests/test_audit_findings.py -q
python -m pytest tests/test_polyflow.py -q
python -m pytest tests/test_backend_proof_server.py -q

# Must be independently invocable after packaging fix
python scripts/run_benchmark.py --help
python scripts/run_benchmark.py --target nextcloud --target-sha da57df078d0808a7235a0177bd99d23c010b472e --mode dev --dry-run

# Run after prerequisites and independent oracles are installed
python scripts/run_benchmark.py \
  --target nextcloud \
  --target-sha da57df078d0808a7235a0177bd99d23c010b472e \
  --mode dev \
  --tasks experiments/benchmarks/public/dev.json \
  --oracle-dir experiments/benchmarks/private/dev \
  --provider ollama \
  --model qwen2.5-coder:1.5b \
  --turn-budget 12 --replicates 2
```

The command containing `--oracle-dir` describes the **required post-fix CLI**, not a promise that current HEAD accepts it. If `qwen2.5-coder:1.5b` cannot solve selected tasks, record exact failure. Test a stronger *preselected* local model under a separately frozen stratum and state memory/runtime tradeoffs. No paid data requirement.

## Gate criteria

- **G0 environment:** target Git commit and toolchains recorded; missing prerequisites surfaced as SETUP_ERROR.
- **G1 RCIR:** at least one real independent `SOURCE_SPAN` with validated current bytes/hash for every valid RCIR trial; source resolution and ambiguity tests pass.
- **G2 isolation:** public agent cannot access hidden oracle; no cross-arm worktree state and graph hash matches target SHA.
- **G3 oracle:** L0 is a verified expected failing assertion on pristine tree; L2 passes on genuinely modified tree; L3 is upstream behavior, not PHP lint.
- **G4 trial:** nonempty real diff, accepted patch, tool trace, provider-native token accounting, no untracked-file omission.
- **G5 paired:** no hidden extra arm, replicate, seed, target revision mismatch; all expected denominator counts reconcile.
- **G6 evidence:** run-scoped manifest, hash-linked raw files, status/metrics derived from exact run; no global snapshot fallback.
- **G7 performance:** primary efficiency marked `NOT_MEASURED` until qualifying successful pairs exist; only then expose a proper metric with uncertainty.
- **G8 product:** real and illustrative interpreter/showcase experiences clearly separated, no unsubstantiated ERPNext parity claim.

---

# PART VII — MANDATORY FINAL DELIVERABLES

Create the following within the repository:

```text
reports/
  EA221B9_PRE_FIX_FACTS.md
  EA221B9_POST_FIX_CHANGELOG.md
  EA221B9_BENCHMARK_STATUS.md
  EA221B9_REPRODUCTION_GUIDE.md
experiments/runs/<immutable_new_run_id>/
  manifest.json
  raw/<task>/<condition>/<replicate>/trial.json
  raw/<task>/<condition>/<replicate>/patch.diff
  raw/<task>/<condition>/<replicate>/provider_usage.jsonl
  raw/<task>/<condition>/<replicate>/retrieval_trace.json
  raw/<task>/<condition>/<replicate>/verifier_L0_L1_L2_L3.json
  results/trials.json
  results/pairs.json
  results/metrics.json
  exports/agent_trials.csv
  exports/paired_token_usage.csv
  exports/retrieved_files.csv
  reports/benchmark_report.md
  proof_index.json
```

Produce report content in this order:

1. **Source and commit integrity:** PolyFlow HEAD, target SHA, graph SHA, oracle SHA, source hash, model/provider, dirty flag.
2. **Change log:** exact files changed, why, behavior before/after, tests for each finding ID.
3. **Unit test actual outcomes:** number run/passed/failed/skipped, exact commands; attach nonempty real logs.
4. **Retrieval quality:** count actual source-backed spans, content hash checks, critical-file recall and unresolved status.
5. **Trial outcomes:** all trial rows and missing arms with error taxonomy; real changed files/diff and verification evidence.
6. **Pairing:** exact keys and all invalid-pair denominators and reasons.
7. **Agent success:** baseline, RCIR, both-successful, neither; confidence/sample limitations.
8. **Token efficiency:** provider-native source, per-turn records, valid vs both-successful metric distinction. If zero both-successful, print `NOT_MEASURED` as the headline.
9. **Feature closure/interpreter:** inventory vs real executable task proof vs unknown parity; UI demonstration disclaimers.
10. **Remaining failures:** explicitly list any unclosed P0/P1 issues, exact reproducible error traces and the next corrective experiment.

End with a short engineering verdict in plain words:

> **Implemented:** [exact modules].  
> **Verified on real tasks:** [task IDs and hashes, or NONE].  
> **Context efficiency on successful tasks:** [measured value with n, or NOT_MEASURED].  
> **Next engineering milestone:** [one specific gate/blocker].

**Stop condition:** Do not declare everything complete just because new unit tests were added or the showcase runs. If a mandatory gate is blocked by missing local Nextcloud/PHP/Ollama/model, emit `BLOCKED_BY_ENVIRONMENT` with exact commands needed to reproduce once locally. Do not invent outputs.

---

# PART VIII — RESEARCH/DEMO HONESTY NOTES

1. **Past graph count:** The committed historical `experiments/rcir_v8_3/reports/canonical_graph_report.md` reports 12,621 entities and 143,225 edges, but does not establish the current `ea221b9` A/B patch success rate.
2. **Past ranking:** A historical v8.5 ranking report contains a validation-selected R0 baseline and limited top-k precision. A higher graph node count or an 'R0 PASSED' report is not proof of coding quality or context savings.
3. **Past 5-task A/B:** 3/5 valid complete pairs, 2 timeout-affected pairs and zero both-successful tasks was the **earlier experiment**, not the newest `ea221b9` result. The +1.68% exploratory token delta must not be marketed as successful-task efficiency.
4. **Latest audit tests:** `reports/commit_4c8505_baseline_audit.md` reports unit test results from the **parent**. Latest HEAD contains a new 452-line finding-test file but no observed fresh live Nextcloud benchmark artifact in commit delta. No automatic inference that all tests passed.
5. **Presentation:** Describe PolyFlow + the interpreter + RCIR + Agent Pool as layered architecture with some real implementations and proof boundaries; explicitly distinguish executed features from feature closure, and agent-pool blueprint from an actually traced role-specialized run.

**A good result is a reliable failure diagnosis plus a fixable path. An unexplained 90% savings number is not a good result.**

