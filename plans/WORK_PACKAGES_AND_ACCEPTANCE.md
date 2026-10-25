# Executable work-package catalog (planning baseline v3)

All work packages are **PROPOSED** until read-only source inspection, ADR review, and scoped owner authorization. Each work package must have its own ticket and raw evidence. `PASS` is a stage gate, not a promise that code will be written or that the product is good.

## A0: Freeze reality, not the repo

- **A0-01 checkout census:** `git rev-parse HEAD`, `git status --short`, `git remote -v`, `git submodule status --recursive`, `git ls-files` under relevant paths; record untracked user files and branch. Zero destructive commands. Acceptance: paths and SHAs captured; discrepancies with Oct 9 report highlighted.
- **A0-02 CI timeline:** list four failed workflows at pinned SHA; identify per-job exit status and raw error logs. Acceptance: reproducible log links or `UNAVAILABLE`; no indirect assumptions from workflow names.
- **A0-03 benchmark inventory:** catalog every CLI entrypoint (live, dry-run, wrapper, smoke), benchmark fixture and gold/evaluator storage; map which scripts really call a model and which only check static reports. Acceptance: call graph and truth table.
- **A0-04 language/interpreter baseline:** read parser, runtime, SDK package metadata and tests. Record `KNOWN_SUPPORTED`, `CLAIMED`, `UNTESTED` cross-language capabilities. Acceptance: boundaries and no modification plan.
- **A0-05 Agent Pool independence:** compare old PolyFlow `agents/` documents, standalone `paril-01/agents` actual checkout, Oct 15 AEF 3.2 RFC. Acceptance: no claim that RFC was deployed.

## A1: Architecture decisions and negative cases

- **A1-01 D1 R0 conventional:** specify lexical inverted index, symbol lookup, source span extraction, immutable snapshot, freshness control, normalization and token-budget packing; a strong conventional competitor.
- **A1-02 D2 R1 old RCIR:** build precise current behavior diagram for `graph/canonical_graph.py`, `graph/multi_view.py`, `retrieval/candidate_generator.py`, `retrieval/ranker.py`, `context/compiler.py`, `state/*`; distinguish implemented code from executed proof.
- **A1-03 D3 R2 VEST-lite:** candidate versioned fact record, query planner, inverse dependency index, exact/inferred edge confidence, context-evidence API, invalidation semantics and bounded fallback. Every relation must prove its origin or stay labeled inferred.
- **A1-04 D4 R3 research branch (optional):** define an actual n-ary relation use case requiring hypergraph representation; compare against adjacency nodes in existing graph. Reject if no measured gain.
- **A1-05 trust and hazard model:** untrusted source as instructions, wrong repo SHA, symlink/path escaping, source exfiltration, stale cache, benchmark leakage, multiagent self-approval, cross-tenant storage, arbitrary run commands. Acceptance: threat → enforcement point → negative test.
- **A1-06 AEF ownership ADR:** source of truth is standalone AEF; its claims/gates/roles don't depend on RCIR; optional adapter is read-only evidence feed. Acceptance: install without RCIR, and contract does not carry signing authority in agent prose.

## A2: Protocol before measurements

- **A2-01 pre-registration:** task bank methodology, DEV/VALIDATION/LOCKED-TEST split, truth labels sourced from evaluator-only worktree, inclusion/exclusion policy, trial schedule, model/IDE version, fixed budgets, repeat count, run seed, confidence intervals and no-post-hoc-optimization policy.
- **A2-02 success definition:** task success = evaluator-verified behavior and no critical regressions; no-op tasks have correct no-edit outcome. Refuse "finished" based only on model statement or a green UI.
- **A2-03 measurement schema:** provider-native API usage vs estimated token counts vs IDE credits; all requests including failures; context/index CPU+RAM cost and cold/warm distinction; score success, latency and cost separately.
- **A2-04 independent evaluator isolation:** hidden tests, labels, model prompts and evaluator keys absent from agent/test system being assessed. Prohibit adaptive training/tuning on locked labels.

## B0: Small hotfixes (after explicit approval)

