# PolyFlow Final Implementation Master Prompt
## RCIR Benchmark Completion → Portable PolyFlow SDK → Real Token-Efficiency Proof → Frappe/ERPNext Extreme Validation

**Repository:** `paril-01/PolyFlow`  
**Reviewed HEAD:** `989249cfbaf003f329d53e93f4b299ad81aaebec`  
**Review date:** 2026-10-08  
**Purpose:** This is the single implementation specification for finishing the current PolyFlow/RCIR system and converting it into a presentation-ready, reproducible engineering proof. Do not split this document into separate implementation tickets or independent prompts. Work through it as one integrated program.

---

# 1. Final Objective

Finish PolyFlow as one coherent system that can demonstrate, with reproducible evidence, all of the following:

1. **PolyFlow language/runtime**
   - `.poly` files are parsed by a real custom interpreter.
   - Multi-language cells are executed by real host runtimes rather than presentation-only emulation.
   - Schemas, links, contracts, decisions, standards, errors, and source relationships are represented consistently.
   - Errors are translated into useful PolyFlow diagnostics and written to structured project-local logs.

2. **Portable PolyFlow SDK**
   - The interpreter, runtime, CLI, RCIR bridge, agent integration, and diagnostics can be distributed as a package/portable SDK.
   - A person can clone or receive PolyFlow, install the package in a fresh environment, and run `.poly` files without manually modifying `PYTHONPATH`.
   - `polyflow doctor`, `polyflow run`, `polyflow test`, `polyflow inspect`, `polyflow analyze`, and the RCIR-backed agent workflow work from the installed distribution.

3. **RCIR**
   - RCIR discovers a repository, resolves dependency relationships, ranks relevant context, compiles token-bounded context, and returns it deterministically.
   - RCIR improves over a defined non-RCIR baseline on the metrics that matter.
   - No hardcoded benchmark answers, stale artifacts, mock evidence, or TEST-set tuning are permitted.

4. **Real AI agent integration**
   - The same model performs the same coding tasks under:
     - baseline condition without RCIR,
     - RCIR condition.
   - The agent actually inspects files, edits code, runs tests, and produces non-empty diffs.
   - Success is independently verified.
   - Token usage is measured from the provider wherever provider usage metadata exists.

5. **Token and cost/credit reduction**
   - Distinguish three different measurements:
     1. semantic representation/context compression,
     2. context tokens delivered to the model,
     3. real provider-measured input/output/total tokens.
   - Do not combine them into one marketing percentage.
   - If an IDE exposes real credit usage through an API/export/log, capture it.
   - If it does not expose credits, report token reduction and a clearly labelled cost-equivalent estimate only where pricing is known.

6. **Extreme external validation**
   - After the current Nextcloud benchmark is repaired and frozen, validate the system against **Frappe + ERPNext together**.
   - Measure the actual repository size. Do not pre-write “10K”, “50K”, or any other file count.
   - Build a deterministic PolyFlow semantic representation of the complete in-scope ERPNext/Frappe system.
   - Run RCIR over the real repositories.
   - Demonstrate difficult cross-module changes with measured context reduction, dependency coverage, and agent results.

7. **Presentation bundle**
   - A single reproducible folder must contain:
     - exact commits,
     - commands,
     - benchmark outputs,
     - token A/B evidence,
     - interpreter demos,
     - agent evidence,
     - ERPNext/Frappe scale evidence,
     - presentation-safe summaries generated from raw results.

The final claim must be evidence-driven:

> PolyFlow provides a portable feature-centric polyglot runtime, while RCIR supplies repository intelligence that reduces the amount of code an AI coding agent must consume without losing the critical change context required to complete real software-engineering tasks.

Do not claim a particular percentage until a fresh benchmark measures it.

---

# 2. Current State That Must Be Preserved

The latest commit already includes substantial work. Do not rebuild these components from zero:

- RCIR v8.5.2 benchmark contract.
- Cryptographic provenance envelopes.
- Dataset, graph, ground-truth, config, and code hashes.
- Contract-feasibility checking.
- Manifest generation.
- Run-consistency scanning.
- Stage 1–14 test suites.
- Deterministic retrieval/context evaluation.
- Source-derived Nextcloud adapters.
- R0 baseline artifact.
- Validation-only ranker selection.
- Separate diagnostic P@20/P@50 handling.
- Turn-budget agent matrix.
- Real provider probing.
- Worktree validation.
- Acceptance and regression harnesses.
- `polyflow-sdk/`.
- `.poly` parser/runtime/linker/error handling in the main PolyFlow package.
- PolyFlow CLI concepts.
- Existing RCIR graph/context/compiler architecture.

Improve or unify them. Do not create parallel replacement implementations unless the old path is deliberately deprecated with compatibility shims.

---

# 3. Current Benchmark Snapshot

The currently committed v8.5.2 result is useful development evidence but **must not be the final presentation benchmark**, because it was produced from a dirty development state based on PolyFlow commit `48c6f617...`, while the reviewed repository HEAD is now `989249cf...`.

Current recorded results:

| Area | Current result |
|---|---:|
| Formal run validity | `VALID` for the recorded development run |
| Architecture verdict | `OPTION_C_REJECTED` |
| Contract | `8.5.2`, feasible |
| Impact macro recall | `84.33%` |
| Worst-task pool recall | `66.67%` |
| Silent misses | `3` |
| Test dependency MRR | `0.4728` |
| Test nDCG@50 | `0.3911` |
| Selected ranker | `R0` |
| Ranker improvement over R0 | `0%` |
| Critical source recall @4k | `73.33%` |
| Mean 4k context tokens delivered | `2851.8` |
| Context budget violations | `0` |
| Determinism | `PASS` |
| Process-level hash-seed determinism | `PASS` |
| Type-flow coverage | `90%` |
| Type-flow resolved precision | `57.14%` |
| Wrong-exact rate | `42.86%` |
| Agent completion | `0%` |
| Current 8-turn RCIR tokens | `2166` |
| Current 8-turn baseline tokens | `1976` |
| Graph nodes | `48,611` |
| Graph edges | `143,225` |
| Graph ingest total | `~5.48 s` |
| Retrieval mean | `~1.99 s/task` |
| Retrieval p95 | `~10.59 s/task` |
| Context compile mean | `~21 ms/task` |
| Peak RSS | `~469 MB` |

