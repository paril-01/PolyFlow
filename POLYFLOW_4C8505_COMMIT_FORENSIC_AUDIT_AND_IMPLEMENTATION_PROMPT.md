# PolyFlow: Commit `4c8505d` Forensic Audit and Benchmark-First Implementation Prompt

> **Use this entire file as the execution prompt in AntiGravity IDE.** This document is a set of direct engineering instructions, not an invitation to write another plan. Execute changes, run real checks, preserve failures, and return file-by-file diffs and evidence.
>
> Audited HEAD: [`4c8505d122f078b3e288551ea6c80c942d8521b5`](https://github.com/paril-01/PolyFlow/commit/4c8505d122f078b3e288551ea6c80c942d8521b5), October 9, 2026 (UTC). Previous commit: `b86acd511ffdee5b834a56e00ab8c1b87d66530a`. Scope: 51 changed files plus relevant call chains in the existing repo.
>
> **Evidence limitation:** This audit independently inspected repository source through GitHub, compared the two commits, and read committed tests/reports. The auditor did **not** run live Ollama, Nextcloud/Frappe containers, a full local repository test suite, or a new benchmark. Where a result is absent, mark it `NOT_MEASURED`, not `PASS`.

---

## 0. Non-negotiable contract

You are the PolyFlow implementation engineer operating INSIDE the actual checked-out repository. The user's immediate goal is a **working benchmark with legitimate, measurable task success and provably useful RCIR context**, not a better-looking dashboard. Repair the code first, run developer diagnostics, then run frozen tests, then publish truthful result artifacts. UI changes happen **last** and only consume verified artifacts.

**Do not** fabricate test success; force a benchmark threshold; relabel `NOT_MEASURED` as zero or PASS; copy a baseline as an after-fix run; alter held-out gold answers to improve apparent scores; replace a live retrieval failure with canned candidate data; reuse previous run metrics in a fresh run; or show `.poly` mapping as verified ERPNext runtime parity. An honest failure is useful data.

**Permissions/constraints:** Prefer free/local tooling; keep platform portable Windows and POSIX; use pinned commits and reproducible manifests; protect hidden evaluators and benchmark integrity; maintain existing APIs wherever feasible; no destructive refactor of PolyFlow, RCIR or the Agent Pool. Everything required must be committed as code, tests, scripts or an honest results report.

**Priority order:** P0 benchmark correctness → P0 RCIR real-source delivery → P0 agent tool and verification correctness → P1 robustness and benchmark methodology → P1 proof/API reliability → P2 interpreter/ERPNext demonstrations → P3 UI presentation polish.

Before making changes, run `git rev-parse HEAD`, `git status --short`, inspect all paths listed in §1, record current exact commit and working-tree state, then baseline-run unit/static tests. Do not blindly discard user modifications. If HEAD differs from audited commit, produce a current delta and adapt surgically. Never silently skip a required test.

## 1. Executive verdict and finding register

**Meaningful progress:** Commit `4c8505d` adds a separate `experiments/benchmark_core/` package, real worktree provisioning, a paired trial runner, a live-provider class, data-models, a cleaner model-tool parser, more integrity tests, and run-oriented API surfaces. It is **not yet sufficient** to prove benchmark gains or genuine source-backed RCIR delivery. A current blind run with accepted edits was not included in the 51 changed files observed.

Legend: `P0` blocks formal results/release; `P1` integrity/operability; `P2` user-facing truth; `P3` polish. `CONFIRMED` = directly visible in source; `REQUIRES_RUNTIME_CHECK` = plausible integration failure requiring a reproducible test before declaring it observed.

| ID | Priority | Status | Exact source | Fault / consequence |
|---|---|---|---|---|
| F01 | P0 | CONFIRMED | `rcir/src/rcir/context/provider.py` | `LiveRCIRContextProvider` calls superclass without `ContextCompiler(repo_root=target_repo)`. `compiler._extract_snippet()` uses a reference-stub path if `repo_root is None`. Can count stub tokens as RCIR delivery. |
| F02 | P0 | CONFIRMED | `scripts/run_benchmark.py` | RCIR init/retrieval exceptions are warnings; the `rcir` trial can run with empty context and `context_provider=None`. It is then reported as if RCIR were an actual arm. |
| F03 | P0 | CONFIRMED | `rcir/src/rcir/context/provider.py` | One `LiveRCIRContextProvider` instance is reused across every trial. `ContextSessionState` remembers entities across tasks/replicates, so later trials can receive different or missing context. |
| F04 | P0 | CONFIRMED | `experiments/benchmark_core/pairer.py` | Pairs keyed by `task_id` only; multi-replicate trials overwrite one another. No exact model/commit/seed/budget matching or duplicate/missing-arm error. |
| F05 | P0 | CONFIRMED | `experiments/benchmark_core/pairer.py`, `scripts/run_benchmark.py` | Hitting turn budget without edits is mislabeled a provider timeout. Failure reasons and valid-pair denominators become corrupted. |
| F06 | P0 | CONFIRMED | `experiments/benchmark_core/evaluator.py` | If L3 is not requested, sets `l3_regression_passed=True` and logs `L3_OPTIONAL_SKIPPED`. Boolean PASS is being used to encode skipped tests. |
| F07 | P0 | CONFIRMED | `experiments/rcir_v8_5/agent_tasks/verify_regression.py` | Exit 0 currently means PHP syntax checks passed, not an upstream regression suite. It also falls back to scanning all PHP files on certain git-status cases. |
| F08 | P0 | CONFIRMED | `experiments/benchmark_core/evaluator.py` | No mandatory pre-edit negative control: targeted test must fail on original pinned revision before accepting a fix. Missing PHP binary, missing changed file, script timeouts and exit codes also need explicit fail-closed statuses. |
| F09 | P0 | CONFIRMED | `experiments/benchmark_core/isolation.py` | `verify_target_checkout` returns current HEAD if pinned object merely exists; actual worktree checks out pinned SHA. `RunManifest.target_sha` may therefore describe a different revision. |
| F10 | P0 | CONFIRMED | `orchestrator/tools.py` | `run_command(..., shell=True)` runs model-originated shell commands outside a defensible sandbox. Also `get_git_diff()` depends on internal edit backups, not an independent git change census. |
| F11 | P0 | CONFIRMED | `rcir/src/rcir/context/provider.py` | Task symbol extraction grabs first CamelCase-like word and registry starts empty; no verified canonical symbol→source path resolution or robust task target. |
| F12 | P0 | REQUIRES_RUNTIME_CHECK | `scripts/run_benchmark.py`, `rcir/src/...` | Standalone script only inserts repo root in `sys.path`; test `conftest.py` inserts `rcir/src`. Verify standalone import works in a clean venv without implicit editable installs. |
| F13 | P1 | CONFIRMED | `scripts/run_final_benchmark.py` | 'Final benchmark' still only runs unit tests + showcase builders, then prints fixed historic gate outcomes. It never invokes `run_benchmark.py` and does not accept a run ID. |
| F14 | P1 | CONFIRMED | `scripts/build_showcase.py` | Header promises hash validation, but implementation only checks existence and copies CSVs. It neither validates any digest nor creates destination `csv` directories explicitly. |
| F15 | P1 | CONFIRMED | `scripts/run_benchmark.py` | `RunManifest` has fields `dirty`, index hash, oracle hash and ranker config hash, but runner leaves defaults; `start_time_utc` is local `datetime.now()` without timezone. |
| F16 | P1 | CONFIRMED | `scripts/run_benchmark.py` | No `try/finally` for worktree cleanup and no per-trial failure persistence until after runner/evaluator complete. Exceptions can leave partial runs and lose evidence. |
| F17 | P1 | CONFIRMED | `experiments/benchmark_core/models.py`, `pairer.py` | `TrialKey` contains commit/model/seed/replicate but `TrialResult` does not carry a comparable tuple; `TrialKey.to_string()` omits model, seed and target SHA. |
| F18 | P1 | CONFIRMED | `experiments/benchmark_core/metrics.py` | Agent gate is satisfied by one both-successful pair; no minimum sample size, task difficulty, per-stratum coverage, confidence intervals or clear distinction among efficiency estimands. |
| F19 | P1 | CONFIRMED | `showcase_app/backend/services/rcir_service.py` | A nominal live retrieval creates artificial candidate scores (`1.0 - 0.08*idx`), assigns tiers by index, hardcodes file count, and silently falls back to a saved example query. |
| F20 | P1 | CONFIRMED | `showcase_app/backend/services/benchmark_service.py`, `api/proofs.py` | A newly requested run can receive hardcoded default stats when metrics are absent; per-run CSV endpoints may silently serve global showcase CSVs; `/runs/{id}/proofs` returns global proof index. |
| F21 | P1 | CONFIRMED | `.github/workflows/ci.yml`, `tests/benchmark_integrity/*` | Useful tests were added, but true RCIR/Nextcloud tests skip if checkout unavailable; pairing tests use only one replicate. CI does not test standalone entrypoint, paired live execution, source-span provenance, or multi-replicate pairing. |
| F22 | P2 | CONFIRMED | `showcase_app/backend/services/interpreter_service.py` | Parser is called, but `has_schema` is unused, 'DAG' counts sources + schemas without scheduling, and executed cells are hardcoded rather than taken from parsed `.poly` content. |
| F23 | P2 | CONFIRMED | `showcase_app/backend/services/interpreter_service.py` | Failure of a tax-calculation cell is displayed as `DEGRADED` with a narrated fallback rather than independently executed contract-approved recovery; durations have a hardcoded minimum and merge durations are literals. |
| F24 | P2 | CONFIRMED | `scripts/build_run_exports.py`, historic `experiments/runs/run_20261009_blind_verified` | Legacy exporter/mirrors retain historical or fixed counts/rows; two competing artifact paths can mix historic with live evidence. |
| F25 | P2 | CONFIRMED | `showcase_app/backend/api/health.py` | Health correctly adds `benchmarks_gate=NOT_EVALUATED_BY_HEALTH`, but retains `evidence_status=VALIDATED` merely for process liveness. |
| F26 | P1 | CONFIRMED | `experiments/benchmark_core/task_loader.py`, `evaluator.py` | Public manifest and private oracle are read from the same `test_design.json` path. Sanitizing prompt fields helps, but is not a genuine evaluator isolation boundary. |
| F27 | P1 | REQUIRES_RUNTIME_CHECK | `rcir/src/rcir/context/provider.py` | Loaded graph has no required `target_commit/index_hash/extractor_version` assertion against the worktree. Stale graph→wrong source revision risk. |
| F28 | P1 | CONFIRMED | `orchestrator/agent_loop.py` | Normal run's `AgentLoopResult.success` requires `test_command`, but benchmark runner does not provide one and computes success independently. This is a split contract that can confuse downstream reporting. |

**Do not equate `fix committed` with `benchmark achieved`.** The repository commit's message does not substitute for a pinned complete run artifact with both-arm success and valid test evidence.

---

## 2. Phase A: fail-closed benchmark bootstrap

### A1. Canonical command/package execution

Touch:
- `scripts/run_benchmark.py`
- `experiments/benchmark_core/__init__.py`
- `pyproject.toml` / editable install metadata (if present)
- `tests/benchmark_integrity/test_cli_bootstrap.py` (new)

Implement a stable project entrypoint using `python -m scripts.run_benchmark` and/or documented `python scripts/run_benchmark.py`, with **absolute imports working from a clean venv**. If an installation step is required, add `pip install -e .` and `pip install -e rcir` with correct package configuration. Avoid hidden reliance on `tests/conftest.py` to alter `sys.path`. Add `--dry-run` to check target repo, pinned SHA, graph, tokenizer, model availability, PHP/composer/phpunit, manifest path, and hidden evaluator before spending inference tokens. Return non-zero for required missing dependencies. Check `--help` without optional LLM/Nextcloud imports if feasible.

### A2. Strict run identity and immutability

Implement `RunContext` generated exactly once with UTC offset-aware timestamp and unique collision-resistant ID. The run manifest must include:

```json
{
  "schema_version":"3.0.0",
  "run_id":"<unique id>",
  "polyflow_sha":"<exact HEAD>",
  "polyflow_dirty":false,
  "target_repo":"nextcloud/server",
  "target_sha":"<ACTUAL CHECKED-OUT WORKTREE SHA>",
  "task_manifest_sha256":"<hash of public task spec>",
  "hidden_oracle_sha256":"<private evaluator bundle hash, never exposed to agent>",
  "graph_sha256":"<graph file bytes>",
  "graph_target_sha":"<graph build source revision>",
  "ranker_config_sha256":"<ranker config hash>",
  "model":"<provider actual model ID>",
  "provider":"<provider name/version>",
  "tokenizer":"<provider/tokenizer identity>",
  "turn_budget":12,
  "replicates":3,
  "run_status":"INITIALIZED | RUNNING | COMPLETED | PARTIAL | FAILED",
  "started_at_utc":"2026-10-09T...Z"
}
```

A failed run never transitions to `COMPLETED`. Persist on each completed trial, not just after all tasks. The frozen input hashes and run manifests must never be retroactively changed. A versioned provenance manifest can be appended separately if derivation artifacts are produced later. No in-place overwrites under a completed run ID; atomic `write temporary + fsync + rename` when possible.

### A3. Pinned full checkout

Touch `experiments/benchmark_core/isolation.py`.

- Choose a single policy: require `HEAD == PINNED_NEXTCLOUD_COMMIT` **or** explicitly allow detached worktrees from a pinned object while returning that pinned SHA as the experiment target. Do not return a different HEAD as the claimed revision.
- Validate full target structure and `composer.json`; check untracked state and submodules where relevant.
- Verify each trial worktree SHA after checkout and ensure it is clean before execution.
- Guarantee **separate clean worktrees** for every `(task_id, condition, replicate, budget)`.
- Do not silently fall back to an incomplete clone; use a complete local clone at exact SHA if `git worktree` is unavailable, record isolation mode and verify parity.
- Worktree name must encode unique tuple hash and be path-safe.
- Cleanup with `finally`. On failure preserve source diff/traces before cleanup, record trial as `INVALID_SETUP` or appropriate explicit failure status.
- If `.git` is a file (normal linked git worktree), do not reject the checkout simply because it is not a directory.

### A4. Actual task/evaluator separation

Touch `experiments/benchmark_core/task_loader.py`, `evaluator.py`, task fixture packaging and access guard.

- Store public tasks separately from private oracle JSON/scripts. Move gold diffs, target answers, hidden checks and relevant datasets outside agent-readable worktree or host sandbox.
- `task_loader` validates typed schema and produces only public task fields.
- Hidden evaluator is loaded in **a separate process after agent execution**, with no readable path from its command tool.
- Test using a malicious agent request (`list_dir`, `inspect_file`, `run_command`) attempting to access answers, private scripts and prior reports. Deny all, and record denial.
- Freeze held-out TEST definitions/hashes; allow retrieval and prompt tuning only on DEV and VALIDATION; never learn from hidden TEST feedback in the development loop.

---

## 3. Phase B: real source-backed RCIR, not decorative context

### B1. Fix the critical compiler root defect (F01)

Touch `rcir/src/rcir/context/provider.py`, `rcir/src/rcir/context/compiler.py` only if necessary.

Replace the unrooted compiler created by `super().__init__(raw_graph=raw_graph)` in `LiveRCIRContextProvider` with explicit pinned target binding:

```python
# Conceptual shape; fit exact installed API, do not paste without confirming signatures.
compiler = ContextCompiler(repo_root=self.target_repo)
super().__init__(raw_graph=raw_graph, compiler=compiler, registry=registry, ranker=ranker)
```

Make `RCIRContextProvider` able to reject stub-only `ContextEntry` results in **formal benchmarking**. Verify for every delivered source span:

- `source_exists == True`, `span_resolved == True` (or explicit non-verified class excluded from numerator);
- canonical repository-relative `source_file` under the pinned worktree;
- source content actually equals `worktree/source_file[start_line:end_line]` under normalized newline policy;
- SHA-256 of delivered snippet and/or source file computed from worktree bytes;
- `representation_type = SOURCE_SPAN`, not `FILE_REFERENCE`, `SOURCE_UNAVAILABLE`, `SUMMARY_ONLY`, heuristic placeholder or `// Reference: ...`;
- real token counter applied to the **exact serialized prompt**, including labels/metadata/system prefix when computing actual delivered prompt cost.

Count only verified source spans in `source-backed context` and `critical-source recall`. A ranked filename alone does not count. Add deterministic tests asserting the compiler genuinely opens a source file in a tiny pinned fixture repo, and assert stub mode cannot pass formal tests.

### B2. Graph/source revision invariants (F27)

- Add or verify graph metadata `target_repo`, `target_commit`, `index_schema_version`, extractor version, include/exclude filters, graph SHA, creation timestamp, and entity count.
- Before using a graph, assert its target revision matches trial worktree SHA; otherwise rebuild index at that exact revision or mark `INVALID_CONTEXT`.
- Source-code path from graph entity ID must use actual canonical registry mapping; **do not** derive arbitrary paths by stripping `php://` and splitting `::` unless mapping is independently verified.
- Initialize the registry from graph nodes and alias ledger before `resolve()`; identify ambiguous/missing receiver types, no synthetic `static_exact` confidence.
- Source path must be relative and must not escape root, including symlink/Windows separator attacks.

### B3. Symbol/operation resolution (F11)

- Stop picking the first capitalized word from task text as the only target.
- Parse public task hints, qualified identifiers, paths, operation type, known API names and semantic identifiers. Use canonical IDs and deterministic ranker profile.
- If multiple plausible targets exist, log ambiguity and compile candidate evidence without claiming exact target resolution.
- Require at least one verified target or justified source-backed candidate before formal RCIR arm begins.
- Collect `query_spec`, graph candidates, ranking breakdown, compiled context entries, source hashes and retrieval time in `raw/<trial>/retrieval_trace.json`.
- Do not inject known answer paths or hidden oracle contents.

### B4. Per-trial session isolation (F03)

- Instantiate a **new** retrieval session/provider for every RCIR trial or implement `new_session()` with new `ContextSessionState`, zero `already_seen`, and immutable graph read-only copy.
- No `entities_seen` leakage from task A into task B or replicate 1 into replicate 2.
- Test running same task twice with same seed/context and assert equivalent compiled context and independent per-trial counters.
- Snapshot provider config and graph index once, but not mutable session state.

### B5. RCIR must fail closed (F02)

Replace:

```python
except Exception as rce:
    print(f"[WARN] Live RCIR retrieval: {rce}")
    # ... continue with empty context
```

with a recorded `TRIAL_INVALID_CONTEXT`, full exception trace in the raw trial folder, no LLM call for the invalid arm, and pair status `INVALID_CONTEXT_PAIR` (new enum). Initialization failure must invalidate the planned RCIR trials or fail preflight before inference, never produce an empty pseudo-RCIR arm. Baseline may still be recorded, but an absent valid pair cannot contribute efficiency savings.

### B6. Restore source-backed rank trace for UI

- Use actual `RankedCandidate.total_score` and `breakdown.to_dict()`.
- Export `ranked_files.csv` and `retrieval_entries.jsonl` from each trial's actual ranker/compiled context. No hardcoded score/tier/count.
- For RCIR showcase API, expose `source_reference`, `source_sha256`, `ranker_version`, `query_status`, and a `live | historical_snapshot | unavailable` provenance field.
- An explicitly requested historical snapshot is fine; a silent fallback from a failed live query to cached data is **not**.

---

## 4. Phase C: experiment pairing, statistics and outcome accounting

### C1. Exact paired trial key (F04, F17)

Touch `experiments/benchmark_core/models.py`, `pairer.py`, `scripts/run_benchmark.py`.

Add `TrialResult` fields `target_sha`, `model`, `seed`, `turn_budget`, `replicate`, `task_manifest_sha256`, `experiment_version` (or contain a typed `TrialKey` and use it everywhere). The **pair key** is exactly:

```python
(task_id, target_sha, model, seed, turn_budget, replicate, experiment_version)
```

Pair one baseline with one RCIR record per key, never overwrite dictionary entry by `task_id` alone. Duplicate arm → `INVALID_DUPLICATE_PAIR`, missing arm → `INCOMPLETE_PAIR`, mismatched key → `INVALID_MISMATCHED_PAIR`, not silent omission. Explicitly report `planned_pairs`, `observed_pairs`, `valid_pairs`, `invalid_pairs` and denominator. Pair by randomized or counterbalanced arm order under matched model, tool budget, target snapshot, timeout and hardware profile.

**Mandatory test:** 3 tasks × 3 replicates = **9** pairs, **18** arm-trial records. Swap model/commit/seed on one arm: that pair must become invalid, never look like a valid match. Inject duplicate arm, incomplete arm and provider timeout separately.

### C2. Correct terminal states (F05)

Turn budget exhaustion ≠ provider timeout. Add statuses:

- `TRIAL_BUDGET_EXHAUSTED`: agent completed allowed turns without accepted change.
- `TRIAL_TIMEOUT_PROVIDER`: actual provider timed out.
- `TRIAL_TIMEOUT_TOOL`: tool execution timed out.
- `TRIAL_FAILED_AGENT`: invalid tool protocol/no task progress.
- `TRIAL_FAILED_BEHAVIOR`, `TRIAL_FAILED_REGRESSION`: completed evaluation with failed tests.
- `TRIAL_INVALID_CONTEXT`, `TRIAL_INVALID_SETUP`, `TRIAL_INVALID_EVIDENCE`, `TRIAL_NOT_MEASURED`.

Persist `stop_reason`, `provider_error_class`, `tool_error_class`, `last_turn`, and independent `agent_finished` state. A 12-turn unsuccessful task is normally valid evidence of **failure** (if infrastructure and both arms completed), not an invalid timeout pair.

### C3. Define valid pair and success separately

`VALID_PAIR` requires clean setup, identical paired keys, no provider/tool infrastructure failure, no missing required telemetry, no context invalidity in RCIR arm. A task whose agent genuinely failed tests may remain a valid **comparison**, but must be counted as an unsuccessful task. Count `both_success`, `rcir_only_success`, `baseline_only_success`, `neither_success` separately. Compute per-arm task completion rate using attempted valid tasks plus a separate intention-to-treat view of all planned tasks, with explicit failure accounting. Do not report `0` where measure is missing.

### C4. Correct metrics and evaluation power (F18)

Maintain distinct estimands:

1. **Retrieval quality:** precision/recall/MRR/nDCG against frozen independent ground truth (critical files vs actual code spans distinguished).
2. **Prompt cost:** entire provider-native input tokens per trial, broken into initial context, tool observations, history and output tokens; no invented IDE credits.
3. **Primary end-to-end efficiency:** total input/output/total token cost and wall time **per accepted task**, plus paired both-success subgroup when sample size is sufficient.
4. **Agent quality:** solved rate, CI/test gates, patch correctness, verification coverage, regressions, model/tool timeout rate.
5. **Robustness:** p50/p90/p95 latency, cache hits, per-task-tier successes, failures and outliers.

When 0 both-success pairs, `primary_efficiency_status=INCONCLUSIVE_ZERO_BOTH_SUCCESS`. When only 1–2 successes, display exploratory paired results with `INSUFFICIENT_SAMPLE`, not a product performance claim. Define measurable and pre-registered release thresholds; do not require 90% savings at the cost of incorrect edits. Use median and bootstrap confidence intervals **only when sample supports them**; add distribution tables and per-task raw values. Report negative deltas fully. Compare with meaningful baselines, not only intentionally bloated naive scanning.

### C5. Hard tests for statistical accounting

Add `tests/benchmark_integrity/test_pairing_matrix.py`, `test_metrics_strata.py` containing:

- 3 rep × 2 arms × 5 tasks, expected 15 pairs, not 5.
- both-success count differs from any-success count;
- missing `usage_record` → token metric `NOT_MEASURED`;
- one valid negative-delta pair included as negative;
- `0` input baseline tokens → no division-by-zero;
- provider timeout differs from budget exhaustion;
- mixed models, budgets, commits and seeds do not pair;
- deterministic re-computation of every CSV headline from raw trial JSON.

---

## 5. Phase D: agent tools, tests, and security

### D1. Genuine changed-file census (F10)

Touch `orchestrator/tools.py`, `orchestrator/agent_loop.py`, `experiments/benchmark_core/evaluator.py`.

Replace reliance on `self._modified_files` for benchmark scoring with independent `git diff --name-status HEAD`, `git diff --binary HEAD`, plus safely inspected untracked files. Track edits via `apply_patch`, `edit_file`, and `run_command` (some tools may generate or modify files outside helper APIs). Capture patch text before deleting the trial worktree. Normalize line endings without inventing changes; compare actual post-run filesystem state to pinned HEAD. If patch reverts to baseline, changed-file count and success must be zero. Hash all patch artifacts and save them.

### D2. Restrict command execution (F10)

Current code runs model-supplied commands using `subprocess.run(command, shell=True, cwd=worktree, env=full_host_env)`. An agent may execute shell commands outside the worktree despite safe `cwd`. Introduce **separate tool profiles**:

- coding agent: narrow, allow-listed argv commands without shell expansions; run in OS/container sandbox with filesystem permissions limited to trial worktree, no oracle or host secrets, no network unless explicitly needed and audited;
- evaluator: trusted commands in a separate read-only oracle context, never exposed to agent;
- developer/debug mode: broader commands possible only with explicit opt-in and labeled untrusted.

Use `shell=False` with argument parsing or typed command templates; reject shell metacharacters, shell builtins, absolute paths escaping root, `..` traversal, dangerous environment variables, and command chaining. Set CPU/memory/time limits; stop child process groups on timeout. Avoid broadcasting user secrets to subprocesses. Return `TOOL_DENIED`, `TOOL_TIMEOUT`, `TOOL_ERROR` explicitly. Add tests for `;`, `&&`, `$()`, `..`, symlinks, Windows `&`, absolute executable path, and command recursion.

### D3. Robust apply-patch and tool protocol

- `extract_tool_call` should be tested against nested braces, escaped quotes, fenced JSON, malformed partial JSON, multiple calls and strings containing braces. Return reason-coded errors without accidentally taking a random earlier tool call.
- `apply_patch` must support multiple hunks, paths with spaces, exact context matching, non-zero hunk offsets, deletion/addition and atomic rollback. Prefer `git apply --check` plus `git apply` within sandbox (or proven hunk parser); do not silently fall back to fragile raw `'-'/'+'` replacement that can alter wrong occurrences.
- Log tool invocations, validation failures and actual exit codes. Prevent a model merely saying `finish` from satisfying acceptance.
- If no actual file changed and targeted test did not become green, classify agent as failed even if tool command exits 0.
- Consider configurable task budgets, model capability tests, more precise tool output within context budget, and verified iterative hints. Do not leak gold answer paths.

### D4. Independent L1/L2/L3 with before/after behavior (F06–F08)

Touch `experiments/benchmark_core/evaluator.py`, `experiments/rcir_v8_5/agent_tasks/verify_regression.py`, and task-specific `verify_task*.py`.

Implement explicit tri-state/quad-state records, not PASS booleans for skipped work:

```python
class CheckStatus(Enum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    SKIPPED = 'SKIPPED'
    NOT_MEASURED = 'NOT_MEASURED'
    SETUP_ERROR = 'SETUP_ERROR'
```

- **L0 Negative control:** before agent runs, execute task oracle on pristine pinned repo. It must fail for the intended issue (otherwise invalid task oracle). This is not shown to agent.
- **L1 Syntax:** verify changed files using real relevant parser/compiler (`php -l` for PHP); `php` missing → setup error, not syntax PASS. No changes → `SKIPPED`/failed completion.
- **L2 Targeted behavior:** run actual task-specific behavioral test after modifications; validate target assertions, compare before/after and capture exit code, duration, stdout/stderr, toolchain IDs. Ensure a fixture file unrelated to true test cannot make green.
- **L3 Regression:** execute a defined subset of **actual upstream application tests** (e.g., phpunit/Nextcloud test runner with dependency environment). A PHP syntax pass is L1 only. Missing regression runner → `NOT_MEASURED` or `SETUP_ERROR`, never L3 PASS. If L3 is optional in a task, status `SKIPPED`, and separately record `required=false`; never set `l3_regression_passed=True` for a skip.
- **Adversarial gate:** accept iff clean verified diff, required L1/L2/L3 pass, L0 negative control passed, target revision correct, no secrets/banned paths; include reasons and machine-readable gate log.

Generate gold-independent smoke fixture with deliberately broken behavior where syntax passes but L2 fails and L3 is unavailable; ensure gatekeeper rejects. Create tests for `L3 skipped != PASS`, `L3 syntax-only != PASS`, `missing PHP != PASS`, `empty patch != success` and `positive green-before != valid oracle`.

### D5. Avoid dual-success semantics (F28)

The benchmark runner currently omits `test_command`, so `ReActAgentRunner.success` will generally remain false while the external evaluator separately computes acceptance. Define `agent_res.success` as *agent self-reported completion* or rename to `agent_workflow_completed`; make `EvaluatorOracle` exclusively determine `verified_success` and `gatekeeper`. Ensure both values are separately recorded, not overwritten. The agent should not see hidden test command. Display only independently evaluated `verified_success` as task success.

---

## 6. Phase E: live experiment harness and benchmark progress

### E1. Use a true benchmark entrypoint

`python scripts/run_benchmark.py --mode dev --turn-budget 12 --replicates 3 --model qwen2.5-coder:1.5b` must execute **actual LLM calls** only when all prerequisites are available and must save every raw trial and pair. `python scripts/run_final_benchmark.py` must either invoke that command with explicit flags or be renamed to `verify-artifacts`. No fixed gate text, no baked 0/5. A `--verify-only` command can validate existing evidence, but must say that it has **not** run inference.

Add CLI options: `--target-repo-path`, `--target-sha`, `--graph-path`, `--public-tasks`, `--oracle-path` (evaluator process only), `--provider`, `--model`, `--turn-budget`, `--replicates`, `--timeout`, `--run-root`, `--seed-base`, `--dry-run`, `--verify-only`, `--resume` (append only). Print effective config before execution.

### E2. Diagnose and fix agent success before headline claims

Run an ordered diagnostic matrix with fixed source SHA:

1. **Tool smoke:** local deterministic toy PHP fixture; inject an exact patch and assert diff/L1/L2 success with no LLM. Establish plumbing works.
2. **Agent smoke:** one easy but nontrivial visible DEV task with local Ollama, tool parsing, edit and regression checks. Save turn-by-turn transcripts and tool errors.
3. **RCIR context smoke:** same task with source-backed context. Assert real snippet bytes/line spans and token counter; no leakage.
4. **2-arm DEV A/B:** 3–5 representative tasks, 3 replicates at fixed budget, same model. Diagnose which failure stage dominates: target recognition, retrieval, tool format, patch application, L2 verification, provider timeout.
5. **Harder DEV:** multiple strata including route changes, interface changes, config changes, event handling and cross-module impacts. Maintain exact ground truth and provenance.
6. **Frozen TEST:** only after DEV tuning, under untouched tasks, run once per frozen model/config and audit all outcomes. No cherry-picking successes.

Measure small 1.5B model as a constrained baseline. If it cannot reliably emit correct patches at reasonable turn budgets, report that limitation; use a separate **clearly labeled** stronger local/free model comparison if hardware permits, not a silent model swap. Do not reclassify malformed tool responses as successful task completion.

### E3. Fair comparison

Both arms use same pinned target, public task instructions, model version, model temperature/seed if supported, max-turn limit, wall timeout, filesystem permissions, tool affordances, and verifier, with only RCIR context feature changed. Baseline can inspect/search original repo on demand, RCIR gets actual source-backed compilation and iterative context (its extra retrieval overhead separately measured). Counterbalance run order and caches. Clearly distinguish context construction latency/cost from LLM prompt token savings; account for total task cost.

### E4. Preserve error traces and receipts

Required per-trial raw files:

```text
experiments/runs/<RUN_ID>/
  manifest.json
  inputs/public_tasks.json
  inputs/immutable_config.json
  raw/<TASK>/<CONDITION>/rep_<N>/
    trial.json
    provider_usage.jsonl
    agent_turns.jsonl
    tool_trace.jsonl
    retrieval_trace.json
    git_diff.patch
    changed_files.json
    before_acceptance.json
    l1_syntax.json
    l2_targeted.json
    l3_regression.json
    gatekeeper.json
  results/trials.json
  results/pairs.json
  results/metrics.json
  results/gates.json
  exports/run_summary.csv
  exports/agent_trials.csv
  exports/paired_token_usage.csv
  exports/retrieved_files.csv
  exports/verification_matrix.csv
  proof_index.json
  SHA256SUMS.txt
```

`TRIAL_INVALID_*` must include reason and traceback, not disappear. `proof_index` hashes raw bytes; no proof is marked `VALIDATED` until recomputation succeeds. Do not pack absolute Windows paths in results; use portable root-relative paths and separately record host environment.

---

## 7. Phase F: backend, proof registry, and UI truthfulness

### F1. Run-scoped API only

Touch:
- `showcase_app/backend/services/benchmark_service.py`
- `showcase_app/backend/api/proofs.py`
- `showcase_app/backend/services/evidence_registry.py`
- `showcase_app/backend/services/rcir_service.py`
- `showcase_app/backend/api/rcir.py`
- `showcase_app/backend/schemas.py`

Make `/api/runs/{run_id}`, `/metrics`, `/pairs.csv`, `/retrieval.csv`, `/trials.csv` strictly read files under that exact validated run. **No** fallback to `showcase/data/*` if requested run has missing CSV. Return 404/409 with clear reason and `NOT_MEASURED` missing values. `/runs/<id>/proofs` must load the corresponding run's proof registry, not global historical proof list. Validate run IDs against allowlist and resolve paths safely, including symlinks. A historical view must be explicitly labeled `HISTORICAL_SNAPSHOT` and a live view `MEASURED_RUN` only after evidence hash validation.

`get_run_summary` must not invent `total_trials=10`, `valid_pairs=3`, `token_delta=1.68`, `crash_rate=0`. If data absent, show nullable fields and status. `HealthResponse` should say process is healthy while evidence validation is separate; do not mark `evidence_status=VALIDATED` unconditionally.

### F2. True RCIR query API

Use live retrieval that returns genuine ranker scores and source evidence. If graph unavailable or query cannot be resolved, return explicit error/status rather than fixed scores (`1.0`, `0.92`, etc.), fixed `repo_file_count=4412`, or silent switch to saved `rcir_pipeline.json`. Ensure `target_domain` is actually enforced or removed from API contract. Give query IDs with UUID or collision-safe generator, TTL/persistence as appropriate. Reset session state per independent query. Test two consecutive unrelated queries for cross-contamination.

### F3. Showcase synchronizer (F14, F24)

Touch `scripts/build_showcase.py`, legacy `scripts/build_showcase_data.py`, `scripts/build_run_exports.py`.

- `--run-id` required; verify full run exists, completed/eligible, manifest fields and SHA-256 of every referenced export before copying.
- Create `showcase/data/csv` and React mirror directories explicitly.
- Copy atomically into a versioned `showcase/data/runs/<run_id>/` location. A `latest.json` pointer may be updated only after all hashes validate.
- Stop generating historical hardcoded numbers in parallel exporter; formally archive old runs as `HISTORICAL_UNVERIFIED` where evidence cannot reproduce a claim.
- Never rewrite raw run manifests when CSVs are re-exported.
- Tests: tamper a CSV; delete metrics; change run ID; redirect path to another run; ensure synchronizer fails and current published snapshot remains unchanged.

### F4. Interpreter demo truthfulness (F22–F23)

Touch `showcase_app/backend/services/interpreter_service.py` and tests.

**Two explicit modes:** `REAL_POLY_EXECUTION` and `ARCHITECTURE_DEMONSTRATION` (if only illustrative). Do not label latter live ERPNext parity.

For real execution, parse the exact selected `.poly`, validate actual schema and parser diagnostics (throw on bad/missing schema), construct real executable cell graph from `parsed_ast.language_blocks` and supported directives, schedule cells respecting declared dependencies, dispatch through real runtime, collect actual `CellResult`s. No hardcoded `js_code`, `py_guard_code`, `tax_amount`, `tax_rate`, fake merge durations, fake `max(0.1, measured)` latency floor or derived DAG nodes from `len(sources)+len(schemas)`. If source-only `.poly` is not executable, state `SOURCE_MAPPING_ONLY` and do not execute unrelated fixed cells under its name. In controlled failure, inject a safe optional cell; allow fallback **only if** contract declares and runs a verified fallback. A failed core tax/ledger cell must block financial transaction success. Record monotonic durations, output hashes and fallback provenance.

Test that changing `.poly` executable code changes output; invalid schema fails validation; critical tax failure cannot return SUCCESS/DEGRADED-as-success; optional notification failure returns `DEGRADED` only if actual fallback executes; source-only mapping does not pretend to execute native ERPNext.

### F5. Preserve four-system architecture and Agent Pool

PolyFlow feature closure, custom interpreter, RCIR, and Maker/Reviewer/Rectifier/Gatekeeper Agent Pool remain **independent but composable**. Do not erase or merge them into a generic dashboard. UI must show four sections with understandable terminology and optional clickable plain-language explanations. Import evidence from validated run APIs only. Dynamic flows must indicate when they are illustrations vs actual backend-emitted events. Add one succinct verdict pane showing independent states: feature mapping, source-backed RCIR, agent patches, L1/L2/L3, token analysis, ERPNext parity.

---

## 8. Phase G: tests, CI, and acceptance gates

### G1. CI split: deterministic tests vs expensive live evaluations

Modify `.github/workflows/ci.yml`:

- PR CI: compile/import checks, unit & property tests, fake-provider agent loop tests, isolated tiny Git repo smoke test, security negatives, schema tests and deterministic proof-validator tests. No internet/Ollama dependency for required PR gates.
- Optional/manual/host-runner job: live pinned Nextcloud + Ollama integration (public tasks only) with artifacts and real provider telemetry. If no local target repo or Ollama is available, mark live test `NOT_RUN`, not green. Never skip the only test that would prove live RCIR.
- Make CI exercise `python scripts/run_benchmark.py --help` and `--dry-run`, not just `pytest` with `conftest.py` injecting custom imports.
- Add lint and type-check for core benchmark models as available, plus Windows `subprocess` command compatibility tests.

### G2. Minimum explicit adversarial regression tests

Create at least these tests and prove they fail before fix and pass after fix (or explain if test is new behavior):

1. `test_compiler_real_root_never_stubs`.
2. `test_rcir_stub_context_invalidates_formal_trial`.
3. `test_graph_commit_mismatch_fails_closed`.
4. `test_registry_resolves_file_from_graph_not_uri_guess`.
5. `test_provider_session_isolated_across_tasks`.
6. `test_provider_session_isolated_across_replicates`.
7. `test_rcir_init_failure_no_agent_call`.
8. `test_rcir_retrieval_failure_invalid_context_pair`.
9. `test_exact_pair_key_replicates_3x2`.
10. `test_mixed_model_seed_sha_do_not_pair`.
11. `test_duplicate_arm_rejected`.
12. `test_missing_arm_reported_not_omitted`.
13. `test_budget_exhaustion_not_provider_timeout`.
14. `test_no_edit_after_12_turns_failed_agent`.
15. `test_l3_skipped_never_pass`.
16. `test_php_lint_not_l3`.
17. `test_targeted_oracle_green_before_invalidates_task`.
18. `test_upstream_suite_missing_not_pass`.
19. `test_model_shell_metacharacters_blocked`.
20. `test_model_cannot_read_hidden_oracle`.
21. `test_command_edits_included_in_git_diff`.
22. `test_patch_revert_yields_empty_diff`.
23. `test_raw_artifacts_preserved_on_trial_crash`.
24. `test_run_manifest_target_commit_equals_worktree_commit`.
25. `test_non_utc_local_timestamp_not_labeled_utc`.
26. `test_unverified_metrics_no_default_values`.
27. `test_run_scoped_csv_missing_returns_404`.
28. `test_run_proof_registry_not_global`.
29. `test_tampered_export_blocks_showcase_sync`.
30. `test_historical_snapshot_never_masks_live_failure`.
31. `test_live_rcir_api_returns_actual_ranker_scores`.
32. `test_interpreter_real_code_comes_from_poly_ast`.
33. `test_interpreter_critical_failure_blocks_transaction`.
34. `test_ci_cli_imports_without_pytest_path_magic`.
35. `test_agent_verified_success_only_from_oracle`.
36. `test_secret_oracle_path_does_not_escape_via_symlink`.

Prefer deterministic local fixtures for regression logic. Include at least one separate **real-world** pinned integration run to validate architecture claims; fixture passes alone do not prove Nextcloud/ERPNext performance.

### G3. Formal acceptance gates

**Engineering correctness gates** (must pass before benchmarking):

- A. Standalone command imports and `--dry-run` work; no hidden path coupling.
- B. Pinned revision and index metadata agree; clean full worktrees.
- C. RCIR delivers source-backed spans, not stubs; source hashes pass.
- D. Each requested A/B pair has exact validated identity or explicit incomplete state.
- E. Agent tool safety and hidden-oracle isolation pass adversarial tests.
- F. L0/L1/L2/L3 statuses are honest, with no fabricated PASS.
- G. Every raw trial is persisted with trace, diff and token telemetry or explicit measurement failure.
- H. All API metrics reconcile with raw trials; proof hash verification passes.

**Performance gates** (measured independently, not forced):

- Report agent task completion separately for baseline and RCIR across DEV/TEST strata and replicates.
- Report the proportion and causes of failed/invalid trials, not just successes.
- Require nontrivial both-successful pairs before making savings claims; classify underpowered tests as exploratory.
- Retrieval ranking improvement, if claimed, is compared against meaningful baselines on held-out ground truth.
- All diagrams/UI status labels match the actual measured artifact status; no sample values reclassified as live.

If a performance gate is unsatisfied, stop release promotion, document root cause, and preserve honest result. **Never adjust tests or summaries to manufacture success.**

---

## 9. Execution order and required outputs

Execute precisely in this order, committing coherent logical milestones where practical:

**Checkpoint 0, forensic baseline:** inspect existing code and clean git status; capture initial pytest, import, dry-run and existing run artifact status. Generate `reports/commit_4c8505_baseline_audit.md` listing failures with reproducible commands.

**Checkpoint 1, foundation:** resolve standalone imports, pinned commit/worktree identity, run manifest, true private oracle separation, immutable logging and cleanup. Run deterministic tests.

**Checkpoint 2, RCIR:** bind compiler to actual target, resolve genuine entities/source spans, graph revision manifest, trial-local sessions and fail-closed retrieval. Prove context bytes and source SHA match.

**Checkpoint 3, pairing/accounting:** exact multi-replicate pairing, terminal statuses and metrics; negative and adversarial tests.

**Checkpoint 4, agent and evaluator:** sandbox tool execution, complete git diff, safe patch application, L0/L1/L2/L3 tests and gatekeeper. Prove one local coding smoke task can be independently accepted before running full suite.

**Checkpoint 5, real experimental run:** run DEV diagnostic, improve RCIR/agent only in DEV, then freeze and run fair TEST A/B. If unavailable, write `NOT_RUN` blocker with exact missing dependency. Save raw logs and valid pair matrix; do not skip tasks selectively.

**Checkpoint 6, proof + API:** refactor proof registry and backend run scoping; no hidden historical fallback; verify bytes, hashes and CSV consistency.

**Checkpoint 7, custom interpreter + UI:** real `.poly` parser/executor semantics, correct fallback, architecture labels, and updated demonstration app, only once source truth is sound.

**Checkpoint 8, final report:** publish `reports/POLYFLOW_4C8505_RECTIFICATION_AND_RESULTS.md` with precise table:

| Finding | Status | Files modified | Test proving fix | Actual run proof | Remaining blocker |
|---|---|---|---|---|---|
| F01 … F28 | FIXED / PARTIAL / OPEN | path | test id | run-relative path / NOT_RUN | explanation |

Include `git diff --stat`, source SHA, changed modules, reproducible CLI commands, tests attempted and results, new run IDs and their hashes, confidence limits, honest completed-task numerator/denominator, token deltas for valid pairs, non-improvements, and explicit architecture-vs-parity distinctions. State which claims are `MEASURED`, `HISTORICAL`, `INCONCLUSIVE`, `NOT_MEASURED`, or `DEMONSTRATION`.

**Final human-readable answer after executing the prompt:** concise description of actual fixes, verification status, benchmark table, links/paths to artifacts and unresolved problems. Do not simply say "all issues resolved" because unit tests passed. The real evidence must agree.

---

## 10. Starting commands (adapt only after inspecting repo)

```powershell
# Repo HEAD and changes
git rev-parse HEAD
git status --short
git diff b86acd511ffdee5b834a56e00ab8c1b87d66530a..HEAD --stat

# Baseline deterministic checks
python -m pytest tests/benchmark_integrity -q
python -m pytest tests/test_final_claim_consistency.py tests/test_backend_proof_server.py -q
python scripts/run_benchmark.py --help

# First developer preflight AFTER implementing --dry-run and pinned context
python scripts/run_benchmark.py --mode dev --target nextcloud --turn-budget 12 --replicates 3 --dry-run

# DEV live run ONLY when local model, target repo and oracle are valid
python scripts/run_benchmark.py --mode dev --target nextcloud --turn-budget 12 --replicates 3 --model qwen2.5-coder:1.5b

# Verify completed run and synchronize dashboard from that run ONLY
python scripts/build_showcase.py --run-id <ACTUAL_COMPLETED_VALIDATED_RUN_ID>
```

**Important:** At the moment of this independent audit, neither the commands above nor the full experimental suite were run by the auditor on a local clone. They are execution instructions for the development environment. Do not retroactively attribute their results to this audit.

## 11. Final principle

Build one coherent evidence pipeline:

```text
Pinned repository + frozen public tasks + private independent oracle
          |
          v
Source-backed RCIR graph (correct SHA, real spans) -----> Baseline arm (no RCIR)
          |                                                     |
          v                                                     v
RCIR arm: separate clean worktree                       Separate clean worktree
          |                                                     |
       Real agent/tool calls and complete git diffs in both arms
          |                                                     |
          +------------------------+----------------------------+
                                   |
                  Independent before/after L1/L2/L3 evaluation
                                   |
                    Exact pair keys + valid trial classification
                                   |
                Raw logs / provenance / native tokens / patch files
                                   |
                      Immutable run artifact + hash manifest
                                   |
                       Verified REST API + CSV + UI
```

The final objective is **better task correctness and efficiency grounded in real evidence**, not a plausible animation, a passing showcase generator or an inflated percent. Fixes first, measured results second, presentation last.
