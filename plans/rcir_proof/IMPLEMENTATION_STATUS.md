# Owner-authorized implementation checkpoint — 26 November 2026

PHASE: PF-RP-02–10 scoped software implementation; experimental and release
gates remain unaccepted. This checkpoint does **not** complete the full master
plan or establish benchmark improvement.

REPO/SHA/BRANCH/DIRTY: `paril-01/PolyFlow`, input
`8563118c5b7d69820749394f6b6f4a30f941a0c2`, branch
`work/pf-rp-01-proof-integrity`. Scoped changes plus pre-existing owner changes.
Published commit and hosted conclusions are recorded in [PROGRESS.md](./PROGRESS.md).

AUTHORIZATION: The owner repeatedly requested complete implementation and push.
[Implementation ticket and exact ownership](./IMPLEMENTATION_TICKET.json).
This authorizes software work and branch publishing, not fabricated independent
review, paid inference or release acceptance. No further push approval is needed.

FILES READ: root [AGENTS.md](../../AGENTS.md),
[phase skill](../../.agents/skills/polyflow-phase-execution/SKILL.md),
[master execution specification](../MASTER_IDE_EXECUTION_SPEC.md),
[master implementation/proof plan](../../PolyFlow_RCIR_Master_Implementation_and_Proof_Plan.md),
[existing phase state](../../templates/PHASE_STATE.json),
[progress](./PROGRESS.md), [backlog](./BACKLOG.json),
canonical entity model, context provider/compiler/tokenizer/models, legacy
R0/R1/R2 adapters and bakeoff runner, existing MCP compatibility tests, current
CI configurations and previous CI closeout. Source changes are listed below.

## Requirement-to-file mapping and honest remaining scope

| Plan | Implemented in this checkpoint | Remaining work / acceptance |
|---|---|---|
| PF-RP-01 | [Historical replay verifier](../../experiments/rcir_v8_5/scripts/verify_historical_replay.py), separately named replay CI and manual strict release workflow. Original dirty flag and strict gate preserved. | Hosted result for this checkpoint; historical replay never becomes a current clean benchmark. |
| PF-RP-02 | [Explicit retrieval study](../../experiments/benchmark_core/retrieval_study.py), new CLI and old entrypoint replacement: separate queries/gold, exact SHA and path/span checks, source-hashed oracle, all delivered spans, actual serialized budgets at 1k/2k/4k/8k, per-query timings, p50/p95, no overwrites or automatic winner. R1 now consumes `entries`, registers canonical entities, binds graph SHA and rehydrates source without silent fallback. | Historical 11-task DEV rerun NOT_RUN; checked-in extractor graph is not the required keyed canonical schema with verified identity. Fresh validation split, edge oracle, meaningful ranking/frontier and ablation study remain unperformed. Fixture tests are not architecture evidence. |
| PF-RP-03 | [Snapshot](../../rcir/src/rcir/service/snapshot.py), [source index](../../rcir/src/rcir/service/index.py), [service](../../rcir/src/rcir/service/api.py): Git/overlay identity, before/opened/after byte checks, AST Python symbols, raw span hashes, static import reverse closure/cycles, locked full-rebuild generations and manifest persistence. R2 recursive conservative invalidation now covers dependent methods, deletes/reparse and excludes stale source. R3 is a lexical/canonical union candidate. | Manifest persistence rebuilds on startup; optimized persistent/incremental indexing and bounded typed hybrid traversal are not complete. Non-Python semantics remain lexical/INFERRED. Cross-language and dynamic relation validation, workload performance and reviewed architecture selection remain pending. |
| PF-RP-04 | [Real MCP SDK 2 stdio server](../../rcir/src/rcir/service/mcp_server.py), SDK, CLI, legacy v1 facade, exact serialized delivery budgets, typed error statuses, stale/evicted expansion, pinned symbols, read-only impact/status with explicit refresh. Standalone import no longer eagerly pulls the orchestrator. | Native IDE/client configuration study and deeper cancellation/load validation pending. MCP counts cover the tool result; JSON-RPC framing and complete provider prompts/schemas must be counted separately. |
| PF-RP-05 | [Study primitives](../../experiments/benchmark_core/product_study.py), [independent DEV controller](../../experiments/benchmark_core/agent_trial.py), [study CLI](../../scripts/run_product_study.py): base-only exports, real Linux bubblewrap, no host fallback, bounded output/CPU/address space, separate oracle mounts, executable base/reference/irrelevant controls, local-only provider/model guard, raw request/response/native counts, fresh A/B namespaces, complete changed bytes/modes including untracked/binary files, separate evaluator and hash seals. No host Git executes after agent modifications. Missing planned rows remain in ITT; task-cluster bootstrap and missing-native-usage handling are explicit. | A real local model task is NOT_RUN. Generic dependency/container adapters, full controlled factorial execution, no-edit qualification, human-reviewed command semantics and resource calibration are incomplete. Protocol structure validation does not authenticate a curator. Existing legacy runner remains historical; use the new explicit CLI. |
| PF-RP-06 | [Default-off deterministic supplementary router](../../rcir/src/rcir/service/delivery.py): protected passthrough, explicit lossy views, scoped SHA-bound originals, TTL/LRU/byte limits, no transformation that expands serialized tokens, exact restore and unavailable-after-eviction behavior. | Headroom upstream pin/license/dependency audit, optional SDK/proxy integration and actual trace comparison NOT_IMPLEMENTED/NOT_RUN. Nothing is bundled or enabled under the Headroom name. |
| PF-RP-07 | Protocol validation and reproducible counterbalanced schedule helpers exist. | Independent curator, actual public historical task corpus, source licenses/dependency images, qualified hidden tests, reviewed split families and freeze receipts are missing. No synthetic fixture is relabeled locked or independent. |
| PF-RP-08 | DEV execution and measurement tooling exists. | Actual model calibration, approved pilot, ablations, frozen candidate and actual native usage results NOT_RUN. |
| PF-RP-09 | Independent recomputation helpers preserve failed/missing trials and null usage; no zero-success savings headline. | Locked study, native IDE A/B sessions, native credits and independent acceptance NOT_RUN/NOT_MEASURED. |
| PF-RP-10 | [Development package](../../rcir/pyproject.toml), [quickstart](../../rcir/README.md), installable CLI, real client test, SHA-256 run verifier, clean wheel installation outside checkout, observed Windows dependency constraints. New Windows/Linux product CI. | Development package only. Full hash lock/cross-platform install matrix, signed proof (no signing key available), metric dashboard/current benchmark proof and independent release acceptance pending. |
| PF-RP-11 | No speculative learning/native rewrite introduced. | Optional iteration deferred until measured DEV benefit. |