This tells us exactly where to spend effort. The system is no longer failing everywhere. The remaining blockers are concentrated.

---

# 4. First Priority: Produce the Final Clean Nextcloud Benchmark

Do not move to ERPNext until this stage is complete.

## 4.1 Create a clean benchmark execution model

A formal benchmark must execute from a clean source checkout.

Requirements:

- Current PolyFlow source commit must be recorded exactly.
- Current Nextcloud target commit must be recorded exactly.
- Both source trees must be clean before execution.
- Generated benchmark output must not make the source checkout “dirty” for provenance purposes.
- Use a separate run directory:

```text
experiments/rcir_runs/
  <run_id>/
    manifest/
    raw/
    results/
    reports/
    logs/
```

or an equivalent ignored artifact location.

The benchmark source/config remains tracked. Generated evidence belongs to a run directory.

Do not “restamp” artifacts from older executions with new provenance.

## 4.2 Formal execution must start from empty outputs

Before every release benchmark:

- create a new run directory,
- assert it contains no previous result artifacts,
- run every stage,
- assert required outputs were newly created,
- scan every output for matching provenance.

No formal stage may consume a committed historical JSON result merely because that file exists.

## 4.3 Preserve v8.5.2 history

Do not overwrite old contracts or historical results.

If benchmark architecture, datasets, thresholds, or evaluation semantics change materially, create a new version such as `8.5.3` or `8.6`.

Keep old evidence available for comparison.

---

# 5. Main Technical Blocker: Fix PHP Type Flow Properly

Current formal failure:

```text
coverage             = 90.0%
resolved precision   = 57.14%
wrong exact rate     = 42.86%
required precision   >= 85%
required wrong exact <= 5%
```

Current wrong predictions include:

```text
$user->getUID()
expected receiver: OCP\IUser
predicted receiver: bool

$file->getId()
expected receiver: OCP\Files\File
predicted receiver: string

$file->getStorage()
expected receiver: OCP\Files\File
predicted receiver: string

$storage->getShare()
false abstention

$share->canSeeContent()
false abstention

$parentFolder->getDirectoryListing()
false abstention
```

Do not repair this by restoring hardcoded Nextcloud answers.

## 5.1 Add a type-flow trace mode

Before changing the analyzer, add a deterministic debug trace for a selected call site.

Example:

```bash
python -m rcir.types.php_type_flow \
  --repo <nextcloud> \
  --file apps/files/lib/Controller/ApiController.php \
  --trace-line 76
```

Trace:

```text
method entered
parameter bindings
property bindings
assignment observed
old variable binding
new variable binding
method-summary lookup
source declaration used
branch narrowing
scope enter/exit
final receiver binding
confidence
evidence
```

Save the trace for every failing ground-truth call. This prevents fixing the symptom without finding the bad state transition.

## 5.2 Replace fragile method/parameter parsing where necessary

The analyzer may remain lightweight, but it must correctly distinguish:

- parameter receiver type,
- return type,
- local variable type,
- method return type,
- scalar arguments,
- object receiver.

No scalar return/argument type may overwrite the receiver type merely because it appears on the same source line.

Implement robust handling for:

- constructor parameters,
- PHP 8 promoted properties,
- nullable types,
- union types,
- intersection types,
- return types,
- PHPDoc,
- assignments,
- method-return assignments,
- null-safe chains,
- `instanceof`,
- foreach element types,
- catch variable types,
- closures,
- arrow functions,
- early return/throw,
- branch joins.

If the regex state machine is becoming structurally unsafe, replace the critical source parser with a real PHP parser/tree-sitter layer rather than accumulating more regex exceptions.

## 5.3 Correct assignment propagation

Cases such as:

```php
$file = $this->userFolder->get($file);
```

must replace the original scalar/string parameter binding with the method-return binding.

Then:

```php
$file->getId()
$file->getStorage()
```

must use the updated object type.

Similarly:

```php
$storage = $file->getStorage();
$share = $storage->getShare();
```

must propagate through source-derived method summaries.

## 5.4 Source-derived method summaries only

Continue the current source-derived method summary design.

Method summaries may come from:

- PHP return type declaration,
- interface declaration,
- parent declaration,
- validated PHPDoc,
- canonical hierarchy.

Each summary must preserve provenance.

Do not manually seed ground-truth answers.

## 5.5 Inheritance/interface lookup

If a concrete class does not declare a method-return contract directly:

- resolve implemented interfaces,
- resolve parent classes,
- locate inherited declaration,
- derive return type.

## 5.6 Confidence semantics

`PROVEN_EXACT` must mean the type was actually proven.

Confidence states should remain conservative:

```text
PROVEN_EXACT
INTERFACE_BOUND
HEURISTIC_INFERRED
AMBIGUOUS
UNKNOWN
```

## 5.7 Type-flow acceptance

Do not proceed to final benchmark freeze until the existing adjudicated cases satisfy the frozen contract.

Minimum current gate:

```text
coverage             >= 0.60
resolved precision   >= 0.85
wrong exact rate     <= 0.05
invalid ground truth = 0
```

Engineering target for presentation:

```text
coverage             >= 0.90
resolved precision   >= 0.90
wrong exact rate     <= 0.05
```

Do not alter TEST labels to reach this.

---

# 6. Improve Retrieval So RCIR Beats R0 Instead of Selecting R0

Current validation selection:

