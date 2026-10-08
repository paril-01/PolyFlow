# PolyFlow — Single Final Implementation Prompt
## Evidence-First Benchmarks → Real Backend → Minimal Live Showcase → ERPNext Conversion

**Send this entire file, as one prompt, to the coding agent working inside the PolyFlow repository. Do not split it into ticket prompts.**

**Repository:** `https://github.com/paril-01/PolyFlow`  
**Last independently reviewed commit:** `3a29cebe9732f91c60d4dd78844d8a5d0039104e`  
**Execution rule:** Check the actual HEAD before making changes. If newer commits exist, inspect them and reconcile the findings below against current code. Fix only still-present defects. Preserve useful existing work rather than replacing it blindly.

---

## 0. Role, mission, non-negotiable constraints

You are the implementation, testing, and evidence-verification agent responsible for getting PolyFlow ready for a technical presentation. Execute the tasks in this single file in order; do not respond with more plans or distribute the work across many new prompts. Make real code changes, run real tests where the environment permits, and produce reproducible final artifacts. Where execution is unavailable (e.g. local Ollama/ERPNext fixtures missing), mark evidence `NOT_MEASURED` with the exact missing dependency and runnable reproduction command. **Never replace an unavailable test with a successful mock.**

PolyFlow's original objective comes first: a business capability distributed across frontend, backend, data models/persistence, framework events/configuration, and tests should become **one cohesive feature-oriented `.poly` entry point** while retaining and linking its actual native source. The custom interpreter executes a validated multi-language workflow; RCIR selects minimal relevant code context for an AI agent. ERPNext/Frappe is the extreme external system that must test this claim.

**No fabrication, no benchmark-answer leakage, no marketing-only percentage, no synthetic pass, no scripted fake patch, no hardcoded UI metrics, no manually restamped artifacts, no duplicated before/after data, no passing an unexecuted benchmark.**

A real measured FAIL is more valuable than a manufactured PASS. Optimize performance legitimately, without tuning on held-out TEST. Do not change task labels or thresholds to manufacture approval. When invalid, show INVALID. When no measurements, show NOT_MEASURED. When a deliberately injected failure runs on real code, label the test as a **CONTROLLED LIVE FAILURE INJECTION**, not a production incident.

**Priorities are strict:**
1. Truthful benchmarks and actual RCIR A/B results.
2. Backend API serving validated raw proof files, including CSV and openable/downloadable links.
3. Minimal responsive UI based on backend events and measurements.
4. ERPNext-wide `.poly` mapping and progressively verified execution parity.

Keep all new dependencies free/open source where possible. Reuse code under `rcir/`, `orchestrator/`, `polyflow/`, `polyflow-sdk/`, `experiments/`, and `showcase/` instead of creating competing systems. Do not ask for confirmation at each phase: implement as far as the actual environment allows, reporting blockers precisely.

---

## 1. Mandatory first task: audit, baseline snapshot, and evidence quarantine

1. Run `git rev-parse HEAD` and `git status --porcelain`. Capture exact PolyFlow commit and diff/dirty state, plus exact Nextcloud, Frappe and ERPNext target revisions when present.
2. Inspect current implementation before modifying it, especially:
   - `experiments/final_blind_validation/run_blind_benchmark.py`
   - `experiments/final_blind_validation/access_guard.py`
   - `experiments/final_blind_validation/generate_after_fix_and_delta.py`
   - `experiments/final_blind_validation/{manifest.json,test_design.json,source_inventory.json}`
   - `experiments/rcir_v8_5/scripts/{run_agent_validation.py,run_formal_benchmark.py,evaluate_gates.py}`
   - `experiments/rcir_v8_5/agent_tasks/verify_regression.py` and `verify_task*.py`
   - `orchestrator/{agent_loop.py,tools.py,providers.py,telemetry.py}`
   - `rcir/src/rcir/adapters/frappe_erpnext.py`
   - `scripts/{build_showcase.py,build_showcase_data.py}`
   - `rcir/visualizer-react/`
   - `showcase/data/`, `FINAL_BLIND_VALIDATION_REPORT.md`, `FINAL_SYSTEM_ASSESSMENT.md`