EVIDENCE TABLE / COMMANDS / TESTS:
Exact executable, argv, start time, duration, exit code and raw log path are in
[commands.jsonl](../../experiments/runs/pf_rp_impl_20261126/commands.jsonl).
Failures are retained rather than overwritten. Separate overlapping suites must
not be summed into a benchmark success count.

| Evidence | Classification | Observed command outcome | Raw log |
|---|---|---|---|
| Service, real MCP, study and legacy/adversarial checks | OBSERVED_EXECUTION | `python -m pytest tests/test_rcir_service.py tests/test_rcir_service_mcp.py tests/test_product_study.py tests/test_rcir_c0_mcp_and_bundle.py experiments/architecture_trials/v3/tests/ -q`; exit 0; 50 passed, 1 Windows symlink skip at that checkpoint | [final-service-study.log](../../experiments/runs/pf_rp_impl_20261126/final-service-study.log) |
| Extended study/ITT checks | OBSERVED_EXECUTION | `python -m pytest tests/test_product_study.py -q`; exit 0; 13 passed | [study-last-check.log](../../experiments/runs/pf_rp_impl_20261126/study-last-check.log) |
| Real SDK client transport and counted MCP tool result | OBSERVED_EXECUTION | `python -m pytest tests/test_rcir_service_mcp.py -q -s`; exit 0; 1 passed | [wire-mcp-fixed.log](../../experiments/runs/pf_rp_impl_20261126/wire-mcp-fixed.log) |
| Core interpreter, proof service, closure and claims | OBSERVED_EXECUTION | `python -m pytest tests/test_polyflow.py tests/test_backend_proof_server.py tests/test_evidence_registry.py tests/test_feature_closure.py tests/test_ui_claims.py tests/test_final_claim_consistency.py -q`; exit 0; 72 passed, 2 Windows symlink skips | [interpreter-proof-regressions.log](../../experiments/runs/pf_rp_impl_20261126/interpreter-proof-regressions.log) |
| Existing integrity suite | OBSERVED_EXECUTION | `python -m pytest tests/benchmark_integrity/ -q`; exit 0; 51 passed | [integrity-regressions.log](../../experiments/runs/pf_rp_impl_20261126/integrity-regressions.log) |
| Stages, agent tools and extra real runtime tests | OBSERVED_EXECUTION | exact expanded paths in ledger; exit 1; 82 passed, Go/PHP runtime tests timed out | [stage-regressions.log](../../experiments/runs/pf_rp_impl_20261126/stage-regressions.log) |
| Focused timeout recheck, no runtime edit | OBSERVED_EXECUTION | the two failing real-runtime node IDs, exit 0; 2 passed | [runtime-timeout-recheck.log](../../experiments/runs/pf_rp_impl_20261126/runtime-timeout-recheck.log) |
| Dirty historical release negative controls | OBSERVED_EXECUTION | `python -m pytest tests/benchmark_integrity/test_historical_provenance_gate.py tests/benchmark_integrity/test_historical_hash_policy.py -q`; exit 0; 18 passed | [strict-release-guard.log](../../experiments/runs/pf_rp_impl_20261126/strict-release-guard.log) |
| Historical replay consistency, still release-ineligible | OBSERVED_EXECUTION | `python experiments/rcir_v8_5/scripts/verify_historical_replay.py`; exit 0 | [historical-replay.log](../../experiments/runs/pf_rp_impl_20261126/historical-replay.log) |
| Standalone wheel and real source query | OBSERVED_EXECUTION | `python experiments/runs/pf_rp_impl_20261126/package_smoke.py`; exit 0; build, new venv, install, `pip check`, installed CLI/query, dependency freeze | [wheel-standalone-fixed.log](../../experiments/runs/pf_rp_impl_20261126/wheel-standalone-fixed.log) |
| Agent/evaluator filesystem separation | OBSERVED_EXECUTION | WSL shell negative-control script; exit 0 | [wsl-sandbox-negatives.log](../../experiments/runs/pf_rp_impl_20261126/wsl-sandbox-negatives.log) |
| Actual control execution and patch replay in sandbox | OBSERVED_EXECUTION | WSL Python integration; exit 0; SYNTHETIC fixture, zero model calls | [wsl-study-integration.log](../../experiments/runs/pf_rp_impl_20261126/wsl-study-integration.log) |
| Windows host sandbox preflight | OBSERVED_EXECUTION | exit 2/BLOCKED as required; no host fallback | [sandbox-preflight.log](../../experiments/runs/pf_rp_impl_20261126/sandbox-preflight.log) |
| Model task improvement, independent/locked trials, IDE savings | NOT_RUN / NOT_MEASURED | No claim | None |