```text
R0                  0.3081
OperationCascade    0.3070
Coverage            0.3068
AnchorCoverageRRF   0.2944
ExactFirst          0.2907
```

The current “best RCIR ranker” is therefore the baseline itself.

## 6.1 Keep TEST frozen

All ranker changes must be designed/tuned with DEV and VALIDATION only. After selection is frozen, run TEST once for that benchmark version.

## 6.2 Rank files, not noisy duplicate entities

Introduce a `FileEvidenceAggregate` or equivalent.

For each file aggregate:

```text
best hop distance
exact entity evidence
direct incoming relation count
direct outgoing relation count
relation types
relation diversity
type compatibility
source-evidence confidence
test relationship
boundary relationship
event relationship
config/DI relationship
operation compatibility
lexical evidence
hub degree / generic-hub penalty
number of independent evidence channels
```

Then rank files directly or perform entity ranking followed by a formally specified file aggregation.

## 6.3 Calibrate channel reliability

Using DEV/VALIDATION only, measure per-channel:

```text
precision
recall
unique relevant hits
false-positive rate
mean rank contribution
```

Use these values to calibrate deterministic weights.

## 6.4 Operation-aware weighting

Different tasks should prioritize different evidence:

```text
signature change -> callers, implementations, overrides, tests
event change     -> dispatchers, listeners, payload consumers, tests
config change    -> interface, implementation, DI, config consumers
route change     -> controller, route declaration, clients, tests
```

Represent weights in configuration, not benchmark paths.

## 6.5 Hub penalty

Add deterministic penalties for high-degree generic nodes unless they have strong task-specific evidence. Do not remove direct exact dependencies.

## 6.6 Validation selection

Store every candidate configuration, validation metrics, objective, and selection reason.

Prefer a leave-one-task-out sensitivity report because the validation split is small.

## 6.7 Option B target

The current Option B contract requires at least 5% relative MRR improvement over R0.

Do not weaken this because the current result is 0%. Improve the architecture until there is a real measurable advantage, or report honestly that it does not.

---

# 7. Fix the RCIR-to-Agent Context Interface

This is a concrete integration issue in the current code.

`ConcreteRCIRContextProvider.retrieve()` returns fields similar to:

```text
entities_found
entries
token_budget
tokens_delivered
```

while `RepoToolEnvironment.request_context()` expects fields similar to:

```text
context_markdown
tokens_added
entities
duplicates_skipped
```

Introduce one canonical `ContextRetrievalResult` model:

```text
entries
entity_ids
rendered_markdown
tokens_added
duplicates_skipped
requested_symbol
source_task_id
budget
```

Every context provider and agent tool must use it. No dictionary-shape guessing.

For every context request record:

```text
requested symbol
candidate entries
returned entries
already-seen skipped
exact rendered token count
cumulative context tokens
budget remaining
```

Only delivered entries become `already_seen`.

Add an end-to-end synthetic test with 8 matching entries, limit 5: first call returns 5, second returns remaining 3, and real `RepoToolEnvironment.request_context()` receives non-empty RCIR markdown.

---

# 8. Repair and Strengthen the Real Agent Benchmark

The current live provider connection works, but the coding experiment does not.

Current primary result:

```text
RCIR     0/1 successes
baseline 0/1 successes
```

## 8.1 Do not reuse/restamp old trials

A cached trial may be reused only if all execution/code/context/model/test hashes match exactly.

For formal release benchmarking, disable trial cache and always rerun.

## 8.2 Fix regression status semantics everywhere

Use:

```text
PASS
FAIL
SETUP_ERROR
NOT_MEASURED
```

Only `PASS` satisfies formal regression validation.

Audit helper functions so exit code `3` can never accidentally become success.

## 8.3 Valid worktree only

Formal success requires:

```text
worktree_mode = git_worktree
```

A partial shadow copy is development-only and must be `INVALID_TRIAL`.

## 8.4 Expand beyond one task

Create 5–10 representative tasks if feasible:

```text
simple local method edit
signature propagation
route/controller change
event contract change
config/DI change
cross-file behavior change
```

Each task needs target file/symbol, context mapping, acceptance verifier, targeted regression, timeout, and difficulty.

## 8.5 Repeated trials

Use:

```text
conditions = baseline, rcir
turn budgets = 5, 8
replicates >= 3
preferred = 5
```

Same model/settings for paired conditions.

## 8.6 Use an agent-capable model

Keep the 1.5B model as a small-model limitation experiment if desired.

For the headline agent benchmark use a model capable of reliable tool calls, under identical paired baseline/RCIR settings.

## 8.7 Success definition

A trial succeeds only if all are true:

```text
real inference
valid isolated worktree
acceptance BEFORE = expected fail
at least one real tool call
non-empty code diff
acceptance AFTER = pass
syntax/compile = pass
targeted regression = pass
gatekeeper = APPROVE
```

---

# 9. Build Real Token and Cost Telemetry

This is essential for the presentation.

## 9.1 Historical 80.5% claim

The repository contains historical claims around:

```text
20,473 baseline context tokens
~3,995 RCIR context tokens
~80.5% reduction
```

Keep this as historical evidence, but label it:

```text
HISTORICAL_CONTEXT_SIZE_ESTIMATE
```

Do not present it as current provider-billed token reduction.

Remove or qualify unconditional “80.5% token reduction” SDK copy until a new live paired run supports it.

## 9.2 Canonical usage event

Create `UsageRecord`:

```text
run_id
trial_id
task_id
condition
provider
model
turn
measurement_source
input_tokens
output_tokens
total_tokens
cached_input_tokens if available
context_tokens
tool_result_tokens
latency
provider_cost_usd if measurable
cost_method
ide_credits if explicitly exposed
credit_method
timestamp
```

Measurement sources:

```text
PROVIDER_NATIVE
TOKENIZER_EXACT
ESTIMATED
IDE_EXPORTED
```

## 9.3 Provider integrations

