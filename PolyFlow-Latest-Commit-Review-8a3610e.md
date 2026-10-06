# PolyFlow RCIR v8.5 — Latest Commit Review and Fix Plan

**Review date:** 6 October 2026 (India)  
**Repository:** [paril-01/PolyFlow](https://github.com/paril-01/PolyFlow)  
**Reviewed commit:** [`8a3610e8bec25de6aa545f5391967f851fa3efa7`](https://github.com/paril-01/PolyFlow/commit/8a3610e8bec25de6aa545f5391967f851fa3efa7)  
**Parent:** `d14daaff946b4ecdecd499add3db11f7457188a5`  
**Commit title:** `feat: add RCIR v8.5 experimentation framework, evaluation scripts, and core modules`  
**Scope:** Review of the latest commit, affected core paths, benchmark evaluators, CI workflows, and committed evidence. No repository fixes were applied.

## Verdict

**Fix the benchmark's correctness and agent integration before treating `OPTION_B_ACCEPTED` as reliable evidence of architectural progress.** There are useful additions—centralized source-root configuration, explicit context metadata, provider integration, and saved trial artifacts—but multiple checks currently accept evidence that does not establish their stated claim.

The most consequential problems are:

1. Fresh checkout / CI initialization fails because the Nextcloud gitlink has no `.gitmodules` URL mapping.
2. The gate evaluator can accept zero source recall and agent summaries without trial evidence.
3. File-level ranking metrics double-count symbols from the same file.
4. The RCIR agent condition receives no initial compiled context because of mismatched field names; iterative retrieval has further schema mismatches.
5. Recorded agent trials contain command/path failures, so they do not isolate model capability.
6. New type-flow and canonicalization code has directly reproducible incorrect outputs.

This review does **not** establish that the entire architecture should be abandoned. It establishes that the current acceptance verdict and several metrics need correction and remeasurement.

## What was actually verified

The commit changes **108 files**, with **83,173 insertions and 103 deletions**; much of that volume is saved benchmark output. Review focused on changed executable code and the evidence supporting its claims, rather than treating generated output volume as implementation coverage.

| Check | Observed result | Interpretation |
|---|---|---|
| GitHub default branch and local checkout | Both identified `8a3610e` | Review is pinned to the latest main commit resolved for this task |
| `git submodule update --init` | Exit 128: `No url found for submodule path 'experiments/nextcloud_validation/nextcloud-server' in .gitmodules` | Reproduction blocker |
| `tests/test_rcir_v8_5.py` | **17 passed, 3 failed** | Failures require the unavailable Nextcloud checkout; many passes only inspect saved JSON |
| v8.3, v8.4, agent-loop and repository-tool suites | **26 passed, 2 failed** | Both failures are in older agent/tool tests |
| Same agent/tool suites at parent commit | **8 passed, same 2 failed** | Those two failures are pre-existing, not attributed to this commit |
| Ranking metrics recomputed from committed raw predictions | Match committed TEST metrics before correction | The metric implementation, rather than a transcription discrepancy, is the issue |
| Controlled direct-code reproductions | Confirmed gate bypass, context wiring mismatch, acceptance false positive, type-flow errors, double URI scheme | These are unit-level reproductions, not simulated benchmark successes |
| Context artifacts inspected across all splits | **14 snippet/hash mismatches** | 6 DEV, 4 VALIDATION, 4 TEST |

Tests ran with Python 3.12. The declared CI Python matrix was not reproduced here. No full Nextcloud benchmark or live Ollama trial was rerun: clean submodule initialization is broken and no live provider was used. Saved logs were examined as committed evidence, not represented as newly observed live inference.

## Metric implications

The following recalculations use the **existing saved predictions**, not a fresh benchmark or a newly selected ranker. File deduplication preserves the first occurrence of each nonempty file path and retains the evaluator's fixed denominators.

| TEST metric | Committed value | Diagnostic corrected value | Current contract |
|---|---:|---:|---:|
| Candidate-pool file recall | 100% | 100% | At least 90% |
| P@20, target file excluded | 11% | **7% after file deduplication** | At least 35% |
| P@50, target file excluded | 6.4% | **4% after file deduplication** | At least 20% |
| Graded nDCG@50 | 0.5820 | **0.4023 after file deduplication** | At least 0.50 |
| Dependency MRR | 0.4228 | 0.4255 after file deduplication | At least 0.70 |
| Critical source recall @4k | 56.67% | **50% when summary entries are excluded** | At least 60% |
| Recorded agent completion | 0% for both conditions | **Not a clean model-capability measurement** | Requires valid trial evidence |

The source-only figure is an artifact-based diagnostic: it excludes entries marked `summary` and requires `SOURCE_SPAN` and `source_exists`; it does not independently verify every delivered span against a materialized Nextcloud tree.

**Contract feasibility:** TEST tasks contain only 2–4 relevant dependency files after excluding the target, averaging 3. With file-level fixed-denominator precision, even perfect ordering has mean ceilings of **P@20 = 15% and P@50 = 6%** on these labels. The current 35% / 20% thresholds are unattainable under that interpretation. Decide whether the benchmark evaluates files or entities, build suitable labels, and freeze feasible thresholds before a new held-out evaluation. Do not merely lower gates until the current run passes.

## Prioritized findings

P1 means fix before accepting benchmark or product claims. P2 means a substantive correctness or reproducibility improvement. All source locations below refer to the reviewed commit; line ranges are supplied for navigation.

### F01 — P1: Clean checkout and updated CI cannot initialize the target repository

**Locations:** `.github/workflows/rcir-{unit,full-benchmark,smoke-benchmark,artifact-integrity}.yml`, checkout steps; repository root; `experiments/rcir_v8_5/scripts/environment.py:88–111`.

The commit enables `submodules: true` in all four workflows. Git tracks `experiments/nextcloud_validation/nextcloud-server` as a gitlink pinned to `da57df078d0808a7235a0177bd99d23c010b472e`, but the checkout contains no `.gitmodules`. The standard initialization command fails before the benchmark can run. The reproduction guide assumes an initialized submodule without providing a working bootstrap.

**Fix:** Commit the proper path/URL mapping for `nextcloud/server`, preserve the pinned gitlink, and document clean-clone initialization. Fetch any additional historical objects genuinely required by provenance validation.

**Acceptance:** A clean clone initializes the target, verifies its exact HEAD, passes environment sentinels, and reaches evaluation without manual local configuration. Exercise this in CI.

### F02 — P1: Formal gates do not enforce the contract they claim to enforce

**Locations:** `experiments/rcir_v8_5/scripts/evaluate_gates.py:108–137, 211–231, 274–322`; `contract/benchmark_contract.json`.

- `source_recall_passed` is computed but omitted from `context_gate["passed"]`. The committed result explicitly records `source_recall_passed: false` and `passed: true` for context.
- The agent gate trusts `is_simulation: false` and a status string. It does not validate per-trial nonempty diffs, acceptance transitions, regression results, or artifact completeness required by the contract.
- A controlled invocation with **zero source recall**, high ranking summaries, and an agent summary claiming completion with **an empty trials array** returned **`OPTION_A_ACCEPTED`**.
- Integrity failure writes `INVALID` but returns normally; the CLI therefore need not fail its CI step. Individual integrity flags are hardcoded `true` even when the overall integrity status fails.
- Option B's description requires at least 15% P@50 improvement, but no machine-readable improvement threshold/baseline comparison implements it. The hardcoded decision summary also says 92.5%/80% recall while current TEST artifacts say 100%/100%.

**Fix:** Make the decision function a pure, schema-validated evaluation of explicit contract rules. Include source recall; derive agent validity from verified trials; derive every integrity flag from its check; return nonzero for invalid runs. Make Option B's intended obligations explicit in the contract and derive narrative text from actual metrics.

**Acceptance:** Mutation tests separately break each obligation and confirm the relevant gate fails. Empty agent evidence cannot pass. Missing required artifacts fail the process. If Option B intentionally permits failed primary gates, the report must identify those exceptions precisely.

### F03 — P1: Ranking mixes entity predictions with file-level relevance and inflates scores

**Location:** `experiments/rcir_v8_5/scripts/retrieval_runner.py:331–419`.

Precision/DCG count each ranked entity as relevant whenever its file is relevant. Ideal DCG is constructed from unique expected files. Consequently, multiple symbols in one relevant file earn repeated gain against a file-level ideal ranking.

**Reproduction:** Twenty candidates from the same relevant dependency file produce `P@20 = 1.0` and **nDCG@50 = 7.0403**. A normalized DCG above 1 exposes the inconsistent units. The saved TEST recalculation is shown above.

**Fix:** For file evaluation, deduplicate by canonical path before ranking metrics. For entity evaluation, provide entity-level relevance judgments and construct the ideal ranking at that same level. Recompute validation selection as well as TEST results after correcting the metric. Revisit the infeasible thresholds before freezing the next benchmark.

**Acceptance:** Duplicate entities from one file cannot increase file-level gain; nDCG stays within [0,1]; target exclusion is tested with several target-file symbols; contract ceilings are checked against label cardinality.

### F04 — P1: The RCIR agent condition is not receiving the intended RCIR context

**Locations:** `experiments/rcir_v8_5/scripts/run_agent_validation.py:47–73, 283–293`; `scripts/context_runner.py:151–159`.

The writer emits `rendered_prompt_markdown`, but the agent runner reads `prompt_markdown`. On the committed DEV task this produces **0 characters** instead of the available **4,907-character** prompt.

Iterative retrieval also searches task IDs or a nonexistent `target_symbol` field, rather than the actual task/entry symbol data. Requesting `getThumbnail` returns zero entries. Entries contain `entity_id`, but deduplication reads `canonical_id`, so a task-ID lookup collapses entries onto the empty string and returns only one. The advertised `token_budget` is returned but not enforced by this adapter.

**Fix:** Define a shared serialized context schema, explicit agent-task-to-retrieval-task mapping, correct identity fields, and budget-aware retrieval. Reuse the production context provider where practical. Assert that the RCIR arm actually receives its intended intervention.

**Acceptance:** A real producer-to-consumer integration test delivers a nonempty initial prompt, finds `getThumbnail`, returns distinct unseen entities across requests, and enforces the requested budget. Record supplied context hashes/tokens per trial.

### F05 — P1: Recorded agent failures are contaminated by harness command errors

**Locations:** `scripts/run_agent_validation.py:121–167`; `agent_tasks/tasks.json`; `raw/agent/AGENT-TASK-01_{rcir,baseline}_rep1/` under `experiments/rcir_v8_5`.

Acceptance/regression commands are string-formatted and executed with `shell=True`. The committed acceptance log shows the Windows worktree path cut at the space in the user's profile directory, leading to “Target file does not exist.” The regression log shows a Python `unicodeescape` syntax error caused by an interpolated Windows path inside `python -c`.

Any nonzero acceptance exit is classified as a valid precondition failure, including a missing file or interpreter error. Thus the recorded zero completion rates cannot establish that the model failed a correctly executed task. The 5-turn and 8-turn results are also both populated from the same run aggregate rather than independent budgets or a justified replay analysis.

**Fix:** Use argument arrays with `shell=False`, `sys.executable`, an explicit working directory, and paths as arguments. Distinguish assertion failures from setup/execution errors; mark the latter `INVALID_TRIAL`. Honor task timeouts, clean up in `finally`, and run each claimed turn budget or label it unmeasured.

**Acceptance:** Test paths containing spaces/backslashes, a missing interpreter/script, a genuine failing acceptance assertion, and timeout cleanup. Infrastructure failures must never count as valid before/after transitions or measured model failures.

### F06 — P1: The acceptance test accepts an incorrect implementation

**Locations:** `experiments/rcir_v8_5/agent_tasks/verify_task1.py:18–31`; `agent_tasks/tasks.json`.

The verifier only checks that `$crop` occurs in the signature and somewhere in the body alongside `getPreview(`. It does not enforce a default of `true` or that the fourth preview argument is `$crop`.

**Reproduction:** A method with `$crop = false`, `$unused = $crop`, and `getPreview($file, $x, $y, true)` is incorrect for the requested task but the actual verifier prints `PASS` and returns 0. The “regression suite” only asserts the existence of `IConfig.php`.

**Fix:** Execute behavior-focused PHP tests for the default and explicit false values, and run relevant real regressions. If AST checking supplements this, validate the exact parameter default and call argument structurally.

**Acceptance:** Reject wrong defaults, unused parameters, comments containing expected strings, unchanged preview arguments, and syntax errors. Accept the requested behavior and verify both default and explicit-value paths.

### F07 — P1: New PHP flow handling reports incorrect types as proven exact

**Location:** `rcir/src/rcir/types/php_type_flow.py:313–369`.

`instanceof` narrowing happens before the branch snapshot and ignores whether the condition is negated. Closure parameters are written into the outer method environment and are not restored when the closure ends.

**Direct reproductions:**

```php
public function test($x) {
    if (!($x instanceof Foo)) {
        $x->run(); // Analyzer: Foo, proven_exact — invalid narrowing.
    }
    $x->run();     // Analyzer still reports Foo, proven_exact.
}
```

```php
public function test(Bar $x) {
    $callback = function(Foo $x) {
        $x->run();
    };
    $x->run();     // Analyzer: Foo, proven_exact; outer parameter is Bar.
}
```

**Fix:** Track lexical scopes and condition polarity. Snapshot the precondition environment before narrowing, narrow only valid branches, restore closure scope, and join types conservatively. Prefer abstention over an unsupported exact claim.

**Acceptance:** Cover positive/negative checks, post-branch use, nested closures, same-name parameter shadowing, `else`, early returns, and branch joins. Assert confidence as well as type.

### F08 — P1: Internal endpoint repair creates malformed double-scheme canonical IDs

**Locations:** `rcir/src/rcir/entities/legacy_normalizer.py:109–126`; `rcir/src/rcir/graph/canonical_graph.py:145–167`.

After changing an internal `external://` endpoint to `php://`, normalization falls through and adds another prefix.

**Direct outputs:**

```text
external://OCP\IConfig                  -> php://php://OCP\IConfig
external://lib/public/IConfig.php        -> php://php://lib/public/IConfig.php
```

This can split identity and strand graph traversal when those repaired endpoints are not already resolved by the registry.

**Fix:** Return a validated canonical URI after repairing the scheme, or normalize the scheme-free payload exactly once. Reject malformed/nested schemes.

**Acceptance:** Normalization is idempotent; internal symbols, internal file endpoints, and methods each round-trip to one canonical ID; genuinely external endpoints remain external. Test through `CanonicalGraph.add_edge`, not only the helper.

### F09 — P1: Context mutation leaves hashes and representation metadata stale

**Location:** `rcir/src/rcir/context/compiler.py:297–321, 334–379`.

The compiler computes `content_hash`, `estimated_tokens`, and `representation_type` when creating an entry. Budget downgrades/truncations then change its content without refreshing all those fields. A source entry downgraded to a summary may retain `SOURCE_SPAN` and its original hash/token estimate.

**Committed evidence:** SHA-256 of `content_snippet` disagrees with `content_hash` in **14 entries** across the three saved splits. For example, TEST summaries for `DataDisplayResponse.php`, `Folder.php`, and `AllConfig.php` retain source-span labels.

**Fix:** Centralize entry mutation/finalization. Recompute content hash, token estimate, span extent, resolution status, and representation after every downgrade/truncation, then validate the final serialized artifact.

**Acceptance:** For every final entry, hash equals delivered snippet bytes and token count equals the configured counter. Summary labels cannot claim source-span delivery; truncated spans describe the delivered extent.

### F10 — P1: “Critical source recall” gives credit for file-reference summaries

**Locations:** `experiments/rcir_v8_5/scripts/context_runner.py:137–148, 265–266`; `rcir/src/rcir/context/compiler.py:170–176, 297–303`.

Both `SOURCE_SPAN` and `STRUCTURAL_SUMMARY` count as source delivered. The summary implementation is a generated reference line describing a file/entity, not extracted source. Summary classification also takes precedence over the source-existence check. Together with F09, this overstates delivered source evidence.

Excluding summaries reduces committed TEST critical source recall from **56.67% to 50%** under the diagnostic described above.

**Fix:** Separate file-reference coverage, structural-summary coverage, and actual source-span coverage. Source recall must require a verified existing file and resolved delivered source bytes; summary-only references get no source credit.

**Acceptance:** A missing-file summary and a present-file reference-only summary both contribute zero source recall. A real verified span contributes according to a clearly documented file/span relevance rule.

### F11 — P1: Claimed semantic discovery channels contain benchmark-specific answers

**Location:** `experiments/rcir_v8_5/scripts/retrieval_runner.py:160–259`.

The event channel adds three fixed Nextcloud files for any event task. Config discovery adds four fixed files. Boundary discovery uses one fixed routes file. Verification includes fixed `ManagerTest.php` and `SessionTest.php` candidates. These candidates are labelled `static_exact` without proving the stated relationship for the requested target.

Channel B, named type flow, checks class/interface aliases and suffix matches; it does not consume receiver-analysis output. Nonzero channel counters therefore do not prove that seven independent semantic mechanisms worked. This is a benchmark-specialization/confidence issue; it is not evidence that runtime code directly reads expected-file labels into its candidate list.

**Fix:** Extract relationships from the indexed source and carry source evidence into candidates. Keep useful framework conventions in explicit versioned adapters, mark heuristic evidence honestly, and measure their contribution through ablations. Wire type-flow results into retrieval if that is the intended channel.

**Acceptance:** Moving/removing a relevant registration changes discovery; an unrelated event does not inherit all hardcoded dispatchers as exact dependencies. Demonstrate channel-specific incremental recall on unseen tasks and a second repository before making generalization claims.

### F12 — P2: Provenance and report invariance do not bind results to the executed inputs

**Locations:** `scripts/reconstruct_ground_truth.py:36–41, 465–487, 1110–1133`; `scripts/validate_ground_truth_provenance.py:35–140`; `scripts/evaluate_gates.py:51–108`; `scripts/generate_reports.py:90–104`, all under `experiments/rcir_v8_5`.

The reconstruction script creates handwritten task expectations, sets every task's upstream commit to the current target HEAD, uses hardcoded parent SHAs, and records `diff_files` from label lists rather than a Git diff. File existence and hashes establish source identity, not the correctness/completeness of a change-impact label set. The auditor does not implement its advertised parent/author/date verification. Expected-file hashes are optional in its checks.

The gate mainly compares a reusable run ID and saved statuses. It does not verify the manifest's dataset/graph/config hashes against the actual inputs; `candidate_config_hash` itself is a hash of a constant string. Saved results identify the parent PolyFlow commit, which can be legitimate for a dirty development run only if the executed working-tree state is also captured accurately.

Report generation injects the *current* environment's PolyFlow commit, while committed reports reference the parent commit. Therefore byte comparison is not a stable reproduction of a historical run once checked out at the new commit, even if its recorded metrics are unchanged.

**Fix:** Distinguish manually adjudicated source tasks from historical-change-derived tasks. Validate real Git metadata when claimed. Bind each run to immutable input hashes plus executed source state; fail on missing hashes. Generate reports from the recorded immutable run manifest, and separately validate that the environment matches when rerunning.

**Acceptance:** Changing a dataset, graph, config, source state, or parent SHA without updating the corresponding run makes integrity fail. Historical reports regenerate identically from their recorded inputs. Manual labels do not claim independent historical-diff validation without evidence.

### F13 — P2: Receiver evaluation can match the wrong call site and overstate correctness

**Location:** `experiments/rcir_v8_5/scripts/evaluate_type_flow.py:78–115, 152–183`.

The evaluator reads a fingerprint but does not use it. It first matches within ±5 lines, then falls back to any occurrence of the same receiver/method anywhere in the file. Distinct calls using the same variable and method can therefore borrow each other's predicted type. Suffix matching also accepts types without verifying an actual inheritance/interface relation.

The coverage numerator includes `wrong_exact` counts from expected-abstention cases, while the denominator excludes abstention cases; adversarial inputs can therefore produce coverage above 100%.

**Fix:** Use a stable call-site identity tied to the source hash/span/fingerprint. Mark stale or ambiguous identity invalid rather than substituting another site. Resolve compatibility from the type graph. Define confusion-matrix denominators per population.

**Acceptance:** Repeated same-name calls at different locations cannot cross-match; stale fingerprints fail; unrelated same-suffix types are incompatible; coverage remains within [0,1]. Reevaluate the 12-call-site result after these fixes.

## Additional enhancements and validation gaps

| Priority | Change | Reason and completion criterion |
|---|---|---|
| P2 | Replace artifact-only assertions with behavioral regressions | `tests/test_rcir_v8_5.py` largely asserts stored values. Its “nDCG penalizes late must-change” test only checks `ndcg > 0`; its missing-source test checks a stored rate. Exercise actual ranking, missing-source handling, and gate transitions. Also allow the implemented `AnchorCoverageRRF` selection in the configuration test. |
| P2 | Test the actual frozen ranker for determinism | `evaluate_determinism.py:68–69` declares the selected-config path but always constructs R0. R0 is the current saved winner, so this is a latent failure for another winner. Share the ranker factory and run fresh processes with varied hash seeds; five iterations in one process do not prove cross-process determinism. |
| P2 | Make strict-budget behavior precise | Direct `compile([], token_budget=1)` returns about 30 counted tokens because the header alone exceeds the budget. Final prompt metadata is also updated after the last count. Reject infeasible budgets or return an explicit empty/insufficient-budget result; recount the finalized serialization. This does not establish a violation in the saved 4k runs. |
| P2 | Preserve tokenizer provenance | Default counting can fall back to characters/3.7; `cl100k_base` also does not establish exact token use for the selected Qwen model. Record the actual counter in every benchmark result and distinguish estimated budget compliance from model-token compliance. |
| P2 | Separate fresh execution from artifact verification in CI | Full benchmark workflow regenerates some artifacts but reuses committed agent/performance evidence and does not regenerate reports before the final comparison. Give each run a unique input-bound identity and explicitly mark unexecuted stages `NOT_MEASURED`; do not mix new and old evidence into one current verdict. |
| P2 | Expand agent evaluation after wiring is fixed | One task and one replicate per condition cannot substantiate token-savings or capability claims. Use paired tasks, multiple repetitions, controlled model/options, a capable free/local provider where available, and confidence intervals. Keep failed tasks in the analysis. |
| P2 | Strengthen holdout boundaries | Ground truth for all splits is loaded in the retrieval process and TEST candidates are built before selection; `test_visibility: false` is a literal field. This alone does not prove test-label tuning occurred. Enforce separate selection/evaluation interfaces and check overlap by task semantics/files as well as task IDs. |

## Existing failures, not introduced by this commit

Both of the following fail at the parent commit as well as at the reviewed commit:

- `tests/test_agent_loop.py::TestAgentLoop::test_react_loop_execution` — expected success is false.
- `tests/test_repo_tools.py::TestRepoTools::test_edit_file_and_diff_and_revert` — asserted edit-response wording differs from the implementation.

Track these separately. Update the message assertion only after deciding the response contract; inspect the agent-loop failure before changing its expectation. They should not be described as v8.5 regressions.

## Recommended implementation order

1. **Restore reproducibility:** Fix F01; make a clean checkout and explicit benchmark prerequisites work.
2. **Repair the evaluator:** Fix F02, F03, F10, F12 and F13 before trusting new scores. Decide metric units and freeze a feasible contract for the next held-out run.
3. **Repair core correctness:** Fix F07, F08 and F09 with focused counterexamples. Keep unsupported cases uncertain.
4. **Repair real agent execution:** Fix F04–F06; demonstrate a valid acceptance fail-to-pass transition and actual RCIR context delivery in isolated worktrees.
5. **Remove benchmark-specific shortcuts:** Fix F11 and run channel ablations, then extend to genuinely unseen tasks/repositories.
6. **Regenerate evidence once:** Run the full pipeline under a new immutable run ID, execute the actual behavioral tests, and regenerate reports from that run. Preserve the old artifacts as superseded evidence instead of silently relabelling them.

## Release / claim checklist

- [ ] Fresh clone and submodule initialization succeed without local-only configuration.
- [ ] Every mandatory contract failure blocks its corresponding acceptance decision and invalid runs exit nonzero.
- [ ] File/entity metric units and thresholds are consistent; duplicates cannot inflate gain.
- [ ] Context hashes, spans, representations and counts describe exactly what is delivered.
- [ ] RCIR agent trials demonstrably receive context; infrastructure errors are invalid trials.
- [ ] Acceptance tests reject the demonstrated incorrect implementation and relevant regressions execute.
- [ ] Type-flow and canonicalization counterexamples pass with correct uncertainty/identity.
- [ ] Provenance verifies actual input hashes and executed code state.
- [ ] Claims distinguish source recall, reference coverage, provider reachability, valid agent trials and verified completion.
- [ ] Fresh benchmark output supports the final verdict; no fixed success text or inherited stale results substitute for measurement.

## Minimal reproduction commands

Run from a checkout pinned to the reviewed commit, with `pytest` available:

```bash
git rev-parse HEAD
git submodule update --init
PYTHONPATH=rcir/src:experiments/rcir_v8_5/scripts python -m pytest tests/test_rcir_v8_5.py -q
PYTHONPATH=rcir/src python -m pytest tests/test_rcir_v8_4.py tests/test_rcir_v8_3.py tests/test_agent_loop.py tests/test_repo_tools.py -q
```

Inspect stale delivered-content hashes without Nextcloud or an LLM:

```python
import hashlib
import json
from pathlib import Path

root = Path("experiments/rcir_v8_5/raw/context")
for split in ("dev", "validation", "test"):
    tasks = json.loads((root / f"{split}_contexts.json").read_text())["tasks"]
    mismatches = [
        (task_id, entry["entity_id"])
        for task_id, task in tasks.items()
        for entry in task["entries"]
        if hashlib.sha256(entry["content_snippet"].encode()).hexdigest()
        != entry["content_hash"]
    ]
    print(split, len(mismatches))  # 6, 4, 4 at the reviewed commit
```

All findings are grounded in the pinned source, committed artifacts, or the explicitly described direct-code reproductions. The review is not a certification of untouched modules or a claim of complete end-to-end benchmark execution.