| Ticket | Locate | Exactly what to alter only after reproducing | Required negative tests |
|---|---|---|---|
| B0-01 provenance | `tests/benchmark_integrity/`, benchmark fixtures, submodule manifest and smoke workflow | Correct genuine SHA/fixture alignment or validator bug, preserving original ground truth history; classify all 107 mismatches by underlying mechanism | Wrong SHA / changed bytes / absent target fails loudly |
| B0-02 model contract | `scripts/run_benchmark.py`, `orchestrator/providers.py`, provider consumers | Align constructor/adapter to explicit provider and model, actual endpoint ID, fail-closed provider exceptions and usage record semantics | Invalid model, missing provider, unavailable endpoint cannot generate PASS |
| B0-03 proof routing | `tests/test_backend_proof_server.py`, proof list and server handler | Reconcile real proof index keys to retrievable records and 200 for advertised receipts; scope path and hashes | Unknown proof returns controlled 404; traversal denied |
| B0-04 truthful wrapper | `scripts/run_final_benchmark.py`, report schema and CI | Rename/factor **if approved** into report-validate vs live-trial commands, with distinct exit status and provenance; no static "all good" implying real run | Missing real paired logs => `NOT_MEASURED` |
| B0-05 stage parity | `orchestrator/router.py`, `orchestrator/runner.py` | Convert scheduled-stage names into actual handler registry or fail validation; resolve `retriever`, `maker_revision` mismatch with reviewed ADR | Unsupported stage fails, not silently omitted |
| B0-06 gate integrity | `orchestrator/agent_loop.py`, prompts, `orchestrator/runner.py` | Prevent nonempty diff + one test from becoming general release approval; pass actual role-specific contract to tool-enabled implementer; preserve exact run | Fake pass text, missing test, zero verified evidence => no release |

**Do not conflate B0 safety repairs in old PolyFlow orchestrator with implementing new standalone AEF.** B0 can be a de-risking guardrail while actual AEF design stays separate.

## B1, B2: VEST-lite spike and bakeoff

Suggested internal prototype namespaces, **not mandated paths until code inspection**:

```
experiments/architecture_trials/v3/
  manifests/                 # separate repo snapshots and query definitions
  r0_lexical_symbol/         # strong comparator
  r1_adapter/                # existing RCIR unchanged
  r2_versioned_evidence/     # minimal experimental DS
  tests/                     # fixture property tests
  runners/                   # evaluator; sealed inputs
  README.md                  # truthful proof limits
```

If `experiments/architecture_trials/` conflicts with current repo layout, propose a change; do not silently relocate or overwrite. R2 design requires typed records, incremental indexing with reverse invalidation, selective source reads, observable failures, no fake stubs in official evaluation, deterministic serialized snapshots, independent benchmark gold. Run E0 first. Promotion gate requires no unacceptable critical-source recall regression, no falsely exact dependencies, proven lifecycle freshness, and practical cost/latency advantage compared to R0/R1. Avoid numeric success thresholds until set before untouched test evaluation.

## C0: Selected RCIR production integration

Only after B2 selected architecture and new user approval:

- Map experiment structures onto existing RCIR package with migration, feature-flag rollback and old API compatibility. Keep established typed graph as possible substrate rather than duplicating full graph store.
- Add frozen snapshot + file hash consistency at every entry/exit; incremental event invalidation and exact reason codes.
- Return bounded `ContextEvidenceBundle v1`: actual file/lines/snippet, provenance, resolution class, source freshness, explicitly omitted targets and truthful tokenizer identification.
- Require contract/property/integration/stress tests: concurrency, random diff sequences, patch races, restart/crash, source path escaping, huge file, unavailable network, repo-sensitive content.
- Add read-only MCP tool adapter with least privilege; no external code execution through retrieval interface. Tool must be discoverable and actually called in IDE pilot.
- Migration test verifies old public API behavior or lists versioned breaking change in reviewed ADR. Preserve interpreter and SDK regression suite.

## C1-C2: Controlled and real IDE evidence