PLAN + ALTERNATIVE: retain a simple BM25/source-symbol candidate as the explicit
default. Repair canonical and versioned candidates for fair DEV comparison;
do not select a hybrid without reviewed measurements. Keep deterministic
supplementary delivery off; upstream integration must earn its additional cost.

CHANGES: Source service, MCP facade/transport, lazy optional provider import,
experimental adapters/runner, independent study/controller modules, tests,
three scoped CI workflows, package metadata/quickstart and audit documentation.
Only owned paths are included in the work-branch commit.

RISKS/BLOCKERS: The coverage table is authoritative for unfinished requirements.
The synthetic check cannot satisfy a historical task benchmark. Linux bubblewrap
worked in WSL; native Windows trial execution is unsupported. Large/dependency-
heavy repositories need prepared adapters. Index full verification/rebuild is
deliberately conservative and has not established the performance frontier.
SDK tokenization is cl100k_base, not another model's native billing counter.
Original runtime timeouts are retained as an environment/load concern.

PROHIBITED ACTIONS: No interpreter/SDK implementation edit, target checkout
reset, submodule commit, raw historical receipt/manifest rewrite, repository
merge, main-branch write, paid inference, fabricated native metrics, release
signing or external-review impersonation. The owner's staged recovery document
and changed target gitlinks/worktree remain outside our commit.

TOOL/MODEL IDENTITY: Codex; exact serving model ID UNVERIFIED (not exposed by a
native receipt). Prior recorded VS Code 1.147.0, Git 2.53.0.windows.1, selected
CPython 3.12.2; WSL Python 3.12.3. Local SDK test used MCP 2.3.0 and tiktoken
0.14.0. Clean-wheel dependency versions are in
[observed Windows constraints](./requirements-win312-observed.txt). These are
actual observations, not a claim of a universal hash-locked environment.

SECURITY FOLLOW-UP: Trial search/retrieval explicitly uses source-only snapshots
and never consults agent-modified Git configuration. Initial base-only Git setup
ignores host/system Git configuration and templates. Regression command
`python -m pytest tests/test_rcir_service.py::test_source_only_never_runs_host_git tests/test_product_study.py::test_patch_capture_is_independent_of_agent_git -q`
is recorded in [agent-git-isolation.log](../../experiments/runs/pf_rp_impl_20261126/agent-git-isolation.log).

GATE STATUS: PASS_FOR_TESTED_SOFTWARE_SCOPE; INCOMPLETE_FOR_MASTER_PLAN;
BLOCKED_FOR_BENCHMARK/RELEASE_ACCEPTANCE. No phase is self-promoted.

NEXT ACTION: Verify pushed Windows/Linux CI; obtain independent task/control
curation and canonical graph identity, qualify a real DEV toolchain/model,
then execute the approved pilot before freezing any locked study. The remaining
software and evidence work is explicitly tracked above; no new push permission
is required.

## Hosted source closeout

Source commit `f05fd897be1c632e95b58c1f528d8c8aec7eea47` is pushed.
All five hosted workflows concluded success, including both OS product jobs,
Python 3.10/3.11/3.12 units, both OS artifact replay jobs, general CI and React.
[Native raw workflow/job receipts](../../experiments/runs/pf_rp_impl_20261126/hosted-source-ci-final.json)
were captured with exit 0 in
[hosted-source-ci-final.log](../../experiments/runs/pf_rp_impl_20261126/hosted-source-ci-final.log).
The strict manual release workflow was NOT_RUN; dirty-source rejection was
verified by the saved negative-control tests, not converted to a clean release.
The final audit commit only publishes these receipts/docs and their capture
helpers. Full-plan and release status remain INCOMPLETE/BLOCKED as mapped above.