3. Preserve existing result files as **historical evidence**; do not overwrite them. Label unvalidated/contradictory ones `HISTORICAL_UNVERIFIED` in the new proof index. Exclude them from headline metrics.
4. Freeze and hash the current benchmark/test design and source inventory. Keep source commits and configuration hashes immutable within a single formal run.
5. Create unique run-scoped output under `experiments/runs/<run_id>/` outside tracked source or within an ignored generated directory. Do not treat a dirty development run as a clean release benchmark.
6. Save `AUDIT_FINDINGS.md` mapping every defect to exact source path, root cause, correction, and regression test. This is an output of this same task, not a separate prompt.
7. A blind evaluation must keep prior reports, historical predictions, and answer files away from the model/task-execution process. A Python guard function that nobody calls is **not** an enforced security boundary. Prefer a physically sanitized evaluation worktree/process with allow-listed inputs. Record file access policy, input hashes, enforcement log, and hidden task design.

### Historical issues to verify at HEAD (do not assume fixed)

- The earlier blind RCIR arm used **only a textual tier hint**, not actual RCIR context. The RCIR provider and compiled context were not connected to the trial.
- The “after-fix” data was copied from baseline trials, rather than coming from a second execution.
- `blind_baseline.json` reported **3 valid pairs, 0 successful pairs**, while UI data claimed **5 valid pairs** even with timeouts.
- The baseline allegedly predating the `os` crash fix was actually run after that repair.
- Frozen test-design hashes differed across manifest, after-fix results and report.
- `verify_regression.py` performed PHP syntax checks and incorrectly represented them as full regression tests.
- UI data generators hardcoded candidate scores, graph counts, line counts, latency, coverage, interpreter receipts, and fallback outcome.
- `FINAL_SYSTEM_ASSESSMENT.md` overstated agent modifications/approvals and conflated overall architecture verdict with agent gate.
- `run_agent_validation.py` derived semantic status from nonexistent `ab_result['valid_pairs']`, resulting in fail-open/fail-confused accounting.
- `run_formal_benchmark.py` could default a stage to PASS when no semantic result was emitted.
- ERPNext Feature Closure assigned arbitrary partial coverage (for example 0.85 when no hooks found), used placeholder hook source hashes, and sometimes emitted absolute Windows paths.
- Showcase tests asserted expected constants and selected results rather than deriving assertions from independently measured evidence.

---

## 2. P0: rebuild a real, defensible benchmark harness

### 2.1 Mandatory separation of phases

Implement:

```text
pre_fix_historical/      # archival only unless actually rerun on pinned old commit
current_blind_baseline/  # new unmodified current-code baseline with real execution
rectified_validation/    # development fixes and DEV/VALIDATION checks
frozen_release_test/     # final fresh held-out execution after parameters frozen
```

A true before/after metric is permitted only when the same frozen task set was executed separately at both states, with distinct run IDs, timestamps, commits, raw traces, and usage records. Otherwise label the old figure as historical, not experimentally compared.

### 2.2 Real RCIR condition, not a prompt decoration

In `run_blind_benchmark.py` and the agent runner:

- **Baseline:** same model, same tool definitions, same task, same starting target commit; no RCIR retrieval context. Its normal repository-search tools remain available.
- **RCIR:** same everything else; instantiate the real repository graph/index, ranker and `ContextCompiler` / `ConcreteRCIRContextProvider`, and attach that provider to the `RepoToolEnvironment` actually used by the agent. Give the agent genuinely retrieved context.
- Use an explicit `ContextRetrievalResult` contract for both initial and on-demand context, including rendered markdown, selected paths/spans, content hashes, token budget, tokens delivered, duplicates skipped, and request provenance.
- Capture whether and when the agent invoked RCIR tools, and distinguish provided context from actually consumed model input.
- If RCIR cannot load or retrieve, mark the RCIR trial `INVALID_RCIR_SETUP`, not a baseline-equivalent run.
- Write an RCIR-side proof chain per trial:
  `retrieval_request.json`, `candidates.json`, `ranked_files.csv`, `context.md`, `context_manifest.json`, `provider_usage.jsonl`, `tool_calls.jsonl`, `diff.patch`, `acceptance.json`, `regression.json`, `gatekeeper.json`.
