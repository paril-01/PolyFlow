# RCIR v8.3 — Canonical Graph Fabric, Real Type Flow, Leakage-Free Ranking, Context Planning, and Real Agent Validation

You are operating as a principal compiler engineer, static-analysis architect, information-retrieval researcher, benchmark scientist, and autonomous software-engineering infrastructure engineer inside the PolyFlow repository.

Your task is to audit, correct, and experimentally evolve RCIR from the current repository HEAD:

`07bf269d2eaae6c220978e302c1504434e0dd06e`

Do NOT restart RCIR from scratch.

The Dual-Plane architecture introduced in v8.1/v8.2 is directionally correct.

The current problems are concentrated in:

1. canonical entity identity,
2. graph normalization,
3. typed dependency extraction,
4. type-flow/data-flow analysis,
5. ranker selection methodology,
6. benchmark leakage,
7. context-budget optimization,
8. ground-truth quality,
9. real agent execution validation.

The objective of this iteration is **RCIR v8.3**.

---

# ABSOLUTE RULE 0 — THE PIPELINE MUST NOT SEE THE ANSWER KEY

The benchmark ground truth must NEVER be passed to:

```text
CandidateGenerator
TraversalPolicy
EvidenceVectorBuilder
DeterministicRanker
ContextCompiler
ImpactSummarizer
ContextProvider
Agent prompt
TaskRiskRouter
```

Ground truth may be consumed ONLY by:

```text
evaluation code
metric calculation
gate evaluation
error analysis after retrieval completes
```

Add an automated leakage guard.

If any production retrieval/context function accepts:

```text
ground_truth
critical_ground_truth
relevance_labels
expected_files
expected_edges
```

or equivalent benchmark labels:

the benchmark must fail immediately.

---

# PHASE 0 — FREEZE CURRENT HEAD

Freeze:

`07bf269d2eaae6c220978e302c1504434e0dd06e`

as:

`RCIR_V8_2_BASELINE`

Create:

```text
experiments/rcir_v8_3/
    contract/
    datasets/
    ground_truth/
    manifests/
    results/
    reports/
    scripts/
    validation/
    artifacts/
```

Never overwrite v8, v8.1, or v8.2 artifacts.

---

# PHASE 1 — CREATE AN IMMUTABLE RUN MANIFEST

Every formal benchmark execution must generate:

```text
benchmark_run_manifest.json
```

Required fields:

```json
{
  "run_id": "...",
  "polyflow_commit": "...",
  "target_repository": "...",
  "target_repository_commit": "...",
  "benchmark_contract_hash": "...",
  "dataset_hash": "...",
  "ground_truth_hash": "...",
  "graph_hash": "...",
  "candidate_config_hash": "...",
  "ranker_config_hash": "...",
  "compiler_config_hash": "...",
  "provider": null,
  "model": null,
  "tokenizer": null,
  "environment": {},
  "generated_at": "..."
}
```

Every raw artifact must contain:

```text
run_id
```

Reports may only combine artifacts with identical run IDs and compatible configuration fingerprints.

---

# PHASE 2 — REMOVE THE CURRENT GROUND-TRUTH LEAKAGE

Current v8.2 primary execution effectively does:

```python
crit_set = {
    f for f, grade in ground_truth.items()
    if grade >= 2
}

ImpactSummarizer.summarize(
    ...,
    critical_ground_truth=crit_set
)
```

This is prohibited.

Remove:

```text
critical_ground_truth
```

from `ImpactSummarizer`.

The summarizer must infer importance exclusively from RCIR evidence.

Allowed inputs:

```text
candidate structural evidence
edge resolution
edge type
hop
module
fanout
type compatibility
boundary relation
test relation
historical evidence if genuinely available
```

Ground-truth labels must remain invisible.

---

# PHASE 3 — ADD AUTOMATED LEAKAGE DETECTION

Create:

```text
scripts/audit_ground_truth_leakage.py
```

It should statically inspect production benchmark paths for imports or references to:

```text
ground_truth
graded_ground_truth
expected_files
critical_ground_truth
relevance
gold
oracle
```

where inappropriate.

Also add runtime dependency injection tests.

Example:

run retrieval twice with:

```text
ground_truth A
randomly permuted ground_truth B
```

The RCIR output must be byte-identical.

The ground truth should not even be available to retrieval code in normal architecture.

---

# PHASE 4 — REDESIGN CHANGE SPECIFICATION TARGET IDENTITY

Current design mixes:

```text
target symbol
target file
```

inside a single `target_entities` list.

Replace this.

Define:

```python
ChangeSpecification:
    operation
    requested_symbol
    target_file_hint
    canonical_target_ids
    changed_facets
    requested_scope
    language
    risk_hints
    description
```

Example:

```json
{
  "requested_symbol": "getId",
  "target_file_hint": "lib/public/Files/Node.php",
  "canonical_target_ids": [
    "php://OCP\\Files\\Node::getId"
  ]
}
```

The file path is a disambiguation hint.

It is NOT itself a semantic target entity.

---

# PHASE 5 — INTRODUCE CANONICAL ENTITY IDs

Create a language-independent canonical identity layer.

Example forms:

```text
php://OCP\Files\Node
php://OCP\Files\Node::getId

ts://apps/files/src/services/Recent::getRecentSearch

java://com.foo.Bar#doWork(String)

python://package.module:Class.method
```

Required canonical fields:

```text
repository
language
file
namespace/package
owner type
symbol
kind
signature
source span
```

Do not use arbitrary combinations such as:

```text
file.php::FQN\Class::method
```

as both display name and lookup key.

Maintain compatibility aliases separately.

---

# PHASE 6 — BUILD A CANONICAL ALIAS INDEX

Implement:

```text
CanonicalEntityRegistry
AliasIndex
```

Aliases may include:

```text
simple symbol
fully qualified symbol
file path
namespace alias
import alias
class::method
framework route alias
generated-client alias
```

Example:

```text
getId
Node::getId
OCP\Files\Node::getId
lib/public/Files/Node.php::getId
```

