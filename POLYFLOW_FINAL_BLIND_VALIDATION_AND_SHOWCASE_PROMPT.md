# PolyFlow Final Blind Validation, Rectification & Showcase UI Implementation Prompt

**Repository:** `paril-01/PolyFlow`  
**Reviewed HEAD:** `d5be98cafaf652e9d6242906b6dc3d054933fccb`  
**Purpose:** Perform one final evidence-first validation of PolyFlow/RCIR, repair every remaining correctness/evidence issue, regenerate the benchmark honestly, and only then build the final presentation interface.

This is ONE integrated implementation assignment. Do not split it into separate ticket prompts.

---

# 0. Non-Negotiable Rule: Blind Validation Comes First

The first step is NOT to read the conclusions in:

```text
FINAL_SYSTEM_ASSESSMENT.md
showcase/
experiments/**/reports/
experiments/**/results/ that contain previous benchmark conclusions
rcir/visualizer-react/src/data/benchmarkData.js
historical enhancement/report markdown files
```

The validation agent must not use those artifacts to decide what should pass, what numbers should be obtained, which files are expected, which dependencies should be returned, or which benchmark tasks should succeed.

Those files may be opened ONLY AFTER the independent blind result is frozen.

## 0.1 Create a blind-validation workspace

Create:

```text
experiments/final_blind_validation/
  README.md
  manifest.json
  source_inventory.json
  test_design.json
  raw/
  results/
  reports/
  logs/
```

Run from a fresh clean checkout/worktree. Record exact PolyFlow, Nextcloud, Frappe and ERPNext commits, toolchain versions, OS, provider/model, and timestamp. Hash the benchmark source/configuration.

## 0.2 Explicit deny-list

The blind evaluator must fail if benchmark/test generation reads any of:

```text
FINAL_SYSTEM_ASSESSMENT.md
showcase/**
rcir/visualizer-react/src/data/benchmarkData.js
previous final benchmark reports
previous token summaries
previous gate summaries
```

Implement an access guard or run from a sanitized checkout where those paths are absent.

## 0.3 Freeze blind test design before execution

Create tasks from independent evidence, preferably upstream historical changes/diffs and real source behavior. Store hidden expected dependencies, acceptance evaluator and regression evaluator. Hash `test_design.json` before running baseline/RCIR trials.

The coding agent must NOT receive expected files, ground-truth dependencies, gold patches, report conclusions, or expected RCIR output.

---

# 1. Findings From the Current HEAD That Must Be Rectified

## F01 — Current agent benchmark is actually 0% successful

The committed `showcase/03_token_ab/paired_trials.json` currently reports both RCIR and baseline completion rates at 0.0. Individual trials are invalid with:

```text
error = "name 'os' is not defined"
```

`orchestrator/agent_loop.py` uses `os.environ.get(...)` but does not import `os`.

### Fix

Add the missing import and a unit test that executes a minimal real `ReActAgentRunner.run()` far enough to create a `UsageRecord`. Rerun all agent trials from empty trial directories. Do not restamp/reuse failed trials.

---

## F02 — Formal benchmark stage PASS is not semantic gate PASS

`run_formal_benchmark.py` marks a stage `PASSED` when the subprocess exits 0. `run_agent_validation.py` can exit 0 even when every trial fails.

### Fix

Every stage must emit a machine-readable stage result:

```json
{
  "stage": "agent_validation",
  "execution_status": "COMPLETED",
  "measurement_status": "MEASURED",
  "gate_status": "PASS|FAIL|NOT_REQUIRED|NOT_MEASURED",
  "blocking": true,
  "failures": []
}
```

The master runner must validate that semantic result. `process exit 0 + gate FAIL` is not `PASSED`.

---

## F03 — `FINAL_SYSTEM_ASSESSMENT.md` contradicts raw artifacts

The report claims 20 paired live trials, 20/20 non-empty patches, 5/5 tasks passed, agent validation passed and all gates passed. The committed paired-trial artifact says 0 successful RCIR trials and 0 successful baseline trials. The current gate artifact contains `agent_gate.passed = false`, while Option B can still pass because Option B does not require the agent gate.

### Fix

Generate every report statement from current validated artifacts. No literal benchmark verdicts/numbers in report code. Architecture Decision and Agent Gate must be separate facts.

---

## F04 — Current showcase builder fabricates agent evidence

`scripts/build_showcase.py` writes `tool_calls.jsonl`, `diff.patch`, acceptance logs, regression logs and gatekeeper results using hardcoded strings instead of copying raw verified evidence.

### Fix