- Validate that `context.md` content/hash is really attached to a provider message or returned by a tool, not merely written to disk.

### 2.3 Paired fair execution

At least 5 independent meaningful coding tasks; more and 3+ repetitions if provider capacity permits. Same model, temperature, seed where supported, timeouts, token budget, max turns, worktree commit, task text, verifier, and editing tools in both conditions. Rotate the condition order to minimize order/cache effects. Record cache status. Run baseline and RCIR on isolated **full native git worktrees** of the same upstream commit; never initialize a new tiny git repository from copied `lib`/`apps` folders and call it equivalent to the real target.

Task set must be independently sourced, preferably from real historical Nextcloud changes with an earlier parent checkout, hidden gold patch, non-leaking change request, and upstream or independent behavioral tests. Do not expose expected files, gold diffs, task scripts, previous outcomes or test labels to the agent.

### 2.4 Validity and success rules

Distinct states:

```text
VALID_EXECUTION
INVALID_PROVIDER_TIMEOUT
INVALID_RCIR_SETUP
INVALID_TOOL_FAILURE
INVALID_PROVENANCE
INVALID_TEST_SETUP
COMPLETED_BUT_FAILED_TASK
COMPLETED_AND_PASSED_TASK
```

A valid pair requires both arms to have no runtime/provider/tool/provenance errors, provider-native or appropriately labeled exact usage, identical frozen task configuration, and complete raw traces. **A timed-out trial with partial token counts is not a valid completed trial.** Retain its partial telemetry separately.

Success requires actual nonempty diff, one or more real editing tool calls, acceptance before = expected failure, acceptance after = pass, appropriate compile/syntax pass, independent targeted behavioral tests pass, relevant regression pass, no new violations, and Gatekeeper approval. “No PHP syntax error in unchanged file” is not success.

### 2.5 Correct evaluation statistics

Show separately:

- individual executions, attempted pairs, **valid pairs**, successful pairs;
- acceptance-pass rate on valid trials;
- paired task success delta;
- provider input, output, total, cached input tokens where exposed;
- RCIR compiled context tokens and actual prompt context tokens;
- model turns, tool calls, repository reads, latency;
- P@K, recall, MRR, nDCG on independently adjudicated retrieval ground truth;
- mean and median, spread/CI when sample supports it.

The token-saving formula for each valid pair is `(baseline_input_tokens - rcir_input_tokens)/baseline_input_tokens * 100`. Also compute total-token delta. Report median of valid-pair deltas **with an actual statistical median implementation**, not “middle item at index N//2” for even N. Show paired-successful comparisons separately; if none, result is `NO_SUCCESSFUL_PAIRS`, not a token-saving claim about completed tasks. Never convert tokens directly into IDE credits without official usage evidence. For local Ollama, actual API charge is $0; optional hosted-price scenarios are hypothetical, labeled and sourced/versioned.

### 2.6 Host runtime and honest regression checks

Split verifiers into:

```text
L1_SYNTAX         = actual parser/compiler/linter execution
L2_BEHAVIOR       = task-specific behavior assertions
L3_REGRESSION     = targeted/affected upstream test suite
```

If L3 is just `php -l`, it is **L1**, never L3. Missing PHP/composer/Nextcloud test environment → `NOT_MEASURED` or `SETUP_ERROR`, not PASS. For interface changes, check concrete implementers and contract compatibility. Record exact commands, exit status, counts, durations, and logs. Ensure all verifiers operate on the trial's worktree, not the original repository.

### 2.7 Formal stage status and immutable evidence