- OpenAI: returned usage metadata.
- Anthropic: returned input/output usage.
- Ollama: `prompt_eval_count` + `eval_count`.
- Gemini: use official usage metadata where available. Only fall back to estimation when necessary and label it.

## 9.4 IDE credits

Create `IDEUsageAdapter` for documented API/export/log sources.

Do not scrape private UI internals or invent credit conversions.

If the IDE does not expose credits:

```text
IDE_CREDITS = NOT_MEASURED
```

## 9.5 Report three reductions separately

### A. Representation compression
Original repository source representation vs PolyFlow semantic representation.

### B. RCIR context compression
Baseline candidate/source context tokens vs RCIR delivered context tokens.

### C. Live model token reduction
Baseline provider tokens vs RCIR provider tokens.

Never call A or B “provider savings”.

## 9.6 Paired A/B experiment

Same revision, model, system prompt, tools, max turns, and acceptance tests. Only context strategy differs.

Store task-level baseline/RCIR input tokens, output tokens, total tokens, latency, and success.

Report both all valid paired trials and successful paired trials.

## 9.7 Statistical output

Report:

```text
mean
median
p25
p75
p95 where meaningful
absolute token delta
percentage delta
task-level deltas
confidence interval where sample size permits
```

Do not cherry-pick.

## 9.8 Presentation target

A useful engineering target is:

```text
>= 50% median provider input-token reduction
```

on successful paired trials with no drop in task success.

This is a target, not a number to force. Present the measured result.

---

# 10. Make Token Reduction Visible in the CLI

Add:

```bash
polyflow benchmark tokens ...
```

with text, JSON, and CSV output.

It should display raw baseline/RCIR tokens, success, deltas, and measurement source. No hardcoded demo values.

---

# 11. Optimize RCIR Before ERPNext Scale

Current Nextcloud retrieval p95 is about 10.6 seconds.

## 11.1 Build a run-scoped source evidence index

Build once:

```text
symbol -> entities/files
class/interface -> implementations
method -> callers/callees
event -> construct/dispatch/listeners
route -> controller/method
config -> consumers/providers
source -> tests
file -> module
file -> imports
type -> hierarchy
```

## 11.2 Remove per-query full graph scans

Use indexed lookups for hierarchy, events, routes, config, and tests.

## 11.3 Cache source-derived evidence

Cache by repository commit, file hash, and extractor version.

## 11.4 Incremental graph update

Measure full cold build and changed-file incremental re-index.

## 11.5 Performance target

Aim for:

```text
Nextcloud retrieval p95 < 2 seconds
```

as an engineering objective. If not achieved, report the measured bottleneck honestly.

---

# 12. Clarify Channel B

Either connect Channel B to a real reusable `TypeFlowIndex` containing receiver-resolved call-site evidence, or rename it `TYPE_HIERARCHY`.

Reports must describe the actual implementation.

---

# 13. Preserve Source Evidence Through Ranking

Extend evidence vectors with auditable source evidence:

```text
evidence type
source file
source span
extractor/version
confidence
content hash
```

A presentation query must be able to answer:

```text
Why did RCIR include this file?
```

with real evidence rather than a score alone.


# 14. Portable PolyFlow SDK: Harden What Already Exists

There is already a `polyflow-sdk/` directory. Do not create another competing SDK.

The current SDK is conceptually correct but is not yet truly standalone enough.

Current problems include:

- `dependencies = []` despite runtime imports such as YAML.
- SDK interpreter imports main-repository packages.
- SDK runtime wraps the main-repository runtime.
- RCIR bridge requires `rcir` to exist on external `PYTHONPATH`.
- CLI manually inserts the monorepo root into `sys.path`.
- parser behavior is duplicated between SDK and the main PolyFlow parser.
- package portability has not been proven in a clean environment.

Fix these.

## 14.1 One canonical `.poly` grammar and AST

There must be one canonical implementation supporting:

```text
@contract
@schema
@link
@merge
@error-map
@rationale
@decision
@audit
@ledger
@standard
language cells
```

SDK and development repository must use the same parser.

Add:

```text
grammar_version
AST schema version
```

to parsed output.

Do not keep a simplified second parser that can silently interpret a file differently.

## 14.2 Compatibility shims

If code is moved into the packaged implementation:

- retain temporary import shims for old paths,
- mark them deprecated,
- add tests ensuring old and new imports resolve to the same implementation.

## 14.3 Build a real distribution

Produce:

```text
dist/
  polyflow_sdk-<version>-py3-none-any.whl
  polyflow-sdk-portable-<version>.zip
  checksums.sha256
```

The portable bundle must contain everything required for PolyFlow itself:

```text
CLI
language parser/AST
runtime integration
schema/link/merge/error systems
RCIR package/runtime
agent integration
telemetry
examples
bootstrap scripts
license
version manifest
```

It does not need to bundle Java/Go/PHP/Node themselves. `polyflow doctor` should discover host toolchains.

## 14.4 Eliminate `sys.path` hacks

Installed commands must not depend on adding the PolyFlow monorepo root manually.

Mandatory black-box portability test:

1. Build distribution.
2. Create an empty temporary directory outside the PolyFlow repository.
3. Create a clean virtual environment.
4. Install the built artifact.
5. Copy only a sample `.poly`.
6. Execute:

```bash
polyflow --version
polyflow doctor
polyflow inspect sample.poly
polyflow run sample.poly
polyflow test .
```

7. Place an unrelated source repository there.
8. Execute:

```bash
polyflow analyze <repo>
```

The test must not use the original PolyFlow checkout through `PYTHONPATH`.

## 14.5 Declare real package dependencies

Populate packaging metadata with every actual dependency.

Use optional extras where appropriate, for example:

```text
providers
dev
visualization
```

Do not depend on packages that merely happen to exist on the developer machine.

## 14.6 Cross-platform tests

Run the core package/CLI portability test on:

```text
Windows
Linux
macOS
```

Language runtime checks may be conditional on installed host compilers.

---

# 15. Make the Interpreter a First-Class Presentation Component

The custom interpreter must be demonstrable directly, not merely visible in source.

Add:

```bash
polyflow inspect <file.poly>
```

It should show:

```text
grammar version
contracts
schemas
language cells
links
merge strategy
error maps
standards
decisions/rationales
source references
syntax diagnostics
```

Also add machine-readable AST output:

```bash
polyflow inspect <file.poly> --json
```

or:

```bash
polyflow ast <file.poly> --json
```

If feasible in this implementation cycle add:

```bash
polyflow lint <file.poly>
polyflow fmt <file.poly>
```

Syntax errors should include:

```text
file
line
column where possible
directive/cell
error code
human message
suggested correction
```

---

# 16. No Emulated Runtime Success in Formal Demonstrations

The main PolyFlow runtime contains a fast mode that can emulate successful execution for some non-Python language cells.

This may remain as an explicitly marked fixture/development mode, but it must never be counted as formal multi-language execution.

Formal runtime results must include:

```text
execution_mode = NATIVE_RUNTIME | EMULATED_TEST_MODE
toolchain
toolchain_version
```

Presentation success must use only `NATIVE_RUNTIME`.

Real paths:

```text
Python -> Python runtime
JS     -> Node
TS     -> real compile/transpile + runtime
Java   -> javac/java
Go     -> go compiler/runtime
PHP    -> PHP
```

If a toolchain is missing:

```text
NOT_MEASURED / TOOLCHAIN_UNAVAILABLE
```

Do not return synthetic success.

---

# 17. Structured PolyFlow Error System

The current `polyflow_errors.log` idea should become portable, structured, and project-local.

Use:

```text
.polyflow/
  logs/
    errors.jsonl
    errors.log
```

Each error record should include:

```text
error_id
timestamp
poly_file
cell language
cell tag
source span
runtime
raw exception
normalized category
human explanation
recommended fix
run ID
toolchain version
mapped/unmapped
```

Define categories such as:

```text
PF_PARSE
PF_SCHEMA
PF_LINK
PF_RUNTIME
PF_TOOLCHAIN
PF_TIMEOUT
PF_CONTRACT
PF_RCIR
PF_AGENT
```

The human-readable `.log` should be generated from the structured event.

Add:

```bash
polyflow errors
polyflow errors --last 10
polyflow errors --json
```

This gives a clean interpreter/error-handling demonstration without opening a random log file in an editor.

---

# 18. Add a Portable `self-test`

Add:

```bash
polyflow self-test
```

It should create temporary fixtures and verify:

```text
parse
schema validation
link resolution
real Python cell execution
error translation
structured error logging
RCIR import/availability
CLI installation integrity
package resource access
```

If Node/Java/Go/PHP are installed, exercise those runtimes too.

Output a machine-readable result file in addition to terminal output.

---

# 19. Make `polyflow agent` a Real Agent or Rename It

The current SDK `polyflow agent` command primarily:

- builds a graph,
- retrieves context,
- estimates token savings,
- calculates blast radius,
- prints that the pipeline is ready.

That is useful planning behavior, but it is not the same as the real editing/testing agent used by the RCIR experiment.

Use one of these designs.

## Preferred

Wire:

```text
polyflow agent
```

to:

```text
ReActAgentRunner
RepoToolEnvironment
RCIR ContextProvider
provider telemetry
acceptance/test tooling
```

Example:

```bash
polyflow agent \
  "change request" \
  --repo <repo> \
  --budget 4000 \
  --provider <provider> \
  --model <model>
```

## Alternative

Rename the current planning-only behavior:

```text
polyflow plan
```

and reserve:

```text
polyflow agent
```

for the real editing/testing loop.

Do not present planning-only output as autonomous engineering.

---

# 20. Add a Source-Reference Directive for Existing Enterprise Systems

To represent a large existing application without manually copying every source line into `.poly`, add a source-reference directive.

Suggested form:

```text
@source
path: "erpnext/accounts/doctype/sales_invoice/sales_invoice.py"
language: "python"
role: "service"
symbol: "SalesInvoice"
sha256: "..."
@end
```

The exact syntax may differ, but it must be part of the canonical grammar.

This is different from `@link`, which links `.poly` modules.

A source reference must:

- point to real repository source,
- identify language/role,
- optionally identify a symbol/source span,
- contain or derive a content hash,
- be available to RCIR,
- appear in AST output,
- support deterministic migration,
- preserve traceability to the native source.

This is the foundation for a full ERPNext/Frappe semantic mirror.

---

# 21. Gate Before ERPNext/Frappe

Do not begin the final extreme validation until all of the following are true:

```text
clean Nextcloud formal run
integrity PASS
contract feasibility PASS
type-flow PASS
context PASS
determinism PASS
ranking behavior frozen
agent has real successful trials
provider token A/B telemetry works
portable SDK self-test passes outside repo
```

Then freeze that Nextcloud benchmark version.

---

# 22. Pin Exact Frappe + ERPNext Repositories

Use the real repositories:

```text
frappe/frappe
frappe/erpnext
```

Pin exact commits before benchmarking.

Generate a repository inventory artifact from the actual checkout:

```json
{
  "frappe_commit": "...",
  "erpnext_commit": "...",
  "total_files": 0,
  "source_files": 0,
  "loc": 0,
  "languages": {},
  "doctype_count": 0,
  "python_files": 0,
  "js_ts_files": 0,
  "json_metadata_files": 0
}
```

The zeroes above are placeholders for the generated schema, not expected results.

Never pre-write “10K files”, “50K files”, “millions of lines”, etc.

Use the measured values.

---

# 23. Build a Frappe/ERPNext RCIR Adapter

Do not add benchmark-answer paths.

The adapter must derive framework semantics generically.

## 23.1 Python

