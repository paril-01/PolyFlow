# PF-RP-01 hosted CI checkpoint

PHASE: PF-RP-01 CI and proof integrity. Full-plan implementation is incomplete.

REPO/SHA/BRANCH/DIRTY: `paril-01/PolyFlow`, tested code `b005cf4bdfea6943d78a21707e6634d604adef0c`, branch `work/pf-rp-01-proof-integrity`. This branch has been pushed and its remote SHA verified. Documentation-only receipt followups may be descendants. The owner's pre-existing staged recovery document and modified target submodules remain excluded from commits.

AUTHORIZATION: Owner explicitly requested implementation of the entire attached master plan and pushing changes. Scoped work-branch commits and CI-triggering pushes were performed. No main write or merge occurred. A failed factual gate is not converted into approval by this authorization.

FILES READ: [master plan](../../PolyFlow_RCIR_Master_Implementation_and_Proof_Plan.md), [phase skill](../../.agents/skills/polyflow-phase-execution/SKILL.md), [baseline](./BASELINE.md), [progress](./PROGRESS.md), four workflows, historical manifest, gate evaluator, raw-hash helper, proof registry and regression tests. [Ticket ownership](./PF-RP-01.json) records the inspected scope.

## Evidence table

| Check at b005cf4 | OBSERVED_EXECUTION | Source |
|---|---|---|
| Smoke | PASS | [GitHub run 45765529739](https://github.com/paril-01/PolyFlow/actions/runs/45765529739) |
| Unit/static Python 3.10, 3.11, 3.12 | All three jobs PASS | [GitHub run 45765529708](https://github.com/paril-01/PolyFlow/actions/runs/45765529708) |
| General CI | PASS: Linux validation, Windows validation and React build | [GitHub run 45765529787](https://github.com/paril-01/PolyFlow/actions/runs/45765529787) |
| Artifact integrity | FAIL on both OSes, one remaining violation each | [GitHub run 45765529717](https://github.com/paril-01/PolyFlow/actions/runs/45765529717) |

The exact remaining failure on BOTH platforms is:

> INTEGRITY_FAILURE: PolyFlow working tree was dirty during execution (formal release benchmark requires clean tree)

This is the **historical** manifest's `polyflow_dirty: true`, not an assertion that these new CI checkouts were dirty. Its original digest and flag are preserved. [Linux raw job log](../../experiments/runs/pf_rp_ci_20261126/final-artifact-job-139725410702.log) and [Windows raw job log](../../experiments/runs/pf_rp_ci_20261126/final-artifact-job-139725410905.log) record the failure and actual exit 1. Provenance validation and report invariance passed before this gate.

PLAN: repair real cross-platform code defects, then verify the same required checks on hosted Windows and Linux. Alternative of changing historical `dirty` to false or disabling its clean-release test is rejected because it would falsify source history. The decision between historical replay verification and fresh release eligibility must be explicit before the next phase.

CHANGES: frozen proofs now deliver bytes matching their exact recorded LF or CRLF digest; raw versus reconstructed-delivery identities are separate. Historical gate comparisons permit only explicit uniform UTF-8 EOL reconstruction, never substantive edits, binary transformations, or a replacement expected hash. Current-run raw hashing is unchanged. The clean-release guard remains intact and has a regression control. CI now runs on this exact work branch, without relying on inaccessible PR-creation integration permissions.

COMMANDS / TESTS:

- `python -m pytest tests/test_backend_proof_server.py tests/test_evidence_registry.py -q`: exit 0, 53 passed and 2 Windows symlink skips; [log](../../experiments/runs/pf_rp_ci_20261126/proof-eol-both-directions.log).
- `python -m pytest tests/benchmark_integrity/test_historical_hash_policy.py tests/benchmark_integrity/test_historical_provenance_gate.py -q`: exit 0, 18 passed; [log](../../experiments/runs/pf_rp_ci_20261126/historical-eol-dirty-control.log).
- Exact executable argv, duration, exit and log path: [command ledger](../../experiments/runs/pf_rp_ci_20261126/commands.jsonl).
- Each hosted run above provides its exact commands, runner versions, step outcomes and native logs. No hosted result is inferred from a local test.
- `git push origin work/pf-rp-01-proof-integrity`: succeeded; `git ls-remote origin refs/heads/work/pf-rp-01-proof-integrity` matched the tested SHA. Initial PowerShell stderr handling returned a misleading shell error despite successful push; remote verification resolved it. Later pushes were directly successful.
- GitHub PR creation: HTTP 403 from integration. Alternative GitKraken PR creation: NOT_EXECUTED, not authenticated. No PR was created. Work-branch push triggers run the same workflows without weakening jobs.

RISKS/BLOCKERS: PF-RP-02 through PF-RP-11 have not started. R2 invalidation remains an observed later-ticket failure. Product retrieval, real MCP/CLI hardening, isolated live harness, independent dataset, optional compression, locked study, native IDE study and product proof are NOT_COMPLETE. Live success/token/cost/credit improvements are NOT_MEASURED. Paid provider resources were not used. A historical replay may be byte-consistent yet remain release-ineligible; the current phase ordering makes later implementation depend on that historical release decision. No silent reinterpretation has been applied.

PROHIBITED ACTIONS: no raw historical result/manifest rewrite, no changed expected hashes, no disabled failure test, no interpreter/SDK change, no main write, no merge, no fabricated independent review or benchmark receipt. Pre-existing user files and target checkouts were preserved.

GATE STATUS: BLOCKED_BY_HISTORICAL_DIRTY_RELEASE_EVIDENCE. The code-level cross-platform failures were repaired; the factual release-eligibility failure remains. This is not full implementation completion or release approval.

NEXT ACTION: await the owner's requested decision: (1) separately verify historical replay while keeping this dirty historical run ineligible and requiring fresh proof before release, or (2) retain the current strict gate and produce a genuinely fresh clean evidence set first. No later phase is self-approved. The [phase skill](../../.agents/skills/polyflow-phase-execution/SKILL.md) explicitly states, "You cannot skip a phase or self-approve past a gate."