A stage exiting 0 means only **executed**, not passed its semantic gate. Missing `*_result.json` is failure/NOT_MEASURED. Do not default to PASS. Separate `execution_status`, `measurement_status`, `gate_status`, `blocking`, `failures`. Validate full manifest/source hashes before setting `VALIDATED`. Regenerate `FINAL_SYSTEM_ASSESSMENT.md` from raw current evidence, rather than editing prose manually. Keep unresolved or failed gates explicit. Generate a `claims.json` registry whose values are computed from source artifacts, never duplicated hardcoded numbers.

### 2.8 Improve quality rather than grades

Once harness validity is sound, work on real defects causing weak performance: RCIR context inclusion; poor ranker candidates; excessive expansion around config/interface hubs; false type/route/event edges; oversized context; cache/latency; agent tool schemas; provider timeout handling; insufficient agent capability/turn budget. Tune DEV and VALIDATION only. Freeze ranker and prompt configuration before independent TEST. A larger, genuinely capable model may be run as a separate paired experiment, but do not replace failing tiny-model results. Every model must have its own clearly named result.

**P0 acceptance:** an independent fresh run creates auditable raw evidence, genuinely uses RCIR in only the RCIR arm, classifies provider timeouts correctly, and can be recreated from a clean checkout. No current or historical results are silently reused.

---

## 3. P1: backend proof server, then minimal frontend

Build a **real local backend**, recommended `FastAPI` + Pydantic, packaged with the project. It must call the actual PolyFlow/RCIR services for live operations and load validated frozen run artifacts for completed benchmarks. Do not generate synthetic data in API handlers. The frontend is display and control logic only.

Suggested structure (adapt to existing packaging if possible):

```text
showcase_app/
  backend/
    app.py
    schemas.py
    services/
      evidence_registry.py
      benchmark_service.py
      feature_service.py
      interpreter_service.py
      rcir_service.py
      erpnext_service.py
    api/
      health.py
      features.py
      interpreter.py
      rcir.py
      proofs.py
      erpnext.py
  frontend/
    index.html
    css/{base,layout,components,responsive}.css
    js/{app,polyflow,interpreter,rcir,proofs,erpnext}.js
  README.md
```

Plain **HTML/CSS/JavaScript is explicitly preferred** for this rebuild because the current React UI is cluttered. You may retain React only if it is concretely simpler and passes the same visual/accessibility acceptance. Do not build two competing UIs. Retire or archive the old React presentation and remove it from the supported demo command if the new interface replaces it.

### Backend routes

```text
GET  /api/health
GET  /api/runs
GET  /api/runs/{run_id}/status
GET  /api/features
GET  /api/features/{feature_id}
GET  /api/features/{feature_id}/native-vs-poly
POST /api/interpreter/runs                  # starts a real normal or controlled failure run
GET  /api/interpreter/runs/{run_id}
GET  /api/interpreter/runs/{run_id}/events  # Server-Sent Events
POST /api/rcir/queries                     # real RCIR query, allow-listed repo
GET  /api/rcir/queries/{query_id}
GET  /api/rcir/queries/{query_id}/events   # SSE, if useful
GET  /api/benchmarks/{run_id}/summary
GET  /api/benchmarks/{run_id}/pairs.csv
GET  /api/benchmarks/{run_id}/ranked-files.csv
GET  /api/proofs
GET  /api/proofs/{proof_id}                 # opens verified file with correct MIME
GET  /api/proofs/{proof_id}/download
GET  /api/erpnext/tree
GET  /api/erpnext/features/{feature_id}
GET  /api/erpnext/coverage.csv
```

Only `POST` actions initiate execution. A `GET` must never secretly run a benchmark, edit files, or modify a target repo. Use job IDs and streamed state events; avoid blocking web server threads. For quick presentation, load frozen measured benchmark data by default and offer a separate explicit `Run Live Query` button. It must be visually obvious when the result is `LIVE`, `FROZEN_MEASURED`, `HISTORICAL`, `DEMO_ONLY`, or `NOT_MEASURED`.