Use Python AST for core structure.

Extract:

```text
imports
functions
classes
inheritance
method calls where resolvable
decorators
whitelisted methods
controller hooks
type hints
framework entry points
```

## 23.2 JavaScript/TypeScript

Extract:

```text
imports/exports
API calls
form scripts
client event handlers
module relationships
server endpoint references
```

## 23.3 DocType JSON

Parse real DocType metadata.

Extract typed edges for:

```text
fields
Link fields
Dynamic Link fields
child tables
options
permissions
controllers
related DocTypes
```

## 23.4 `hooks.py`

Derive relationships for framework hooks such as:

```text
document events
override classes
scheduled events
permission hooks
registered handlers
framework boundary registrations
```

Use only what exists in the pinned Frappe version.

## 23.5 Other framework artifacts

Handle relevant:

```text
reports
fixtures
patches
templates
workflows
metadata
```

where they materially affect change impact.

Every framework-derived relation must carry:

```text
source file
source span
evidence type
extractor version
confidence
content hash
```

---

# 24. Complete ERPNext → PolyFlow Semantic Migration

Implement a deterministic migration command:

```bash
polyflow migrate erpnext \
  --frappe <frappe-path> \
  --erpnext <erpnext-path> \
  --output <output-dir>
```

Suggested output:

```text
erpnext-polyflow/
  polyflow.project.json
  inventory.json
  coverage.json
  features/
    <discovered modules...>
```

Do not hardcode a module list that is not present in the pinned repositories.

Discover it.

## 24.1 Coverage ledger

For every in-scope source artifact record:

```text
source path
language/type
mapped PolyFlow feature
mapping type
source hash
RCIR entities
status
reason if excluded
```

Allowed statuses:

```text
MAPPED_SOURCE_REFERENCE
MAPPED_SCHEMA
MAPPED_EXECUTABLE_CELL
MAPPED_TEST
EXCLUDED_VENDOR
EXCLUDED_GENERATED
UNRESOLVED
```

“Complete semantic conversion” is allowed only when every in-scope artifact is accounted for.

## 24.2 Distinguish semantic mirror from execution parity

### Semantic mirror

The entire in-scope repository is represented through PolyFlow contracts, source references, schemas, and RCIR relationships.

### Executable PolyFlow verticals

Selected flows are actually executable through `.poly` runtime cells.

Do not call a semantic mirror “full execution parity”.

If full parity is eventually claimed, it must be backed by upstream tests and behavioral comparison.

---

# 25. Select Executable ERPNext Vertical Slices

After inspecting the pinned repository, choose representative business-critical verticals.

Possible categories where present include:

```text
identity / roles / permissions
CRM / customer
selling
buying
stock/inventory
accounting
payments
manufacturing
HR/payroll
projects/support
assets
```

For each selected vertical:

- identify original native source,
- generate/author `.poly` representation,
- connect schemas/source references,
- provide executable cells where appropriate,
- preserve test relationships,
- run real validation.

The final presentation may show the entire ERPNext/Frappe system semantically mapped while live-executing several representative verticals.

That is more defensible than pretending every code path has been rewritten and behaviorally proven.


# 26. Define Compression Metrics Correctly

The ERPNext/Frappe experiment must produce separate metrics.

## 26.1 File-to-feature compression

```text
original in-scope source files
generated PolyFlow feature modules
ratio
```

This measures organization/representation.

## 26.2 Semantic representation token compression

```text
tokens required to serialize the in-scope native source
tokens required for the PolyFlow semantic contracts/index representation
```

This measures compact semantic representation.

## 26.3 RCIR task-context compression

For every benchmark task:

```text
baseline relevant/broad context
RCIR delivered context
```

## 26.4 Live provider token reduction

Measure from paired real agent experiments.

Do not combine these four measurements into one percentage.

If representation compression is 90% but provider token reduction is 55%, report both.

---

# 27. ERPNext RCIR Benchmark Tasks

Create a real ground-truth task set after understanding the pinned repositories.

Use multiple difficulty levels.

## Tier 1: Local

```text
method behavior
validation rule
local schema change
```

## Tier 2: Cross-file

```text
controller + tests
DocType + Python handler
client + server
```

## Tier 3: Cross-module

```text
schema/field used across modules
permission/role behavior
stock/accounting dependency
workflow event propagation
```

## Tier 4: Architectural

Examples may include:

```text
replace/extend a shared abstraction
change a central framework hook contract
change a shared schema relationship
change a cross-module service interface
```

Ground truth must be independently source-adjudicated.

Never define correctness as “whatever RCIR retrieved”.

---

# 28. ERPNext Baselines

Measure RCIR against more than one baseline where feasible.

## Baseline A — Tool-enabled agent without RCIR

Same model/tools/task, no RCIR context.

## Baseline B — Lexical/search-only retrieval

Traditional search/grep style context discovery.

## Baseline C — Broad context inclusion

Where the task/repository fits within model constraints.

If full context is impossible:

```text
FULL_CONTEXT = INFEASIBLE
```

Do not invent a token number.

That infeasibility is itself useful evidence at enterprise scale.

---

# 29. ERPNext/Frappe Success Metrics

Report:

```text
repository file count
source file count
LOC
language breakdown
DocType count

graph nodes
graph edges
graph build time
peak RSS
incremental update time

candidate recall
critical source recall
MRR
nDCG
silent misses

context tokens
context compression
provider input tokens
provider total tokens

agent completion
syntax/compile success
targeted test success
regression success
turns
latency
```

For architectural tasks also report:

```text
expected affected files
retrieved affected files
false negatives
false positives
```

---

# 30. Freeze External TEST

Use:

```text
DEV
VALIDATION
TEST
```

for ERPNext/Frappe too.

Framework adapter bugs found during DEV/VALIDATION may be corrected.

Once external TEST is opened:

- no tuning under that benchmark version,
- architecture/config changes require a new version,
- preserve the old result.