should all resolve to one canonical target where context permits.

Resolution output:

```json
{
  "canonical_id": "...",
  "resolution": "exact|unique_alias|ambiguous|unresolved",
  "evidence": [],
  "alternatives": []
}
```

---

# PHASE 7 — DO NOT MARK EVERY ENTITY IN THE TARGET FILE AS EXACT

Current candidate generation seeds every entity found in the target file.

Stop this.

If the task says:

```text
Node::getId
```

the exact target is:

```text
Node::getId
```

not:

```text
Node::move
Node::delete
Node::copy
Node::getSize
Node::getName
...
```

Other members of the same type may be supporting context but cannot receive:

```text
entity_match = exact
```

unless they are actual target aliases.

---

# PHASE 8 — FIX EXACT FILE LOOKUP

Remove substring matching such as:

```python
if target_clean in npath
```

for exact lookup.

Use:

```text
normalized exact path
canonical aliases
```

Substring matching belongs only in lexical retrieval.

It may never produce exact identity evidence.

---

# PHASE 9 — REBUILD GRAPH ENDPOINT NORMALIZATION

The current benchmark reports:

```text
TASK-4 IConfig degree = 0
```

while hundreds of IConfig consumers are simultaneously considered affected.

This is evidence of graph-key normalization failure.

Implement:

```text
CanonicalGraph
```

All edge endpoints must be canonicalized at graph construction time.

Every edge:

```json
{
  "source_id": "canonical entity",
  "target_id": "canonical entity or unresolved external",
  "edge_type": "...",
  "resolution_class": "...",
  "source_span": {},
  "target_span": {},
  "evidence": {}
}
```

No traversal algorithm should have to guess which string representation of an entity was used.

---

# PHASE 10 — REBUILD GRAPH DEGREE ANALYSIS ON CANONICAL IDS

`GraphDegreeAnalyzer` must execute after canonical target resolution.

Calculate:

```text
incoming exact degree
incoming inferred degree
outgoing exact degree
outgoing inferred degree
boundary degree
verification degree
```

Then operation-specific relevant degree.

Record:

```json
{
  "target_id": "...",
  "incoming_exact": 0,
  "incoming_inferred": 0,
  "outgoing_exact": 0,
  "outgoing_inferred": 0,
  "policy_relevant_degree": 0,
  "fanout_mode": "..."
}
```

Add an invariant:

if Impact Plane subsequently discovers hundreds of direct consumers while the recorded direct graph degree is zero:

```text
BENCHMARK FAILURE — GRAPH IDENTITY INCONSISTENCY
```

---

# PHASE 11 — REBUILD CANDIDATE GENERATION AROUND CANONICAL TARGETS

New flow:

```text
ChangeSpecification
        ↓
TargetResolver
        ↓
canonical target IDs
        ↓
direct graph relationships
        ↓
boundary relations
        ↓
verification relations
        ↓
operation-compatible indirect expansion
        ↓
lexical fallback
```

Do not start with broad target-file seeding.

Candidate source labels:

```text
TARGET
DIRECT_EXACT
DIRECT_INFERRED
BOUNDARY_EXACT
BOUNDARY_INFERRED
VERIFICATION_EXACT
TYPE_FLOW
INDIRECT_GRAPH
LEXICAL
UNRESOLVED
```

---

# PHASE 12 — CREATE AN UNRESOLVED LEDGER

Current artifacts frequently report:

```text
known_unresolved = 0
unsupported = 0
```

even though many relationships are clearly not resolved.

Zero and unknown are not the same thing.

Introduce:

```text
ResolutionLedger
```

with:

```text
resolved_exact
resolved_inferred
ambiguous
dynamic_unresolved
unsupported
not_analyzed
```

If a detector did not run:

```text
NOT_ANALYZED
```

not zero.

---

# PHASE 13 — FIX TYPED EDGE EXTRACTION BEFORE FURTHER RANKER TUNING

Current typed edge recall is approximately:

```text
40%
```

and major edge classes are absent or misclassified.

Current failures include:

```text
implements
injects
calls
frontend_to_route
event_dispatch
event_listener
config_reads
source_to_test
```

Fix extraction category by category.

Do NOT compensate for missing graph semantics using ranker weights.

---

# PHASE 14 — FIX `implements`

Current graph sometimes represents expected `implements` relationships as `inherits`.

Separate:

```text
class extends class
interface extends interface
class implements interface
```

Preserve exact relation type.

Add PHP regression fixtures.

---

# PHASE 15 — FIX DEPENDENCY INJECTION EDGES

Do not represent:

```text
constructor parameter of type IConfig
```

only as:

```text
imports
```

Emit:

```text
injects
```

when deterministic DI evidence exists.

Keep the import edge separately if appropriate.

Evidence:

```text
constructor parameter
typed property
service registration
container binding
```

---

# PHASE 16 — IMPLEMENT METHOD-LEVEL CALL EDGES

Improve:

```text
calls
```

so method call relationships preserve:

```text
caller EntityID
callee candidate EntityID
receiver expression
call line
resolution class
type evidence
```

Example:

```json
{
  "source": "php://OCA\\Files\\Controller\\ApiController::getThumbnail",
  "target": "php://OC\\Preview\\Generator::getPreview",
  "edge_type": "calls",
  "call_line": 145,
  "resolution_class": "static_exact"
}
```

---

# PHASE 17 — BUILD EVENT SEMANTICS

Add real extractors for:

```text
event_dispatch
event_listener
event_payload
```

Identify:

```text
dispatcher->dispatch(new Event(...))
dispatcher->dispatchTyped(...)
listener registration
event subscriber maps
framework registration
```

Nextcloud-specific conventions belong in:

```text
NextcloudAdapter
```

not generic graph core.

---

# PHASE 18 — BUILD FRONTEND/BACKEND CONTRACT EDGES

Implement:

```text
frontend_to_route
```

from real evidence:

```text
URL construction
generateUrl / generateOcsUrl
HTTP method
route name
endpoint path
controller route declaration
```