The showcase builder may only copy or truth-preservingly summarize validated raw artifacts. Every exported evidence file needs lineage fields: source run, source artifact, source hash, showcase hash, transformation. Missing evidence must become `NOT_AVAILABLE`, never synthesized.

---

## F05 — Showcase provider usage is empty

`showcase/04_agent/successful_trial/provider_usage.json` is currently `{}`.

### Fix

A showcase trial is eligible only if it has real provider/model identity, non-empty usage records, input/output/total tokens, measurement source, and latency.

---

## F06 — “20 paired trials” terminology is wrong

`5 tasks × 2 conditions × 2 budgets × 1 replicate = 20 individual executions`, which is 10 baseline-vs-RCIR pairs, not 20 pairs.

### Fix

Report `individual_trials`, `paired_comparisons`, `valid_pairs`, and `successful_pairs` separately.

---

## F07 — Live token reduction is currently unproven

The current paired artifact reports live-model reduction = 0%. ERPNext displayed live telemetry also has higher RCIR prompt counts than baseline on all four shown examples (209 vs 71, 217 vs 79, 214 vs 75, 191 vs 78).

### Fix

Run a proper blind paired coding benchmark. Same task, commit, model/provider, settings, tools, turns, acceptance and regression tests. Only context strategy differs. Measure provider input/output/total tokens, context tokens, tool-result tokens, turns, latency, and task success. Primary metric: median input-token delta on successful valid pairs. Do not target a predetermined percentage.

---

## F08 — IDE credit saving is NOT measured

Keep `IDE Credits = NOT_MEASURED` unless a documented export/API/log provides actual values. If estimating cost from tokens, label it `Hypothetical API Cost Equivalent`, not IDE credits.

---

## F09 — Cost comparison uses an unrelated reference price

The current experiment uses local Ollama/Qwen but a GPT-4o-mini reference price.

### Fix

For local Ollama, actual provider API cost is $0 and hardware/electricity cost is `NOT_MEASURED`. Keep any cloud cost as a separate optional reference scenario.

---

## F10 — Regression verification is only syntax checking

`verify_regression.py` mainly executes `php -l` on modified files. The report describes this as a full Nextcloud unit/regression suite.

### Fix

Create verification levels:

```text
L1_SYNTAX
L2_TARGETED_TEST
L3_RELEVANT_REGRESSION
```

Presentation-grade agent tasks require at least L1+L2 and should require L3 where feasible. Record exact commands/test counts. Never call syntax linting a full regression suite.

---

## F11 — Interface tasks can pass regex acceptance while breaking implementations

Tasks adding methods to `IShare`, `IConfig`, `IUserSession` mostly regex-check the interface declaration. A valid interface file can still break concrete implementers.

### Fix

Discover affected implementers, require compatible changes, load/compile them, and run targeted tests. Acceptance must be behavioral/structural, not just regex presence.

---

## F12 — Final benchmark tasks need independent origin

For the realistic final test, use hidden historical-diff tasks. Recommended flow: select real upstream change, checkout parent commit, turn intent into task prompt, hide actual diff as evaluator oracle, run baseline/RCIR from same parent, score changed-file recall, patch correctness, tests, and tokens. Repeat for a small Frappe/ERPNext set if feasible.

---

## F13 — Default tracked results remain provenance-confusing

Use:

```text
experiments/rcir_v8_5/results/ = development only
experiments/rcir_runs/<run_id>/ = immutable formal evidence
```

Add `STATUS.md` to development results. Presentation UI may read only a selected validated formal run.

---

## F14 — `OPTION_B_ACCEPTED` does not mean every subsystem passed

UI/report must show Architecture Decision and Agent Gate separately. Never translate Option B into “all gates passed”.

---

## F15 — ERPNext DocType counts are inconsistent

Current artifacts show 840 DocTypes in inventory but 842 generated features/report references.

### Fix

Define and recompute `doctype_schema_count`, `generated_poly_feature_count`, and `non_doctype_feature_count` from the pinned repositories.

---

## F16 — 100% semantic coverage is accounting, not execution parity

Expose distinct metrics:

```text
artifact_accounting_coverage
semantic_mapping_coverage
executable_vertical_coverage
behavioral_parity_coverage
unresolved_count
```

Do not call artifact accounting “100% functionality converted”.

---

## F17 — ERPNext benchmark is retrieval/inference, not autonomous patch proof

Keep current ERPNext evidence under `RETRIEVAL / CONTEXT GENERALIZATION`. Add a separate ERPNext coding-agent benchmark if time permits. Do not mix them.