- Fix/provider-prove actual model call and token telemetry without using model estimates as exact counts.
- Run one-task smoke on same worktree: same underlying model, same context budget and available standard tools; R0/R1/R2 separate arms.
- After smoke, freeze pilot: 5-8 tasks and E0/E2 instrument all calls, edits, failures and independent tests.
- Main evaluation only after evaluator review and budget availability, with held-out tasks across 3 repos. No prompt reuse containing prior gold answer.
- Antigravity E1 native indexing ON in all arms, R1/R2 as additional MCP, track actual MCP invocation. Native-index baseline never intentionally deprived of tools.
- Never claim real IDE credits from API token counts or local model telemetry. Report only vendor-reported IDE credits when available and attributable to the specific trial.

## C3: Agent Pool/AEF execution in its OWN repository

Stage development independently: (1) in-memory typed claim/evidence schema with negative tests; (2) stable semantic IDs/cycle witness/reverse invalidation; (3) deterministic gate policy and honest terminal states; (4) bounded S08 repair/state machine; (5) tool gateway with genuine external authority; (6) real provider-runner with model identity, bounded budgets and checkpointing; (7) reviewer isolation, role-specific contract and flight recorder; (8) high-level blueprint generation; (9) optional PolyFlow RCIR evidence adapter. Every unit has schema tests, failure injection, zero simulated releases and standalone install proof. Don't treat AEF 3.2 reference kernel as authenticated signing system.

Evaluate the one-line requirement user goal fairly: preserve user intent; separate interpretations from engineering constraints; mark unknowns; propose alternatives; anticipate failure domains; generate safe, testable architecture. Do not pretend to know the user's unstated requirements. For a software task, score architecture coverage separately from compilable verified implementation.

## C4-D: Integration and readiness

Allow optional AEF+RCIR only after independent benchmarks for each. Compare AEF-alone + ordinary repo retrieval vs +R1 vs +R2 using same task and model. Require positive interaction value rather than combining two unverified systems. Commercial readiness requires reproducible installation, data protection, tenancy, licensing, abuse prevention, pilot demand and real economics; do not use a cosmetically impressive website as a proxy.

## Explicit regression and integrity tests

1. `pytest` unit/integration commands are examples; verify repository's supported Python version, environment and dependencies before execution.
2. `python scripts/run_benchmark.py --help`: CLI should parse; does **not** prove live model usage.
3. `python scripts/run_benchmark.py --dry-run`: if supported, must return `SIMULATION_ONLY`, never official scored result.
4. An actual minimal real-model trial: must record provider model identity, non-null real usage where provider supports it, all retries and independent verification, no simulated fallback.
5. A proof listing lookup: every advertised id resolves or reports its evidence explicitly missing, with negative unauthorized path tests.
6. Route registry test: every routable stage has a valid handler and a receipt; missing handler causes preflight fail.
7. Provenance mutation test: changed target bytes rejected, not quietly rehashed into acceptance.
8. Critical task affected code: hidden evaluator receives no gold from retrieval index or agent context.
9. AEF stale evidence test: invalidate ancestor and all dependents; previous release gate demotes.
10. AEF approval test: model-generated `"approved":true` without genuine external gateway authorization blocks impactful write.

## Reviewer/owner acceptance checklist before any 'Proceed'

- Can an unfamiliar IDE agent identify what to do **without guessing missing paths or decisions**?
- Is the current SHA and branch explicit, or marked unverified?
- Is the permitted set of files explicit and limited?
- Is there a deterministic failure case and a reproducible acceptance test?
- Are the baseline and alternative on equal footing?
- Does code output depend on tests that the same agent can falsify?
- Can a role accidentally mark its own output independently verified?
- Can a model be tricked into skipping stages or using unavailable tools?
- Can we revert minimal patch without changing interpreter semantics?
- Are old metrics/CI runs clearly historical?
- Are model/API tokens, IDE credits and generated estimates kept distinct?
- Is user authorization scoped to this ticket only, with no silent progression?

If any answer is materially unknown: reject the plan for revision or mark the ticket blocked, not green.