Record ambiguity rather than guessing.

This is required to recover the current Recent.ts cross-stack weakness.

---

# PHASE 19 — BUILD CONFIGURATION SEMANTICS

Differentiate:

```text
config_reads
config_writes
injects_config
container_resolves
service_registers
```

Do not treat every occurrence of `"config"` as semantic evidence.

---

# PHASE 20 — BUILD EXPLICIT SOURCE-TO-TEST EDGES

Possible evidence:

```text
test imports target
test instantiates target
test invokes target method
test extends target-specific base test
historical test/production co-change
framework test mapping
```

Emit:

```text
source_to_test
```

with resolution class.

Do not derive exact verification edges merely because a filename contains `Test`.

---

# PHASE 21 — REPLACE CURRENT TYPEFLOWINDEX WITH SOURCE-DERIVED TYPE FLOW

Current TypeFlowIndex relies mostly on graph strings.

Build:

```text
PHPTypeFlowAnalyzer
```

over actual source syntax.

Extract:

```text
parameter type hints
nullable types
union types
intersection types
return types
typed properties
constructor promotion
PHPDoc @param
PHPDoc @return
PHPDoc @var
new expressions
assignments
property assignments
method return propagation
foreach element types
factory return flows
interface implementations
inheritance
event payload types
container resolutions
```

---

# PHASE 22 — USE REAL RECEIVER EXPRESSIONS

Never simulate:

```text
$entity
$this
$this->node
```

based on filename or graph-string heuristics.

For every method invocation parse the actual receiver expression from source.

Example:

```text
$node->getId()
$this->node->getId()
$event->getNode()->getId()
$this->rootFolder->get($path)->getId()
```

Represent expression trees.

---

# PHASE 23 — ADD LOCAL DATAFLOW

Within each function/method perform deterministic forward propagation.

Example:

```php
$node = $this->rootFolder->get($path);
$id = $node->getId();
```

If `RootFolder::get()` returns Node:

```text
$node → Node
```

then:

```text
$node->getId()
```

can resolve accordingly.

Support:

```text
direct assignment
constructor assignment
property assignment
typed parameter
typed return
simple factory method
foreach element
null coalescing where resolvable
```

Unknown flows remain unknown.

---

# PHASE 24 — ADD INTERPROCEDURAL RETURN PROPAGATION

If:

```text
foo() returns NodeInterface
```

and:

```text
$node = foo()
$node->getId()
```

propagate:

```text
NodeInterface
```

through the call.

Bound analysis depth to avoid explosion.

Record provenance for each inference.

---

# PHASE 25 — MODEL COLLECTION ELEMENT TYPES

Support:

```text
Node[]
array<Node>
iterable<Node>
list<Node>
Traversable<Node>
PHPDoc generic collections
```

This matters for loops such as:

```php
foreach ($nodes as $node) {
    $node->getId();
}
```

---

# PHASE 26 — MODEL EVENT PAYLOAD FLOW

For event listeners:

```text
Event → getNode() → Node
Event → getEntity() → entity type
```

Framework-specific mappings may live in adapters.

This should address several current TASK-2 misses.

---

# PHASE 27 — FIX TYPEFLOW ENTITY-ID PARSING

Do not parse:

```text
file.php::FQN\Class::method
```

by taking:

```python
parts[0]
parts[1]
```

Canonical EntityIDs make this unnecessary.

TypeFlow must operate on structured identity fields rather than string position assumptions.

---

# PHASE 28 — BUILD A REAL TYPE-FLOW BENCHMARK

Discard the current benchmark definition as formal accuracy evidence.

Do not simulate receiver expressions.

Construct a frozen set of real call sites.

For each call site record:

```json
{
  "file": "...",
  "method": "...",
  "line": 0,
  "source_expression": "$node->getId()",
  "receiver_expression": "$node",
  "expected_receiver_type": "...",
  "expected_method_owner": "...",
  "adjudication": "...",
  "evidence": []
}
```

Establish expected receiver type independently through:

```text
source inspection
type annotation
known interface
historical/compiler evidence
manual adjudication
```

Measure:

```text
exact resolution accuracy
ambiguous rate
unknown rate
wrong-owner rate
coverage
precision on resolved cases
```

Do not call:

```text
resolved / all calls
```

“accuracy” unless unresolved and wrong cases are defined appropriately.

---

# PHASE 29 — FOCUS TYPE-FLOW RESEARCH ON `getId()`

Create receiver-ground-truth samples covering:

```text
Node::getId
User::getId
Group::getId
Share::getId
App::getId
Session-like getId
other getId owners
```

The goal is not simply to resolve more calls.

The goal is:

```text
high precision among resolved calls
+
useful coverage
```

Wrong exact resolution is more damaging than explicit ambiguity.

---

# PHASE 30 — FIX THE SILENT-MISS CATALOG

Current v8.2 `silent_miss_catalog.json` is based on v8.1 output and contains 20 misses, while v8.2 currently reports 21.

This is stale.

Generate the miss catalog directly from the CURRENT run's:

```text
impact_plane.json
```

after metrics are finalized.

Each miss must reference:

```text
run_id
task_id
ground_truth item
candidate generator state
graph evidence
classification
root cause
```

No hand-maintained counts.

---

# PHASE 31 — DO NOT PRE-LABEL ROOT CAUSE WITHOUT EVIDENCE

Root-cause classification should be established by diagnostics.

For each miss inspect:

```text
Was canonical target resolved?
Was correct edge in graph?
Was endpoint canonicalized?
Did traversal policy allow the edge?
Was candidate generated?
Was it removed by contradiction pruning?
```

Then classify.

Do not assume:

```text
TYPE_FLOW_MISS
```

just because a generic method is involved.

---

# PHASE 32 — REBUILD GROUND TRUTH INDEPENDENTLY

Current v8.2 ground truth inherits the old v8.1 file list and assigns new verification labels using path rules.

That is not independent adjudication.

Do not generate:

```text
verified = true
```

because the filename contains:

```text
Test
Provider
Listener
Node
IConfig
```

---

# PHASE 33 — GROUND-TRUTH RECORD SCHEMA

Every file-level relevance judgment:

```json
{
  "task_id": "...",
  "file": "...",
  "tier": 0,
  "reason": "...",
  "evidence": [],
  "adjudicator": "historical_patch|static_analysis|manual_review|test_evidence",
  "verified": true
}
```

If not actually reviewed:

```text
verified = false
```

---

# PHASE 34 — USE HISTORICAL PATCHES AS PRIMARY EVIDENCE WHERE AVAILABLE

Find real historical commits representing:

```text
interface change
route change
event evolution
config contract change
schema change
permission change
cross-service contract change
```

Use:

```text
files changed in patch
tests changed
compilation/test failures
source consumers
```

to construct ground truth.

Do not treat grep results as authoritative truth.

Legacy grep ground truth may remain only as:

```text
LEGACY_HEURISTIC_REFERENCE
```

---

# PHASE 35 — VERIFY EVERY NEW DATASET TASK EXISTS

Before freezing DEV/VALIDATION/TEST:

for every task verify:

```text
target file exists
target symbol exists
operation is meaningful
ground truth exists
source evidence exists
```

If a proposed target such as:

```text
TraceExporter
```

does not exist in the frozen Nextcloud revision:

replace it BEFORE freezing the benchmark.

Do not keep synthetic-looking tasks merely because they make the dataset table attractive.

---

# PHASE 36 — ACTUALLY USE DEV / VALIDATION / TEST

The current files:

```text
dev.json
validation.json
test.json
```

must control execution.

Remove primary benchmark dependence on:

```python
from experiments.rcir_v8.scripts.run_baseline import TASKS
```

for v8.3 evaluation.

Create:

```text
DatasetLoader
```

---

# PHASE 37 — DEV PHASE

Only DEV can be used for:

```text
feature development
ranker weight tuning
operation-profile tuning
context quota tuning
type-flow heuristics
```

Store all tuning history.

---

# PHASE 38 — VALIDATION PHASE

Use VALIDATION for:

```text
ranker selection
architecture selection
context planner selection
threshold selection where contract permits
```

No TEST data is visible.

---

# PHASE 39 — TEST PHASE

Once configuration is frozen:

```text
selected_ranker_config.json
selected_context_config.json
selected_typeflow_config.json
```

run TEST exactly once for the formal report.

If test performance is poor:

report poor performance.

Do not retune and rerun under the same version.

Any retuning creates:

```text
v8.3.1
```

or another explicitly new experimental version.

---

# PHASE 40 — ADD DATASET LEAKAGE GUARDS

During ranker selection:

attempting to open:

```text
datasets/test.json
ground_truth/test_*
```

must fail.

Add a unit/integration test proving this.

---

# PHASE 41 — FIX RANKER SELECTION

Delete:

```python
best_config_name = "Cascaded_Operation_Profiles"
```

Ranker selection must be computed.

Input:

```text
VALIDATION metrics only
```

Output:

```text
selected_ranker_config.json
```

with:

```json
{
  "selected_configuration": "...",
  "selection_objective": "...",
  "validation_metrics": {},
  "candidate_configurations": {},
  "selected_at": "...",
  "test_metrics_visible": false
}
```

---

# PHASE 42 — CORRECT THE CURRENT FALSE RANKER RATIONALE

Current evidence shows roughly:

```text
R0:
P@20   46.0%
P@50   36.4%
nDCG   0.5487
MRR    0.5133

Cascaded Operation:
P@20   33.0%
P@50   30.4%
nDCG   0.4731
MRR    0.7167
```

Therefore neither universally dominates.

R0 is stronger for:

```text
precision
graded relevance
```

Cascaded operation ranking is stronger for:

```text
first-hit quality
```

Do not call the cascaded profile “highest nDCG/Precision.”

---

# PHASE 43 — MOVE TO MULTI-OBJECTIVE RANKING

The Context Plane needs at least two objectives:

```text
ANCHOR QUALITY
    find the most critical first items

COVERAGE QUALITY
    cover diverse MUST_CHANGE / MUST_INSPECT dependencies
```

Experiment with:

```text
AnchorRanker
CoverageRanker
```

and fuse them.

Possible approach:

```text
reciprocal rank fusion
semantic interleaving
quota-based merge
```

Do not use learned black-box ranking yet.

Keep everything deterministic and auditable.

---

# PHASE 44 — OPERATION-SPECIFIC BUCKET ORDER

Current cascaded order is globally fixed:

```text
A0 > A1 > A2 > A3 > A4 > A5 > A6 > A7
```

That defeats part of operation conditioning.

Implement operation-specific ordering.

Example:

```text
SIGNATURE_CHANGE
A0 target
A2 implementation/override
A1 direct exact
A4 tests
A5 inferred
A6 indirect
A3 unrelated boundaries
A7 lexical
```

For route changes:

```text
ROUTE_CHANGE
A0 target
A3 route/boundary
A1 exact callers
A4 tests
A5 inferred
A2 type relations
A6
A7
```

For events:

```text
EVENT_CHANGE
A0
event dispatch/listener bucket
direct exact
tests
type relations
inferred
indirect
lexical
```

Do not merely change weights inside an immutable global bucket order.

---

# PHASE 45 — SPLIT BOUNDARY BUCKETS

Do not merge:

```text
route
event
service boundary
generated-client
queue
```

into one generic boundary class.

Use explicit semantic buckets.

---

# PHASE 46 — FIX MODULE DIVERSITY

Current diversity derives module using approximately:

```text
file_path.split("/")[0]
```

which makes:

```text
apps/files
apps/dav
apps/files_sharing
```

all the same `"apps"` module.

Use:

```text
ModuleResolver
```

and repository adapter metadata.

---

# PHASE 47 — DISABLE DECORATIVE FEATURES

The selected config currently enables features such as:

```text
historical
hub penalty
```

even when corresponding evidence is not populated.