### Security and portability

- Bind localhost by default; require explicit user opt-in for external networking.
- No generic path parameter may read arbitrary filesystem locations. `proof_id` must resolve through a server-generated allow-listed proof registry; reject `../` and symlink escapes.
- No arbitrary shell command from the browser. Run specific allow-listed interpreter/RCIR operations in sandboxed isolated temp workspace with timeouts and resource limits.
- Controlled failure injection changes the demo fixture/run input only, never the original ERPNext checkout or recorded benchmark evidence.
- Pin/check source commits; hash files on serving; refuse mismatches instead of serving false proof.
- Support Windows and Linux file paths; normalize repo-relative paths. Do not leak local user home directories into proof JSON.
- Show clear error/NOT_MEASURED state if a toolchain/model/repository is unavailable. Never seed fallback values like file count 10080, latency 1.2ms or a default 80.5% reduction.

### Proof registry and exports

Create `proof_index.json` dynamically from successful raw run artifacts. Each proof record includes ID, title, run ID, source file, SHA-256, bytes/MIME, origin kind, measurement method, validity status, timestamp and safe URL. Every displayed numerical result must link to the source artifact, and a corresponding **CSV row set** where tabular. Clicking opens text/CSV/JSON/patch/log in a readable viewer or downloads it, not a dead decorative button.

Require derived CSVs:

```text
run_summary.csv
feature_closure.csv
source_mappings.csv
retrieved_files.csv
agent_trials.csv
paired_token_usage.csv
interpreter_events.csv
runtime_receipts.csv
coverage_ledger.csv
```

CSV creation must use parsed raw artifacts and real repository indexing, not editable hardcoded dictionaries. Emit SHA-256 manifest and source lineage for each exported file. Implement `verify_showcase` that independently recomputes all summary numbers and file hashes.

**P1 acceptance:** backend starts in a clean environment, endpoints respond with current data, paths cannot escape the artifact root, every meaningful on-screen number opens a verifiable proof file, and no numerical fallback fills missing data.

---

## 4. P2: replace the clutter with five minimal presentation tabs

**Design principle:** Let the presenter explain. The interface shows the flow and the proof, not an essay. No emojis, dense JSON, bloated research prose, giant animation effects, or too many metrics.

Use no more than five navigation items:

```text
1. PolyFlow      2. Interpreter      3. RCIR      4. Proofs      5. ERPNext
```

Global UI: small header (PolyFlow, active repository, run state); clean typography; neutral background; one accent; subtle thin connectors; data panels with ample space; data state next to every measured number; small `View proof` affordance. Avoid jargon in visible labels unless vital. Keep technical details behind a click-to-expand drawer. Animations should respect reduced-motion settings.

### Tab 01: PolyFlow — native vs feature view

This must be the opening screen and highest-quality visual. Same **real feature in ERPNext**, selected from actual pinned clone, e.g. Sales Invoice:

```text
┌──────────────────────────────┬──────────────────────────────┐
│ ORIGINAL ERPNext             │ POLYFLOW                     │
│                              │                              │
│ Frontend / Client            │ sales_invoice.poly           │
│ Backend / Python             │ ├ Contract                   │
│ Data model / DocType         │ ├ Frontend links             │
│ Hooks / configuration        │ ├ Backend links              │
│ Tests                        │ ├ Schema / persistence       │
│ Dependencies                 │ ├ Events / tests             │
│                              │ └ Feature dependencies       │
│ [Browse native files]        │ [Open actual .poly]          │
└──────────────────────────────┴──────────────────────────────┘
          Native files N  →  1 feature entry point
```

Data come from the **same actual FeatureClosure** object and generated `.poly`. Clicking one node highlights corresponding file(s) on the other side; clicking a path opens source/proof. Show only real measured `native artifacts`, `directories`, `languages`, `feature modules`, `unresolved`. Detect true tech stack (Frappe uses Python, JS, DocType metadata etc.); do not add React where it is not present. Make meaningful distinction between `.poly` source reference and actual transformed executable code. The native files do not disappear just because `.poly` links them.

