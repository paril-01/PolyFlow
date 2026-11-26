# RCIR proof baseline and current recovery

PHASE: PF-RP-00 baseline, followed by scoped PF-RP-01 implementation.

REPO/SHA/BRANCH/DIRTY: `paril-01/PolyFlow`, input SHA `6a586e16007cb1bed123619b4494067f99eccf2f`; current branch `work/pf-rp-01-proof-integrity`. Pre-existing user changes: staged recovery-pack document, untracked master implementation plan, changed Flask/Requests gitlinks and dirty OpenTelemetry checkout. These were preserved. Remote main was freshly resolved as `57a23c59877bd1775171f135fd9512f1b9eb2eb3`, not the local input SHA.

AUTHORIZATION: Owner's current request explicitly authorizes evaluation followed by implementation from the attached plan, with logs and progress. Local scope is recorded in [PF-RP-01.json](./PF-RP-01.json). This does not authorize paid calls, push, merge, release, architecture selection, or treating failed gates as passed.

FILES READ: [root rules](../../AGENTS.md), [phase skill](../../.agents/skills/polyflow-phase-execution/SKILL.md), [master implementation plan](../../PolyFlow_RCIR_Master_Implementation_and_Proof_Plan.md), [v3 execution specification](../MASTER_IDE_EXECUTION_SPEC.md), [work packages](../WORK_PACKAGES_AND_ACCEPTANCE.md), [historical phase state](../../templates/PHASE_STATE.json), [previous implementation report](../../reports/recovery/PF_RC_CI_001_IMPLEMENTATION.md), CI workflows, provenance reader/validator/environment, proof registry/routes/health/schema/tests, R1 adapter, bakeoff runner, MCP adapter, VEST-lite, context provider, live/wrapper CLIs, isolation, provider/metrics code, repository tools, gate/report generator and related tests. Native GitHub job logs for all four cited failed workflows were retrieved and saved in this run.

## Evidence table and requirement mapping

| Finding | Classification and evidence | Current disposition |
|---|---|---|
| F01 provenance | OBSERVED_EXECUTION: current Windows validator exits 0 against pinned Nextcloud objects. Historical GitHub provenance jobs failed before this local fix. | Reuse committed PF-RC-CI-001; do not rewrite recorded hashes or reimplement it. Linux result is separately recorded in the command ledger. |
| F02 proof 404 | OBSERVED_SOURCE + OBSERVED_EXECUTION: index hashes match CRLF historical bytes; LF Git blobs differ. Historical native CI log confirms first proof 404. | Repaired: verified bytes, explicit raw/delivery digest policy, all path branches checked, unavailable records labeled, no static validated health. |
| F03 unfair deterministic harness | OBSERVED_SOURCE: target hint in query, missing-target fallback, max(1, tasks), hardcoded invalidation percentage, winner does not compare both alternatives. | Open, PF-RP-02. No rerun overwriting old bakeoff receipt. |
| F04 R1 integration | OBSERVED_SOURCE: adapter accesses `context_units`, broad exception fallbacks; canonical delivery uses entries. | Open, PF-RP-02; zero historical recall is not excused or promoted. |
| F05 MCP truthfulness | OBSERVED_SOURCE: first 45 file lines, character budget and exact tokenizer/freshness labels. | Open, PF-RP-04. Existing contract tests are insufficient to claim a real MCP client invocation. |
| F06 lifecycle | OBSERVED_EXECUTION: existing adversarial test leaves `UserController.php::getUser` FRESH after base invalidation; exit 1. Source expands dependencies only once. | Open, PF-RP-03. No source change outside current recovery ticket. |
| F07 provider freshness | OBSERVED_SOURCE: provider constructed before per-trial worktrees; graph revision guard runs only when graph metadata is present. | Open, PF-RP-03/05; no valid fresh live claim. |
| F08 oracle/evaluator | OBSERVED_SOURCE: public tasks path also initializes evaluator; manifest assigns same digest to public tasks and hidden oracle; verify-only selects first task. | Open, PF-RP-05. Existing public tasks are DEV only. |
| F09 isolation | OBSERVED_SOURCE: pinned Nextcloud identity, shared Git worktrees and local-clone fallback. | Open, PF-RP-05. No OS isolation certification or blind trial. |
| F10 telemetry | OBSERVED_SOURCE: fixed arm order and missing-usage zero defaults appear in runner/provider; actual settings and native request usage not independently run. | Open, PF-RP-05/07/09. Savings and success NOT_MEASURED. |
| F11 search containment | OBSERVED_SOURCE: walker directly opens found files rather than checking each through the safe resolver. | Open, PF-RP-05. Proof resolver containment is repaired separately; repo search exploit was NOT_RUN. |
| Historical report contradiction | OBSERVED_EXECUTION: report validator initially exits 1; saved final assessment says VALID/OPTION_B_ACCEPTED while its input JSON says INVALID and contains a malformed target commit. | Old report preserved byte-for-byte; only derived assessment regenerated to reflect its actual input. Validator now exits 0. This is not a fresh experiment or a success claim. |
| Historical test side effects | OBSERVED_EXECUTION/SOURCE: integrity tests wrote gate/integrity JSON into tracked results. | Outputs copied to this audit run and original clean files restored; historical tests now evaluate in copied temporary results and assert originals unchanged. |
| Windows argv quoting | OBSERVED_EXECUTION: repo command test exited 0 without expected stdout; selected Python PATH did not fix it. Non-POSIX shlex retained wrapping quotes. | Minimal wrapper-quote removal before subprocess argv; output and quoted-executable regression checks pass. |