Before enabling a feature calculate:

```text
feature_population_coverage
nonzero_count
unknown_count
```

If coverage is zero:

```text
feature_enabled = false
status = NOT_MEASURED
```

Do not give a score weight to a signal that doesn't exist.

---

# PHASE 48 — ADD FEATURE COVERAGE ARTIFACT

Generate:

```text
feature_coverage.json
```

Example:

```json
{
  "type_compatibility": {
    "known_fraction": 0.0
  },
  "historical_cochange": {
    "known_fraction": 0.0
  },
  "hub_degree": {
    "known_fraction": 0.0
  }
}
```

Ranker reports must reference this.

---

# PHASE 49 — BUILD A REAL CONTEXT PLANNER

Do not simply consume global ranking until 4,000 tokens are exhausted.

Introduce:

```text
ContextPlanner
```

Input:

```text
ChangeSpecification
ranked evidence
ImpactSummary
token budget
```

Output:

```text
ContextPlan
```

---

# PHASE 50 — SEMANTIC CONTEXT ROLES

Use roles such as:

```text
TARGET
DIRECT_CALLER
IMPLEMENTATION
BOUNDARY
TEST
CONFIG_SCHEMA
INDIRECT_SUPPORT
IMPACT_SUMMARY
```

The plan allocates budget between roles.

---

# PHASE 51 — EXPERIMENTAL CONTEXT QUOTAS

Evaluate deterministic quota variants on DEV.

Example only:

```text
TARGET             20%
DIRECT STRUCTURAL  25%
CALLERS            15%
TESTS              15%
BOUNDARY/SCHEMA    10%
SUPPORTING          5%
IMPACT SUMMARY     10%
```

Do not freeze these values until validation.

---

# PHASE 52 — OPTIMIZE FOR CRITICAL RECALL @ BUDGET

Current:

```text
CriticalRecall@4k ≈ 33.88%
```

with extreme weaknesses such as:

```text
TASK-2 ≈ 8.33%
TASK-4 ≈ 2.34%
```

This is now the primary Context Plane problem.

Ranker selection alone is insufficient.

Context Planner validation must optimize:

```text
CriticalRecall@Budget
nDCG@Budget
ContextPrecision
token density
```

---

# PHASE 53 — HANDLE HIGH-FANOUT TASKS DIFFERENTLY

A target such as IConfig cannot have hundreds of consumers represented literally in 4k tokens.

Use:

```text
architectural summary
+
representative structural examples
+
top critical direct consumers
+
iterative retrieval handle
```

The full Impact Plane remains available separately.

---

# PHASE 54 — IMPACT SUMMARY MUST NOT USE GROUND TRUTH

Critical consumers should be identified by structural evidence such as:

```text
direct exact dependency
interface implementation
high-confidence typed caller
service registration
boundary contract
direct test
```

not benchmark tier labels.

---

# PHASE 55 — FIX IMPACT SUMMARY METADATA

Do not hardcode:

```text
unresolved_count = 0
full_manifest_reference = some/path
```

Derive them.

The manifest reference must point to an artifact that actually exists.

---

# PHASE 56 — FIX SOURCE SPAN PROPAGATION

The Context Compiler currently supports:

```text
node metadata
edge call line
```

but primary execution does not pass them.

Extend:

```text
CandidateRecord
EvidenceVector
RankedCandidate
```

to preserve:

```text
node_span
call_spans
definition_span
edge evidence
```

Pass this directly into:

```text
SourceSpanResolver
```

---

# PHASE 57 — PARSER SPANS BEFORE REGEX

Primary formal context extraction hierarchy:

```text
1. exact parser node span
2. exact edge call line
3. adapter-derived span
4. heuristic source scan
5. unresolved
```

Record counts for each category.

---

# PHASE 58 — STOP INJECTING RANDOM FILE HEADS

If no span can be identified:

do NOT return:

```text
lines 1-25
```

as if useful.

Return:

```text
SPAN_UNRESOLVED
```

and either:

```text
include compact metadata only
```

or request later through iterative retrieval.

---

# PHASE 59 — FIX TARGET PINNING

Current logic effectively treats:

```text
rank == 1
```

as pinned.

That is wrong.

Before ranking:

resolve canonical target ID(s).

Then Context Planner MUST reserve them.

A target is pinned because it is explicitly requested, not because the ranker happened to place it first.

---

# PHASE 60 — KEEP TARGET AND SUPPORTING CONTEXT SEPARATE

The target should not compete against supporting candidates for inclusion.

Context construction:

```text
reserve target context
        ↓
remaining token budget
        ↓
plan supporting evidence
```

---

# PHASE 61 — TOKENIZE THE FINAL SERIALIZED PROMPT

Do not add constants such as:

```text
+50 metadata tokens
+25 summary tokens
```

Instead:

1. construct the exact final rendered entry,
2. serialize Markdown/text exactly as the model receives it,
3. tokenize that exact text.

---

# PHASE 62 — USE THE ACTUAL MODEL TOKENIZER

If evaluating:

```text
Qwen2.5-Coder
```

do not call:

```text
cl100k_base
```

an exact tokenizer for that model.

Implement:

```text
HuggingFaceTokenizerCounter
```

or the locally installed tokenizer for the actual model.

Artifact:

```json
{
  "model": "...",
  "tokenizer": "...",
  "token_count_type": "exact"
}
```

If unavailable:

```text
estimated
```

and budget claims must say estimated.

---

# PHASE 63 — REBUILD TOKEN-WEIGHTED METRICS

Use actual entry/prompt tokens.

Report:

```text
relevant tokens
irrelevant tokens
metadata tokens
impact-summary tokens
target tokens
test tokens
boundary tokens
```

Then calculate:

```text
TokenWeightedPrecision
TokenWeightedCriticalRecall
```

---

# PHASE 64 — IMPLEMENT ITERATIVE RCIR CONTEXT PROVIDER

The ContextProvider abstraction now exists.

Implement a concrete:

```text
RCIRContextProvider
```

It must execute:

```text
symbol/query
    ↓
TargetResolver
    ↓
Impact Plane lookup
    ↓
selected ranker
    ↓
Context Planner
    ↓
Context Compiler
    ↓
unseen incremental entries
```

No silent grep fallback.

---

# PHASE 65 — TRACK CONTEXT SESSION STATE

For an agent session record:

```text
entities_seen
spans_seen
files_seen
tokens_already_supplied
impact groups already supplied
```

Repeated context requests should not resend identical source.

---

# PHASE 66 — STRENGTHEN REPORT CONSISTENCY

Current validator only checks a handful of values.

Replace it with:

```text
generate reports from raw artifacts into temp directory
    ↓
byte/hash compare against committed reports
```

If different:

```text
CI FAIL
```

No manual benchmark report editing.

---

# PHASE 67 — ARTIFACT DEPENDENCY VALIDATION

Check that:

```text
silent_miss_catalog.run_id
==
impact_plane.run_id
```

Likewise:

```text
gate evaluation
context report
ranker report
agent report
performance report
```

must all reference compatible artifacts.

Stale v8.1-derived data must fail validation.

---

# PHASE 68 — FIX MACHINE GATE CONTRACT IMPLEMENTATION

The current benchmark contract says Option B requires:

```text
precision improvement over P0 = 0.15
```

but gate code uses a hardcoded different condition.

Remove hardcoded semantic thresholds from evaluator logic.

Read all thresholds from:

```text
benchmark_contract.json
```

---

# PHASE 69 — READ P0 METRICS FROM AN ARTIFACT

Do not default:

```python
p0_precision_50 = 0.052
```

Pass a versioned baseline artifact.

Record its hash.

---

# PHASE 70 — VALIDATE CONFIGURATION FINGERPRINTS BEFORE GATING

Gate evaluation must refuse to combine:

```text
Impact Plane from config A
Context Plane from config B
Agent run from config C
```

unless explicitly allowed and documented.

---

# PHASE 71 — REAL PROVIDER CAPABILITY PROBE

Current agent validation hardcodes:

```text
has_live_endpoint = false
```

even if the daemon responds.

Replace with actual capability probing:

```text
provider endpoint reachable
model listed
tiny deterministic inference succeeds
response provenance available
```

Only then:

```text
LIVE_PROVIDER = true
```

Daemon availability alone is insufficient.

---

# PHASE 72 — IF MODEL CANNOT LOAD

Try a smaller locally available open model only if formally configured.

Record:

```text
requested model
actual model
reason for substitution
model digest
```

Do NOT silently substitute.

Do NOT fabricate a run.

If no live model executes:

```text
AGENT E2E = NOT_MEASURED
```

rather than fake trials with zero activity.

---

# PHASE 73 — BUILD THE REAL AGENT BENCHMARK RUNNER

When a real provider is available:

actually instantiate:

```text
ReActAgentRunner
RepoToolEnvironment
RCIRContextProvider
```

Run the agent.

Do not write hardcoded A/B metric dictionaries.

---

# PHASE 74 — ISOLATED GIT WORKTREES

For every trial:

```text
clean source commit
    ↓
new isolated worktree
    ↓
task setup
    ↓
run A or B
    ↓
collect diff/tests/logs
    ↓
destroy worktree
```

Condition A and B must start from identical repository state.

---

# PHASE 75 — TASK-SPECIFIC FAILING ACCEPTANCE TESTS

Before agent execution:

verify:

```text
acceptance test FAILS
```

After modification:

verify:

```text
same acceptance test PASSES
```

This prevents:

```text
pre-existing tests pass
```

from counting as task success.

---

# PHASE 76 — AGENT SUCCESS CONTRACT

Success requires ALL:

```text
live provider
simulation_fallback=false
tool calls > 0
non-empty intended diff
correct files modified
acceptance test initially failed
acceptance test finally passed
repository verification passed
Gatekeeper APPROVE
```

Otherwise:

```text
success = false
```

---

# PHASE 77 — MULTIPLE REPLICATES

For each formal agent task and condition:

run at least:

```text
3 repetitions
```

if runtime permits.

Report all raw trials.

Do not report only averages.

---

# PHASE 78 — COUNTERBALANCE A/B ORDER

Alternate:

```text
A then B
B then A
```

across tasks/repetitions to reduce ordering/cache effects.

---

# PHASE 79 — TURN-BUDGET EXPERIMENT MUST ACTUALLY RUN AGENTS

Delete placeholder trial generation.

For:

```text
5
10
20
```

or risk-specific budgets:

actually run the same task/model/config.

If no live provider:

```text
NOT_MEASURED
```

---

# PHASE 80 — REAL TOOL TELEMETRY

Record:

```text
turns
tool calls
inspect_file calls
search_code calls
request_context calls
apply_patch calls
run_command calls
files inspected
files modified
context tokens
model tokens
latency
verification attempts
repair cycles
```

---

# PHASE 81 — VERIFY ADAPTIVE ROUTING END TO END

TaskRiskRouter integration now exists.

Add executions proving:

```text
LOCAL_BUG
CROSS_MODULE
ARCHITECTURE_REFACTOR
```

actually result in different:

```text
stages
turn budgets
token usage
```

Do not report theoretical savings.

---

# PHASE 82 — TYPED EDGE EVALUATION

Continue the honest v8.2 policy:

if precision cannot be measured:

```text
NOT_MEASURED
```

Do not fabricate it.

Focus first on typed-edge recall.

Produce category-level metrics.

---

# PHASE 83 — EXPAND TYPED EDGE GROUND TRUTH

Twenty edges is insufficient.

Create a larger manually/independently adjudicated set covering:

```text
imports
calls
constructs
inherits
implements
overrides
injects
route_to_controller
frontend_to_route
event_dispatch
event_listener
config_reads
config_writes
source_to_test
service registration
queue producer/consumer
schema relation
```

Balance across categories.

---

# PHASE 84 — NEGATIVE EDGE DATASET FOR PRECISION