---

## F18 — `baseline_a_tokens = 0` means not measured

Use typed statuses `MEASURED`, `NOT_MEASURED`, `INFEASIBLE`. Never encode missing measurements as numeric zero.

---

## F19 — 55.1x context compression uses an arbitrary 32k window

Rename it `bounded_context_window_compression`. Keep it separate from actual provider-token reduction.

---

## F20 — ERPNext source token footprint is estimated

Either calculate using a specified tokenizer/version or label it `ESTIMATED_SOURCE_TOKENS` and record method.

---

## F21 — Current React visualizer contains stale hardcoded benchmark truth

`rcir/visualizer-react/src/data/benchmarkData.js` contains old values including historical 80.5% token reduction and old recall/agent outcomes.

### Fix

Delete current benchmark truth from JS constants. Components may contain labels/layout only. Load current evidence from generated `showcase/data/*.json`.

---

## F22 — Current Polyglot Studio has hardcoded successful runtime output

Values like `ALL RUNTIMES EXIT 0`, `214 ms`, `0 Drift`, `6/6 PASS`, `Zero Mocks` are literal UI data.

### Fix

Use a real demo backend endpoint or frozen validated execution artifact. Every result must carry `LIVE`, `FROZEN_MEASURED`, or `NOT_MEASURED`.

---

## F23 — `polyflow demo` fake live RCIR query

The current “live query” largely imports an RCIR class and prints a hardcoded 1.2ms.

### Fix

Actually load graph/index, parse intent, resolve target, retrieve candidates, rank, compile context, measure wall time, and return evidence.

---

## F24 — Demo uses fallback benchmark numbers

Remove numeric defaults such as `repo.get("total_files", 10080)`. Missing required data must render `NOT AVAILABLE`.

---

## F25 — Demo final verdict is hardcoded

Compute final status from evidence. Possible states: `VALIDATED`, `PARTIAL`, `FAILED`, `INVALID_EVIDENCE`.

---

## F26 — Showcase quick demo uses `PYTHONPATH`

The formal presentation path must use the installed wheel/portable launcher. Keep any PYTHONPATH launcher as development-only.

---

## F27 — `@source` sample uses the empty-file SHA-256

The current sample contains `e3b0c442...b855` and no demonstrated real source fixture.

### Fix

Reference a real pinned source or real fixture and compute actual hash at build time. Interpreter UI must show source exists/hash matches/symbol span matches.

---

## F28 — Interpreter error artifact is manually authored

Run the actual parser/linter on a broken `.poly`, capture the real diagnostic object, serialize it, and display raw + human-readable form.

---

## F29 — Latest commit has no exposed CI status/workflow evidence

Add CI for core tests, blind-harness tests, SDK black-box install, React build, showcase evidence validation, and claim consistency. Keep expensive live-model benchmark manual if required.

---

# 2. Blind Baseline Run Before Further Optimization

After implementing only what is needed to make the blind harness executable, run the current system as-is and produce:

```text
experiments/final_blind_validation/reports/BLIND_BASELINE_REPORT.md
experiments/final_blind_validation/results/blind_baseline.json
```

Answer: what works, fails, is unmeasured/invalid, actual retrieval quality, task success, provider tokens, context compression, latency, and SDK portability. Freeze/hash this before performance fixes.

---

# 3. Rectification Sequence

```text
1. Fix AgentLoop telemetry crash
2. Fix stage semantic PASS/FAIL
3. Strengthen acceptance + real regression tests
4. Remove fabricated showcase evidence
5. Make reports data-derived and consistent
6. Run valid paired token A/B experiment
7. Optimize RCIR retrieval/index if needed
8. Reconcile ERPNext metrics
9. Make SDK/demo fail closed
10. Build final UI
```

Then rerun the SAME frozen blind benchmark design and produce `BLIND_AFTER_FIX_REPORT.md`, `blind_after_fix.json`, and `blind_delta.json`.

---

# 4. Final Benchmark Requirements

Minimum agent benchmark: 5 independent tasks, baseline + RCIR, same model/tools/start commit/turn budget, >=3 replicates preferred. Use one primary turn budget for headline comparison.

Token report must include valid/successful pair counts, input/total token distributions, context tokens, success rates, turns and latency. No token-reduction claim if `valid_pairs == 0`.

Every successful trial must retain acceptance-before, real diff, syntax, targeted tests, relevant regression, gatekeeper, provider usage, tool trace and RCIR context trace.

---

# 5. Final Presentation UI

Reuse `rcir/visualizer-react/` (React/Vite). Do not create a second app unless technically impossible. Simplify the current visualizer substantially.