### Tab 02: Interpreter — real-time animated workflow, two modes

There should be **two clear controls**: `Run Normal Flow` and `Run Failure Flow`. Keep animation as simple lines and moving packets on an SVG or lightweight DOM diagram. Every packet movement is driven by actual backend SSE events, not a predetermined timer sequence that continues even when runtime fails.

```text
                      [ .poly ]
                         ↓
                      [ Parse ]
                         ↓
                    [ Validate ]
                         ↓
                    [ Scheduler ]
                   ↙      ↓       ↘
            [Python]   [JS]    [Python]
                   ↘      ↓       ↙
                  [ Merge / Fallback ]
                         ↓
                     [ Receipt ]
```

- In normal mode, invoke real parser, contract validation, cell scheduler, actual host language runtimes and merge. Display minimal status/latency/cell count and a receipt proof link.
- In failure mode, **actually inject a controlled failure** into one noncritical cell in a sandbox; show that cell failing, the real declared fallback running, the unaffected cells completing, and the true final result `DEGRADED` or `FAILED`. Do not assert success unless runtime receipts prove it.
- If the core business operation is not safe without that cell, show `FAILED`, not magically “recovered”.
- Under the diagram offer only two expandable views: `Run details` and `Proof` (raw JSON events, logs, receipt, source). No giant inline trace wall.
- Keep synthetic/fake accounting and external dispatch out of demo: use a safe local fixture or a real test ERPNext environment. Label it `LOCAL EXECUTION FIXTURE` if not production ERPNext.

### Tab 03: RCIR — structure and token comparison

Use two subtabs: `How it works` and `Tokens`.

`How it works` is one animated row:

```text
Repository → Index → Graph → Retrieve → Rank → Pack → Agent
```

A single selected task produces a live context trace. Only show repository file count, files selected, context tokens and top five selected files. Selecting a file reveals **why** via source evidence. Do not show huge graph dumps, long descriptions or preset rankings as if live.

`Tokens` is a side-by-side measured comparison of same task/model/start state:

```text
Without RCIR                     With RCIR
[input tokens]                   [input tokens]
[total tokens]                   [total tokens]
[task status]                    [task status]

              Measured delta: ...
       [Open paired CSV] [Open raw run]
```

Show `Success`/`Failure` for both arms to prevent apparent token reduction from being caused by early failure or timeout. If no valid paired successes exist, clearly show `No successful paired trial evidence`. IDE credits stay `NOT_MEASURED` absent official metering. Never promise “80–90%” before measuring it.

### Tab 04: Proofs — not another agent-themed dashboard

A compact, neutral evidence library only:

```text
Benchmark run / time / source commit
Valid pairs / successful tasks / evidence state

[Open token usage CSV]
[Open agent trials CSV]
[Open actual code diff]
[Open acceptance + regression logs]
[Open retrieval trace]
[Open interpreter receipt]
[Open integrity manifest]
```

Failures and missing evidence must be shown neutrally and plainly. A `Download CSV` click must produce a real CSV, not a JSON blob disguised as a link.

### Tab 05: ERPNext — actual scale and transformation tree

Show a concise measured scale header and collapsible feature/module tree, not a huge preset graph. On click, display its actual generated `.poly`, mapped sources and tests, evidence links and validity status. Show three distinct measures:

```text
Structural mapping
Executable converted features
Behaviorally verified features
```

Do not conflate 100% ledger accounting with equivalent functional execution. Preset hard-coded recall/MRR tasks should not be primary content; live query results must be generated by actual RCIR backend and their proof is clickable. Large-scale layout should virtualize trees/tables where necessary.

### Responsive/UX acceptance