If true precision is desired, create scoped negative examples.

Example:

```text
same method name, wrong owner
same filename, wrong namespace
same route substring, unrelated endpoint
same event suffix, unrelated event
same config symbol, unrelated config service
```

Then evaluate:

```text
false positive rate
precision
specificity
```

within that explicitly defined scope.

---

# PHASE 85 — RE-EVALUATE IMPACT PLANE ONLY AFTER GRAPH FIXES

Current global recall around 97% looks strong, but macro recall is only about 88% and the weakest task is around 67%.

After canonicalization and typed extraction rerun.

Do not blindly broaden retrieval.

The target is:

```text
high macro recall
high worst-task recall
controlled candidate growth
```

---

# PHASE 86 — PARETO REPORT

Compare architectures using:

```text
macro pool recall
worst-task pool recall
candidate pool size
P@20
P@50
nDCG
MRR
CriticalRecall@Budget
token cost
query latency
```

Generate Pareto frontier.

Do not optimize one metric at the expense of everything else without documenting the tradeoff.

---

# PHASE 87 — FEATURE IMPACT REPORT

For every feature:

```text
canonicalization
type flow
boundary graph
test graph
BM25
module diversity
context planning
impact summary
```

report:

```text
metric delta
coverage
cost
failure cases
```

Delete features that consistently degrade performance unless they are necessary for another clearly documented objective.

---

# PHASE 88 — EXTERNAL GENERALIZATION ONLY AFTER INTERNAL METHODOLOGY IS CLEAN

Current generalization report correctly states:

```text
Nextcloud only
```

Keep that status.

After v8.3 methodology is frozen, evaluate externally.

Suggested sequence:

```text
OpenTelemetry Demo
Odoo
Frappe/ERPNext
```

Do not modify core architecture in response to external TEST results under the same version.

---

# PHASE 89 — CI

Add actual GitHub Actions workflows:

```text
.github/workflows/
    rcir-unit.yml
    rcir-artifact-integrity.yml
    rcir-smoke-benchmark.yml
    rcir-full-benchmark.yml
```

Current HEAD has no workflow/status evidence.

---

# PHASE 90 — UNIT CI

Run:

```text
canonical EntityID tests
alias resolver tests
graph endpoint normalization
degree analyzer
traversal
typed edge extractors
type flow
ranker feature gating
context planner
source span resolver
tokenizer
ContextProvider
agent success semantics
gate evaluator
```

---

# PHASE 91 — ARTIFACT INTEGRITY CI

Validate:

```text
JSON schemas
run IDs
configuration hashes
report hashes
ground-truth leakage
stale artifact references
contract/gate consistency
```

---

# PHASE 92 — BENCHMARK SMOKE CI

Use a tiny deterministic fixture repo.

Exercise:

```text
extract
canonicalize
impact
rank
compile context
evaluate
generate report
```

No Nextcloud-scale workload required.

---

# PHASE 93 — MANUAL FULL BENCHMARK

Full Nextcloud benchmark:

```text
workflow_dispatch
```

or equivalent manual trigger.

Store run provenance.

---

# REQUIRED REGRESSION TESTS

At minimum implement tests proving:

```text
target symbol and target file are separate concepts

only actual requested symbol receives exact target identity

same-file sibling methods are not A0 exact targets

substring path matching cannot create exact identity

canonical alias forms resolve to same EntityID

IConfig degree cannot remain zero if canonical incoming edges exist

fanout mode uses canonical graph degree

ground truth cannot reach ImpactSummarizer

ground truth cannot reach ContextPlanner

ground truth cannot reach ranker

silent miss catalog comes from current run ID

implements is not replaced by inherits

constructor injection emits injects

method call preserves call line

event dispatch/listener edges resolve

frontend route edges resolve

source-to-test evidence is typed

TypeFlow parses actual receiver expression

local assignment type propagates

property type propagates

parameter type propagates

factory return propagates

foreach element type propagates

ambiguous getId remains ambiguous

wrong getId owner is never exact

R0 feature set contains only R0 signals

ranker selection is computed, not hardcoded

validation dataset controls selection

test dataset is inaccessible during selection

operation-specific bucket order changes ranking

ModuleResolver controls diversity

disabled feature with zero evidence cannot influence ranking

target canonical EntityID is always pinned

rank 1 alone does not imply pinned

parser span metadata reaches ContextCompiler

unresolved source span never injects arbitrary file head

final rendered prompt is what gets tokenized

model tokenizer provenance is correct

ContextProvider returns incremental unseen context

agent benchmark uses actual ReActAgentRunner

agent A/B uses isolated worktrees

acceptance test fails before patch

acceptance test passes after patch

simulated provider cannot satisfy agent gate

gate evaluator reads thresholds from contract

P0 baseline metrics come from artifact

report regeneration is byte/hash consistent
```

---

# NEW ARCHITECTURE

The intended v8.3 architecture is:

```text
                    CHANGE REQUEST
                          │
                          ▼
                 ChangeSpecification
                          │
                          ▼
                    TargetResolver
                          │
                          ▼
               Canonical Entity ID(s)
                          │
                          ▼
              ┌─────────────────────┐
              │ CANONICAL GRAPH     │
              │                     │
              │ typed edges         │
              │ aliases             │
              │ source spans        │
              │ call sites          │
              │ unresolved ledger   │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   IMPACT PLANE      │
              │                     │
              │ high recall         │
              │ exact/inferred      │
              │ unresolved          │
              │ full audit trail    │
              └──────────┬──────────┘
                         │
                         ▼
                EVIDENCE ENRICHMENT
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Type Flow       Boundaries    Verification
          │              │              │
          └──────────────┼──────────────┘
                         ▼
             ┌──────────────────────┐
             │    CONTEXT PLANE     │
             │                      │
             │ Anchor Ranker        │
             │ Coverage Ranker      │
             │ Operation Profile    │
             └──────────┬───────────┘
                        ▼
                  ContextPlanner
                        │
              semantic token quotas
                        │
                        ▼
                  ContextCompiler
                        │
                exact source spans
                        │
                model tokenizer
                        │
                        ▼
               RCIRContextProvider
                        │
                        ▼
                  Coding Agent
                        │
                        ▼
               inspect / patch / test
                        │
                        ▼
                   Gatekeeper
```