This is necessary if the final external result is going to mean anything.

---

# 31. Presentation Folder

After the final clean Nextcloud and ERPNext/Frappe experiments, create:

```text
showcase/
  README.md
  manifest.json

  01_polyflow_interpreter/
    example.poly
    broken_example.poly
    inspect_output.txt
    run_output.json
    error_output.jsonl

  02_nextcloud_rcir/
    benchmark_summary.json
    retrieval_metrics.json
    context_curve.json
    determinism.json
    type_flow.json

  03_token_ab/
    paired_trials.json
    paired_trials.csv
    token_summary.json
    cost_summary.json
    measurement_method.md

  04_agent/
    successful_trial/
      prompt.txt
      rcir_context.md
      provider_usage.json
      tool_calls.jsonl
      diff.patch
      acceptance_before.log
      acceptance_after.log
      regression.log
      gatekeeper.json

  05_erpnext_extreme/
    repository_inventory.json
    migration_coverage.json
    graph_metrics.json
    benchmark_summary.json
    token_summary.json
    sample_poly_features/
    difficult_change_examples/

  charts/
    generate_charts.py
    generated/

  scripts/
    run_quick_demo.*
    verify_showcase.py
```

All summaries must be generated from raw evidence.

Do not manually type benchmark percentages into presentation JSON.

---

# 32. Add `polyflow demo`

Create:

```bash
polyflow demo --profile final
```

It should verify and display frozen benchmark evidence while running a few fast live proofs.

Suggested flow:

```text
1. Print SDK version + polyflow doctor
2. Inspect a .poly file
3. Execute a real multi-language sample
4. Demonstrate a deliberate error and structured translation
5. Load the signed/frozen Nextcloud RCIR result
6. Run one live RCIR impact/context query
7. Display baseline vs RCIR measured token usage
8. Display one successful agent-edit proof
9. Display Frappe + ERPNext inventory and migration coverage
10. Run one live ERPNext RCIR query
11. Print reproduction commands and artifact hashes
```

Every displayed item must carry one status:

```text
LIVE
FROZEN_MEASURED
HISTORICAL
NOT_MEASURED
```

Do not make a cached result look live.

---

# 33. Final Presentation Narrative

The final demonstration should tell one coherent story.

## Part A — The fragmentation problem

Show a traditional feature spread across backend, frontend, schemas, tests, configuration, and documentation.

## Part B — PolyFlow

Show one `.poly` feature representation containing or linking:

```text
contract
schema
source references
language cells
tests
error policy
rationale/decisions
```

Use the portable interpreter to inspect and execute it.

## Part C — RCIR

Show:

```text
large repository
large node/edge graph
one requested code change
small evidence-backed RCIR context
```

Explain why each selected file is relevant.

## Part D — Real token usage

Show raw paired counts first:

```text
baseline input/total tokens
RCIR input/total tokens
```

Then show the measured percentage reduction.

## Part E — Agent

Show:

```text
task
context
tool calls
real diff
acceptance before/after
regression pass
provider usage
```

## Part F — Extreme scale

Show actual Frappe + ERPNext repository statistics.

Then show:

```text
semantic migration coverage
PolyFlow feature organization
RCIR graph
difficult cross-module query
context/token result
```

Avoid spending presentation time on every internal benchmark version used during development.

---

# 34. Claim Hygiene

Before presentation, search the repository for claims such as:

```text
production-grade
80.5%
90%
zero regressions
millions of lines
complete
verified
autonomous
```

Require a current evidence artifact for every claim.

### Good

```text
“On benchmark run X, RCIR reduced median provider input tokens by 68.4% across N paired successful trials.”
```

### Bad

```text
“RCIR always reduces tokens by 80–90%.”
```

### Good

```text
“The Frappe/ERPNext migration accounted for 99.2% of in-scope source artifacts; the remainder are explicitly categorized.”
```

### Bad

```text
“We converted every ERPNext functionality.”
```

unless coverage and behavioral parity genuinely prove it.

---

# 35. Full Test Matrix Before Final Freeze

Run:

```text
PolyFlow parser tests
PolyFlow schema tests
PolyFlow linker tests
PolyFlow merge tests
PolyFlow error-map tests
PolyFlow runtime tests
portable SDK tests
CLI tests

RCIR Stage 1–14 tests
new type-flow tests
ContextProvider integration tests
token telemetry tests
agent evidence tests
run-lifecycle tests
report truthfulness tests
packaging black-box tests
```

Then:

```text
Nextcloud formal benchmark
Nextcloud paired agent benchmark
Nextcloud token A/B benchmark
```

Only after those:

```text
Frappe/ERPNext migration
Frappe/ERPNext RCIR benchmark
Frappe/ERPNext paired token/agent experiment
```

---

# 36. Mandatory New Regression Coverage

Add tests covering at least:

```text
type-flow scalar cannot replace object receiver incorrectly
method-return assignment overwrites scalar parameter binding
inherited/interface return type lookup
chained return propagation
catch variable typing
scope isolation
no hardcoded type answers

ContextProvider result schema is identical end-to-end
request_context receives non-empty RCIR markdown
already_seen only tracks delivered entries
strict token budget is enforced

formal trials cannot restamp stale evidence
formal trial cache disabled or exact-hash validated
NOT_MEASURED regression cannot pass
zero tool calls cannot pass
partial shadow copy cannot pass

provider token measurement source is recorded
Gemini native usage is used when available
estimated tokens are labelled
cost calculation records pricing basis
IDE credits remain NOT_MEASURED unless explicitly available

SDK installs outside repo
SDK has no monorepo sys.path dependency
canonical parser behavior is identical
real-runtime execution cannot silently use emulator
structured project-local error log works

ERPNext migration maps every in-scope artifact or records exclusion
migration is deterministic
source hashes are stable
generated PolyFlow AST is valid
```