## Tool and environment evidence

See [inventory.log](../../experiments/runs/pf_rp_01_20261126T014922/inventory.log). Windows CPython 3.12.2 was explicitly selected. Git 2.53.0.windows.2, VS Code 1.147.0 (build hash recorded), Node 25.8.0 and PHP 8.3.33 were executed. Composer and gh were not on PATH. Docker CLI is installed but its Linux engine connection failed. Ubuntu WSL is available; its Python is 3.12.3. WSL emits pre-existing PATH translation warnings; successful commands remain separately identified by exit code.

Local Ollama `/api/tags` was read without inference: installed model names/digests are in the inventory. This does not prove coding capability. No model downloads, paid model calls or live coding trials were performed. Exact model ID serving this chat is UNVERIFIED because no native runtime model-ID receipt is exposed. Agent identity is Codex; do not substitute an assumed model version.

The environment installer initially reported success for dependencies without making them available to selected CPython. This was detected by fresh collection failures. Explicit CPython pip installation and its raw log are saved. Final package versions are captured separately. There is no successful test claim based on a failed collection.

`git submodule status` reports uninitialized registrations, while direct Nextcloud Git inspection resolves its standalone checkout to the pinned SHA and the environment verifier reports it clean. Do not initialize/reset user target folders to hide this distinction. Flask/Requests/OpenTelemetry are not certified clean benchmark targets by this audit.

Historical performance receipt and run manifest have different run IDs and PolyFlow revisions; do not merge their metrics. The old phase-state SHA/branch disagree with the actual checkout; it remains preserved as historical state. The current ticket and append-only ledger govern this run. Standalone AEF was not audited or changed; it remains a separate repository.

## Plan and alternative

PLAN: first repair reproducibility and secure proof availability, then request independent CI review. Reuse existing provenance repair. Stronger simpler alternative to any retrieval redesign remains R0; no architecture winner is selected. Historical CRLF proof bytes are reconstructed only when the exact recorded digest matches UTF-8 LF reconstruction, with a named delivery policy and separate raw digest. Raw byte verification remains mandatory; tampering, binary mismatches and mixed-ending reconstruction fail closed.

CHANGES: exact ownership is in the ticket and final scoped diff. Source repair covers proof registry/HTTP routes/health/schema, Windows command quoting, isolated historical-gate tests, proof/tool regression tests, Windows/Linux CI matrix and missing submodule checkout, and the contradictory derived assessment. No interpreter or SDK source changed.

COMMANDS / TESTS: [commands.jsonl](../../experiments/runs/pf_rp_01_20261126T014922/commands.jsonl) contains exact argv, start time, duration, exit code and log path for every logged command, including failed attempts. [PROGRESS.md](./PROGRESS.md) summarizes latest results. The pytest synthetic fixtures are integrity controls, never empirical benchmark tasks.

RISKS/BLOCKERS: hosted workflows have not run on this uncommitted patch; independent review remains required. R2 lifecycle test is still failing in its later-ticket scope. Native IDE study, independent held-out dataset, calibrated live model and isolation are outstanding. The historical INVALID report input is preserved, not reclassified as fresh valid evidence. Archived test-generated JSON is explicitly synthetic evaluation output.

PROHIBITED ACTIONS: no push, merge, release, paid inference, hidden-gold modification, repository merge, or interpreter/SDK change. Existing tests temporarily overwrote two historical outputs; this was detected, saved as test-generated output and restored, then the offending tests were isolated. No persistent raw-result/manifest change remains; final Git checks record this explicitly.

GATE STATUS: BASELINE_CAPTURED for PF-RP-00; PF-RP-01 local repairs verified where logs say so, hosted CI and independent acceptance pending. No self-promotion to PF-RP-02 or benchmark readiness.

NEXT ACTION: review the scoped patch and authorize publishing this branch for the four required CI workflows; address failures against the same ticket. After acceptance, PF-RP-02 repairs the harness/R1 integration. PF-RP-03 then fixes invalidation and source-bound lifecycle before production MCP or live evidence.