Test at 1920×1080, 1440×900, 1366×768, ~1024 wide tablet and ~390 wide phone; zoom 100%, 125%, 200%. Desktop comparison stays two columns; narrower widths stack without horizontal text clipping. Diagram scales via SVG `viewBox` and preserves readable text; mobile pan/zoom only for diagrams where unavoidable. Keyboard navigation, ARIA labels, focus outlines, screen reader status for event results, and prefers-reduced-motion. Long filenames truncate with click-to-open full path, never overlap neighboring cards. No slide-deck-sized paragraphs in the default view.

**P2 acceptance:** all five tabs are usable without presenter narration; live interpreter events really drive flow; RCIR data are measured rather than declared; every file/number opens a valid proof; no overflow on tested sizes.

---

## 5. P3: ERPNext conversion with verifiable parity boundaries

Perform only after P0–P2 are proven. Treat this as a separate **functional scope**, not permission to show fake equivalence.

- Pin full `frappe/frappe` + `frappe/erpnext` checkout commits; record installation/toolchain/database requirements and exact source inventory.
- Generate one PolyFlow project of many `.poly` feature modules, not one gigantic monolithic file.
- Per feature, discover native frontend, backend, DocType schemas/child tables, persistence relationships, APIs, hooks, tests, permissions, templates and linked features. Use actual AST/framework metadata where possible. Each source reference must exist, hash-match, have portable repo-relative path and verifiable edge/source span. No placeholder SHA, repeated absolute path, invented symbol or arbitrary 0.85/0.9 coverage default.
- The generated `.poly` AST must parse through the canonical real parser; all schema fields must derive from actual DocType JSON instead of fixed `name/docstatus` templates alone. Keep source-reference links distinct from executable code.
- Create independently adjudicated per-feature recall/precision/coverage on held-out features; report unknowns and precision rather than forcing 100% from known expected paths.
- Generate complete repository **structural/source-reference mapping** if feasible, supported by `coverage_ledger.csv`, feature mapping files and a reproducible converter. This may cover all accounted artifacts without implying executable parity.
- For actual behavior, pick a controlled set of business verticals and execute them against real supported Frappe/ERPNext test environments, with MariaDB/Redis/background jobs as applicable. Compare inputs/outputs/errors/side-effects against native ERPNext, run relevant upstream tests, and record divergences. Do not replace real DB writes or webhook delivery with a text receipt claiming COMMITTED/DELIVERED.
- If full-system behavioral parity is not reached, report exact coverage denominator, number of executable converted features, pass rate and gaps. Do not claim a “completely working ERPNext in PolyFlow” unless every in-scope functionality is proven under the stated environment.

**P3 acceptance:** the full mapping can be regenerated from pinned sources; selected executable verticals have actual behavioral test evidence; the presentation separates **mapped**, **executable**, and **verified parity**.

---

## 6. Required test and anti-fabrication suite

Add explicit tests that fail on the defects previously seen:

1. RCIR arm actually calls retrieval/index/context provider and returns nonempty evidence-backed context; baseline arm does not.
2. Changing RCIR output affects the RCIR agent input; it does not affect baseline.
3. Trial with provider timeout cannot become a valid pair even if partial tokens are present.
4. `blind_after_fix` cannot be generated from `baseline_data['trials']`; separate run/provenance required.
5. Blind-guard policy is actually exercised, with a failed attempt to access a denied artifact from the evaluation process.
6. Frozen benchmark/test-design SHA must equal the current file hash and all report references.
7. Missing stage result is not PASS; L1-only result is not L3 regression PASS.
8. No unchanged target produces successful agent approval; concrete interface implementation regressions fail validation.
9. Showcase evidence loader rejects missing/tampered proof and path traversal.
10. Showcase generators contain no fixed metric dictionaries or synthetic interpreter success/failure traces. A simulated/controlled test must be clearly classified and still execute the real runtime.
11. Every UI metric recomputes from underlying evidence; changing a raw fixture changes derived output or invalidates it.
12. Feature Closure outputs source-relative paths and real content hashes; detects duplicate links, missing files and false-positive hook associations.
13. Generated `.poly` parses and native-vs-PolyFlow feature mapping matches real source.
14. Interpreter SSE event order corresponds to real executed cell state; a failed cell is not shown as success.
15. UI viewport tests/screenshot visual inspection at listed sizes; no page-wide overflow, clipped tab, unreadable packed graph or dead proof link.
16. SDK wheel/CLI runs outside monorepo without `PYTHONPATH` hacks; if still blocked, surface NOT_VERIFIED.
17. CI includes static/unit/integration tests and frontend build. Live-provider/ERPNext full benchmark may be manually triggered, but must have a reproducible command and evidence capture.