No emojis. Minimal professional icons only. Support 1920x1080, 1440x900 and 1366x768.

Use exactly five primary tabs:

```text
01 PolyFlow
02 Interpreter
03 RCIR
04 Agent & Validation
05 ERPNext Scale
```

Keep a small evidence/status control in the header instead of a sixth tab.

---

# 6. Tab 01 — PolyFlow

Question: “What is PolyFlow and what changed versus a traditional repository?”

Layout: original repo tree on left, transformation in center, `.poly` feature-centric representation on right. Use a real source example. Clicking a source file highlights its mapped `.poly` feature, source-reference provenance, related schema/cells/tests, and actual hash.

Bottom drawer shows real `.poly` syntax (`@contract`, `@schema`, `@source`, language cells, `@link`, `@error-map`, `@decision`). Top counts: native artifacts, mapped features, source refs, schemas, tests, unresolved.

---

# 7. Tab 02 — Interpreter

Question: “What happens when a `.poly` file executes?”

One-click `Run Workflow` animation:

```text
.poly Source
→ Parser / AST
→ Contract + Schema Validation
→ Cell Scheduler
→ Language Runtimes
→ Merge / Fallback Policy
→ Execution Receipt
```

Use restrained packet movement only while running.

The backend must execute the actual SDK and return parse/validation/per-cell runtime/toolchain/latency/merge/final status.

Add `Normal Run` and `Inject One Cell Failure` modes. Failure demo must show real fail-partial/fallback behavior, e.g. one runtime fails while others continue and final status becomes DEGRADED/RECOVERED where policy allows.

Three compact capability cards:

1. Human Error Translation: raw exception → PF_* code → plain explanation → fix → source line.
2. Contract & Schema Guard: invalid payload blocked before unsafe execution.
3. Source Traceability: `.poly` cell → native source → hash → span.

Error panel has only `Readable` and `Raw JSON` subtabs and reads `.polyflow/logs/errors.jsonl`.

---

# 8. Tab 03 — RCIR

Question: “How does RCIR reduce repository context for an AI agent?”

Two internal subtabs: `Structure` and `Token Usage`.

## Structure

Horizontal flow:

```text
Repository
→ Parsers + Adapters
→ Canonical Graph
→ Change Intent
→ Candidate Channels
→ Evidence Fusion / Ranker
→ Context Compiler
→ Agent
```

Animate one task packet. Show only 1–2 metrics per stage. Clicking a ranked file reveals why selected, edge/evidence, source/span, confidence.

## Token Usage

Side-by-side synchronized lanes:

```text
WITHOUT RCIR              WITH RCIR
same task                  same task
same model                 same model
same tools                 same tools
repository workflow        RCIR evidence workflow
→ context                  → context
→ LLM                      → LLM
→ patch/test               → patch/test
```

Counters: input/output/total tokens, context tokens, turns, latency, task result. Center delta only if both measurements valid. Otherwise show `NOT MEASURED`.

Credits box has `MEASURED` or `NOT MEASURED`; never fake IDE credits. Optional separate `Reference API Cost Scenario` with explicit reference model/pricing.

---

# 9. Tab 04 — Agent & Validation

Question: “Does the system actually make and verify code changes?”

Timeline:

```text
Task → Inspect → RCIR Context → Patch → Syntax → Targeted Tests → Regression → Gatekeeper
```

Selected real trial shows task, model, turns, tools, files modified, diff, acceptance before/after, exact regression command/result, token usage, gatekeeper.

Add a Blind Test header:

```text
Benchmark Mode: BLIND
Prior report access: BLOCKED
Hidden evaluator: ENABLED
```

Show before-fix vs after-fix and baseline vs RCIR results.

---

# 10. Tab 05 — ERPNext Scale

Question: “Does this work on a large, complicated enterprise system?”

Header: Frappe + ERPNext exact commits. Show measured total artifacts/source files/LOC/language counts/DocType schemas/tests.

Use a module grid, not a giant hairball graph. Clicking a module shows native files, PolyFlow features, DocTypes, tests and source references.

Show coverage distinctly:

```text
Artifact accounting
Semantic mapping
Executable verticals
Behavioral parity
Unresolved
```

Preset RCIR tasks: local, cross-file, cross-module, architectural. Show expected/retrieved critical sources, recall, MRR, context tokens, query latency. Only show an agent patch panel if such an experiment exists.

---

# 11. Header & Evidence States

Header shows `PolyFlow`, current evidence run ID, evidence state, repository selector.