---

# RESEARCH PRIORITY ORDER

Do not work on all components simultaneously.

Priority 1:

```text
remove benchmark leakage
fix dataset split enforcement
fix ranker selection
```

Priority 2:

```text
canonical entity IDs
graph endpoint normalization
target identity
```

Priority 3:

```text
typed edge extraction
real TypeFlow
```

Priority 4:

```text
Context Planner
CriticalRecall@Budget
```

Priority 5:

```text
real agent A/B
```

Priority 6:

```text
external generalization
```

---

# v8.3 PRIMARY HYPOTHESES

## H1 — Canonical Identity

Canonical graph normalization will remove contradictory behavior such as:

```text
hundreds of IConfig consumers
but graph degree = 0
```

Expected effect:

```text
higher macro impact recall
lower arbitrary candidate expansion
```

---

## H2 — Real Type Flow

Source-derived receiver type propagation will improve generic-method resolution relative to both:

```text
string heuristic
current v8.2 TypeFlowIndex
```

without increasing false exact resolutions.

---

## H3 — Multi-Objective Context Planning

Separating:

```text
anchor relevance
coverage relevance
```

and compiling by semantic role will improve:

```text
CriticalRecall@Budget
```

substantially beyond the current ~34%.

---

## H4 — Operation-Specific Cascade

Allowing operation-dependent semantic bucket order will preserve the cascaded ranker's MRR advantage while recovering part of R0's superior:

```text
P@20
P@50
nDCG
```

---

## H5 — RCIR Agent Utility

Under a real provider and real acceptance tests:

RCIR context will reduce repository exploration and/or increase verified task completion relative to an identical agent without RCIR.

This remains unproven until real runs occur.

---

# FROZEN RESEARCH TARGETS

Treat these as targets, not achieved facts.

## Impact Plane

Aim for:

```text
Global CandidatePoolRecall >= 95%
Macro CandidatePoolRecall >= 95%
Worst Task Recall >= 90%
Silent Misses <= frozen contract threshold
```

---

## Context Plane

Aim for:

```text
Precision@20 >= 35%
Precision@50 >= 20%
nDCG@50 >= 0.50
MRR >= 0.70
CriticalRecall@Budget >= 60%
```

The exact SELECTED pipeline must satisfy them.

Not an unused ablation.

---

# ADDITIONAL CONTEXT TARGET

Because current CriticalRecall@Budget is the main bottleneck, also report:

```text
CriticalRecall@2k
CriticalRecall@4k
CriticalRecall@8k
```

This produces a context-efficiency curve.

Do not optimize only one arbitrary budget.

---

# EDGE INTELLIGENCE TARGET

Do not freeze an artificial precision target yet.

First:

```text
increase typed edge recall across all supported categories
```

and establish a legitimate precision methodology.

---

# TYPE-FLOW TARGET

Report separately:

```text
coverage
precision among resolved receivers
wrong-exact rate
ambiguity rate
unknown rate
```

A reasonable system should prefer:

```text
UNKNOWN
```

over an incorrect exact receiver.

---

# AGENT TARGET

No target is valid until a live provider executes.

When live:

evaluate:

```text
verified completion rate
turns
tool calls
search calls
context requests
tokens
latency
repair cycles
```

---

# STOP CONDITIONS

Stop and classify the run if any of these occur:

```text
ground truth enters retrieval pipeline
test set used during selection
selected ranker hardcoded
report differs from raw JSON
run IDs mismatch
configuration hashes mismatch
provider simulation occurs in formal agent benchmark
target dataset file does not exist
ground truth is generated from RCIR output itself
```

These are benchmark-invalidating conditions, not warnings.

---

# FINAL DECISION ENGINE

The final report must come exclusively from:

```text
gate_evaluation.json
```

Possible results:

```text
OPTION A — VALIDATED
OPTION B — PARTIALLY VALIDATED
OPTION C — REJECTED
```

No human override.

No prose reinterpretation.

No substitute ablation metrics.

No validation on a configuration different from the one executed in the primary pipeline.

---

# REQUIRED FINAL ARTIFACTS

Produce at minimum:

```text
results/
    canonicalization_evaluation.json
    impact_plane.json
    silent_miss_catalog.json
    edge_recall_evaluation.json
    type_flow_evaluation.json
    feature_coverage.json
    ranker_dev.json
    ranker_validation.json
    selected_ranker_config.json
    context_plan_evaluation.json
    context_plane.json
    context_budget_curve.json
    agent_turn_budget.json
    agent_ab_runs.json
    performance_benchmark.json
    external_generalization.json
    gate_evaluation.json
```

Reports:

```text
reports/
    v8_2_reassessment.md
    canonical_graph_report.md
    impact_plane_report.md
    typed_edge_report.md
    type_flow_report.md
    ranking_report.md
    context_planner_report.md
    context_budget_report.md
    agent_validation_report.md
    generalization_report.md
    failure_catalog.md
    final_assessment.md
    reproduction.md
```

---

# FINAL ENGINEERING PRINCIPLE

RCIR should not be optimized as:

> “return fewer files.”

It should be optimized as three connected but separate systems.

### Impact Plane

> Determine everything that could realistically be affected, with explicit uncertainty.

### Context Plane

> Select the smallest high-information representation of that impact necessary for the current engineering decision.

### Execution Plane

> Demonstrate that the context materially helps a real coding agent produce and verify the correct modification.

The current v8.2 implementation has made the first plane reasonably promising and has finally made the evidence pipeline honest.

The next bottleneck is no longer cosmetic benchmark cleanup.

It is **semantic correctness**:

```text
canonical identity
typed relationships
receiver resolution
critical context selection
```

Fix those before adding additional ranking features.

Begin with Phase 0 and preserve every negative result.