Do not write tests that explicitly assert current measured numbers such as “five valid pairs”, “100%”, “842”, or “median +1.68%”. Instead assert **mathematical consistency**, provenance and expected software behavior.

---

## 7. Exact deliverable set

Produce or update in repo:

```text
AUDIT_FINDINGS.md
FINAL_SYSTEM_ASSESSMENT.md                      # generated honestly from newest valid run
experiments/runs/<unique_run_id>/
  manifest.json
  raw/
  results/
  logs/
  reports/
  exports/
    agent_trials.csv
    paired_token_usage.csv
    retrieved_files.csv
    feature_closure.csv
    coverage_ledger.csv
  proof_index.json
showcase_app/backend/...
showcase_app/frontend/...
showcase_app/README.md
showcase/verify_showcase.py                     # or equivalent verifier
scripts/run_final_benchmark.*                  # OS-supported reproducible entrypoint
scripts/run_showcase.*                        # launches backend + minimal UI
```

Keep real proof artifacts as run-scoped files, never silently overwrite history. Include a `SHOWCASE_REPRODUCTION.md` with exact setup, pinned commits, model/provider config, benchmark command, server command, open URL, and expected statuses in the absence of optional dependencies. Provide a feature-demo `.poly` that uses a real local fixture and a clear origin label. No package has to contain the user's private absolute Windows paths.

### Final user-facing acceptance report

End your implementation response with a factual table:

```text
Workstream              Status                Evidence
Blind harness           PASS/FAIL/NOT_MEASURED  <actual file>
True RCIR A/B           ...                     <actual file>
Task completion         ...                     <actual file>
Live token savings      ...                     <actual file>
Interpreter normal      ...                     <actual receipt>
Interpreter failover    ...                     <actual receipt>
Proof links             ...                     <test result>
Minimal UI              ...                     <build/screenshot>
ERPNext mapping         ...                     <coverage CSV>
ERPNext executable      ...                     <test report>
Full ERPNext parity     ...                     <test report or NOT_VERIFIED>
```

If benchmark numbers are weak, fix real defects and rerun a new DEV/VALIDATION benchmark, then only release TEST after freeze. If numbers remain weak, retain the honest results and document the engineering bottleneck. Do not rebrand failure as success.

**Completion means: real backend, real interpreter flow, actual RCIR context retrieval, valid A/B evidence, openable proof CSV/JSON/source files, a minimalist responsive UI, and clear measured ERPNext mapping/parity status. It does not mean the final report merely says “all tasks completed”.**

---

## 8. Final demo script (for a human presenter, not a fake simulation)

1. Open **PolyFlow**: native ERPNext Sales Invoice scattered across layers on left; one generated `sales_invoice.poly` entry point and source links on right. Click a file and open its real source proof.
2. Open **Interpreter**: click `Run Normal Flow`. Watch actual packet events travel through parser, validation, language cells, merge, receipt. Open the receipt. Click `Run Failure Flow`; see one actual controlled cell failure, fallback action and honest degraded/failed outcome.
3. Open **RCIR**: show the simple pipeline and a real retrieval query. Switch to `Tokens`, compare a valid paired task, and open source token CSV. If no successful paired tasks, say so and display separate available context/retrieval metrics.
4. Open **Proofs**: show actual run manifests, task results, tests, diffs and downloadable files.
5. Open **ERPNext**: expand the measured feature tree, select a real `.poly`, and show separately structural mapping and proven executable parity.

The presenter should do the explaining. The software should show **only enough text to establish what is happening and how to verify it**.