---

# 37. Final Formal Gates

Do not manufacture `OPTION_A_ACCEPTED`.

The final presentation should not proceed with the current state where:

```text
type-flow = FAILED
agent = FAILED
ranker improvement = 0%
```

A strong final state should have:

```text
Integrity                PASS
Contract feasibility     PASS
Impact                   PASS
Ranking                  PASS
Context                  PASS
Type Flow                PASS
Canonicalization         PASS
Determinism              PASS
Agent                    PASS on multi-task evidence
Token A/B                MEASURED with valid paired trials
SDK portability          PASS
```

Option A or Option B is acceptable if its real prerequisites are satisfied.

Do not change the verdict label merely for presentation optics.

---

# 38. Recommended Implementation Order

Implement in this order unless a dependency forces a small change:

```text
1. Fix PHP TypeFlow
2. Fix ContextProvider ↔ RepoToolEnvironment schema
3. Remove stale agent-trial restamping/caching
4. Fix all agent regression/status semantics
5. Add provider-native usage telemetry
6. Expand agent tasks and replicates
7. Improve validation-selected file ranking over R0
8. Build source-evidence indices and reduce retrieval p95
9. Run the complete Stage/unit suite
10. Produce a clean current-HEAD Nextcloud run
11. Run paired real agent/token benchmark
12. Freeze the Nextcloud result
13. Unify and harden the portable PolyFlow SDK
14. Build wheel/portable bundle and clean-environment tests
15. Add inspect/lint/error/self-test/demo commands
16. Add @source/source-reference support and migration framework
17. Pin Frappe + ERPNext
18. Inventory actual repository scale
19. Build Frappe/ERPNext adapter
20. Generate complete semantic PolyFlow mirror
21. Create external benchmark ground truth
22. Freeze external ranker/config
23. Run external TEST
24. Run paired external token/agent experiment
25. Generate showcase folder
26. Verify every presentation claim from raw evidence
```

---

# 39. Required Final Deliverables

The work is finished only when the repository contains:

## A. Clean Nextcloud benchmark

Fresh current-source results with one consistent provenance chain.

## B. Real token benchmark

Paired baseline/RCIR trials with provider-native usage wherever available.

## C. Successful agent evidence

Multiple real tasks rather than one lucky demonstration.

## D. Portable SDK

Installable and runnable outside the PolyFlow source checkout.

## E. Custom interpreter proof

`.poly` inspect, parse, execute, diagnostics, and error logging.

## F. Frappe/ERPNext adapter

Source-derived Python, JS/TS, DocType, hooks, and framework relationships.

## G. Complete semantic migration

Every in-scope source artifact mapped, excluded, or unresolved with reason.

## H. Extreme benchmark

Measured at the actual repository size.

## I. Presentation folder

Commands, evidence, charts, and reproduction instructions.

## J. Final system report

Create:

```text
FINAL_SYSTEM_ASSESSMENT.md
```

including:

```text
exact source commits
environment/toolchain versions
test counts
Nextcloud benchmark
token A/B results
agent results
SDK portability
Frappe/ERPNext inventory
semantic migration coverage
external benchmark
known limitations
final verdict
```

No unsupported promotional language.

---

# 40. Final Completion Rule

Do not stop because code compiles.

Do not stop because unit tests pass.

Do not stop because RCIR retrieves some files.

Do not stop because a provider answers.

The work is complete only when the whole chain is proven:

```text
.poly source
  ↓
portable PolyFlow interpreter
  ↓
real runtime + diagnostics
  ↓
repository indexing
  ↓
RCIR evidence
  ↓
ranked token-bounded context
  ↓
real model usage
  ↓
tool-driven code modification
  ↓
acceptance + regression pass
  ↓
measured token delta
  ↓
reproducible artifacts
  ↓
large external Frappe/ERPNext validation
```

That is the final system to present.

---

# Current System Status — Short Version

**PolyFlow language/runtime:** Implemented and substantial. The main parser/runtime/linker/schema/error infrastructure exists. The remaining issue is unifying it with the SDK and proving real-runtime, standalone execution.

**Portable SDK:** Started, not yet proven portable. `polyflow-sdk/` already has the CLI, interpreter, runtime bridge, RCIR bridge, doctor command, and package metadata, but it still depends on monorepo imports/PYTHONPATH. It is not yet the finished Flutter-style distribution.

**RCIR core:** Working. Provenance, graph analysis, retrieval, context compilation, deterministic execution, source evidence, benchmark contracts, and run-integrity logic are now meaningful. Current impact/ranking/context/determinism results are broadly healthy.

**RCIR type flow:** The principal correctness blocker. Coverage is `90%`, but resolved precision is only **57.14%** and wrong-exact rate is **42.86%**. This must be fixed before the final benchmark.

**Ranking advantage:** Not yet demonstrated. `R0` remains the selected ranker and the current measured improvement over the R0 baseline is **0%**.

**Agent integration:** Live LLM inference is working, but formal coding-task completion is currently **0%**. The current evidence does not yet prove an RCIR-assisted coding-agent win.

**Token reduction:** Historical **80.5%** evidence is best treated as an estimated context-size reduction result, not the final live provider-token/IDE-credit claim. A new paired provider-measured benchmark is mandatory.

**Performance:** Context compilation is fast, but retrieval p95 is currently about **10.6 seconds**, which should be indexed/optimized before the much larger Frappe/ERPNext experiment.

**Frappe/ERPNext extreme validation:** Not implemented yet. It should be the final external proof after Nextcloud, agent, token telemetry, and portable SDK are clean.

**Overall:** PolyFlow is now a strong advanced prototype/research system with several genuinely working subsystems. It is **not yet presentation-final**, but the remaining work is concentrated rather than open-ended: fix type flow, prove the agent and real token reduction, harden the portable SDK, then execute the Frappe/ERPNext extreme validation and freeze the resulting evidence.