Evidence states:

```text
VALIDATED
PARTIAL
INVALID
DEVELOPMENT
```

Hash integrity proves file integrity, not factual correctness. Do not use `VERIFIED` solely because hashes match.

---

# 12. UI Data Architecture

Create:

```text
showcase/data/
  run_manifest.json
  system_status.json
  polyflow_mapping.json
  interpreter_demo.json
  rcir_pipeline.json
  token_ab.json
  agent_trials.json
  erpnext_scale.json
  claim_registry.json
```

Generate with `scripts/build_showcase_data.py`. React reads these files; no benchmark truth in JS constants.

Each displayed claim must have source lineage:

```json
{
  "id": "rcir.token.input_reduction",
  "value": 0,
  "unit": "%",
  "status": "MEASURED|NOT_MEASURED|HISTORICAL",
  "source_artifact": "...",
  "source_json_path": "...",
  "source_sha256": "...",
  "run_id": "..."
}
```

---

# 13. Showcase Builder Must Fail Closed

Rewrite `scripts/build_showcase.py` with no handwritten evidence, hardcoded benchmark percentages/PASS values, numeric defaults, synthetic diffs or synthetic logs.

It must validate run, artifact hashes, semantic gates, export evidence, build claim registry, and fail if a required claim lacks evidence.

---

# 14. Final Report Consistency Test

Create `tests/test_final_claim_consistency.py` comparing final report, showcase data, formal gates, agent A/B and ERPNext artifacts.

It must fail if report says 5/5 but artifact says 0/5; agent gate false renders “all gates passed”; NOT_MEASURED becomes 0; DocType counts disagree; pair counts disagree; token delta differs from recomputation.

---

# 15. Visual Design Rules

Dark neutral background, light typography, one restrained accent; green only valid pass, red failure, amber partial/not measured. No emojis. Avoid excessive gradients/glow/giant cards/badges. Prefer thin connectors, small moving packets, monospace values, clear captions and whitespace. 200–600ms transitions. No constant decorative motion. Render only task-relevant subgraphs.

---

# 16. UI Tests

Add tests for build, all five tabs, no hardcoded benchmark values, invalid evidence → INVALID, missing evidence → NOT MEASURED, token delta equals JSON, agent panel rejects missing/synthetic diff, interpreter failure uses runtime response, live RCIR query calls real pipeline, ERPNext counts data-driven.

Add a static test banning current hardcoded presentation claims such as:

```text
80.5%
96.7%
ALL RUNTIMES EXIT 0
ALL 11 VERIFICATION GATES PASSED
214 ms
```

unless explicitly inside HISTORICAL fixtures.

---

# 17. Required Final Output

Produce:

```text
FINAL_BLIND_VALIDATION_REPORT.md
FINAL_SYSTEM_ASSESSMENT.md
showcase/
rcir/visualizer-react/
```

Final report includes blind baseline, problems, fixes, after-fix blind results, baseline-vs-RCIR agent results, provider tokens, interpreter/runtime validation, SDK portability, Frappe/ERPNext validation, known limitations, evidence manifest.

---

# 18. Final Acceptance Criteria

Do not declare presentation-ready unless:

```text
blind design frozen before prior conclusions are readable
agent loop no longer crashes
valid agent trials > 0
agent evidence copied from raw runs only
report and artifacts agree
master benchmark distinguishes execution from gate success
real targeted/regression tests run
live token A/B is measured
UI token claims equal raw provider records
IDE credits remain NOT_MEASURED unless real data exists
ERPNext counts are internally consistent
showcase has no fabricated diffs/logs/verdicts
React has no hardcoded current benchmark numbers
all five tabs work
```

If RCIR does not reduce provider tokens, show that result honestly and emphasize the metrics it genuinely improves: dependency recall, context quality, task success, repository searches, turns, or latency. Do not force the token narrative.

---

# 19. Final Presentation Sequence

```text
1. PolyFlow
   Native repository → feature-centric .poly representation

2. Interpreter
   One click → parse → validate → execute → merge
   Inject one cell failure → show fail-partial/fallback
   Show error translation + source traceability

3. RCIR Structure
   Repository → graph → evidence channels → ranker → context compiler → agent

4. RCIR Token Usage
   Same task/model side by side
   Baseline vs RCIR actual provider telemetry

5. Agent & Blind Validation
   Real diff + tests + gatekeeper + before/after blind benchmark

6. ERPNext Scale
   Actual scale + semantic mapping + difficult RCIR query
```

The viewer should understand the system without the presenter having to explain what every panel means.

That is the final standard.
