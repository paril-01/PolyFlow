# RCIR v8 — Evidence-Guided Repository Intelligence Redesign

You are operating as a principal software architecture researcher and senior repository-analysis engineer inside the PolyFlow repository.

Your task is **not** to make RCIR look successful.

Your task is to determine, through reproducible experiments, whether RCIR can be redesigned to achieve substantially better useful dependency retrieval and downstream coding-agent performance.

The current repository HEAD to use as the frozen baseline is:

`226cfc6b3b8663f98dd97f0327529f765ac36284`

Do not overwrite or reinterpret existing benchmark evidence.

---

# ABSOLUTE RULE 0 — NO FABRICATED SUCCESS

Never fabricate:

- benchmark results
- repository files
- dependencies
- graph edges
- ground truth
- token counts
- timing
- memory
- compiler output
- tests
- agent edits
- Git diffs
- LLM telemetry
- historical PR relationships
- precision
- recall
- model provenance
- CI status

If something is unavailable, write:

`NOT MEASURED`

`UNSUPPORTED`

or

`BLOCKED`

as appropriate.

Do not change an evaluator so that it agrees with RCIR output.

Do not hardcode expected benchmark answers into RCIR.

Do not convert a failed experiment into a success through wording.

Negative results are valid.

---

# PRIMARY OBJECTIVE

The current two-hop candidate expansion achieves high candidate coverage but extremely poor precision.

The objective of RCIR v8 is:

> Preserve high dependency/candidate coverage while radically reducing irrelevant context, making the resulting context useful to real coding agents.

The optimization objective is NOT:

`maximize recall`

in isolation.

The objective is:

```text
high coverage
+ useful ranking
+ bounded context
+ explicit uncertainty
+ correct downstream engineering changes
```

---

# CURRENT BASELINE TO PRESERVE

Record the current benchmark before changing anything.

Current reported Nextcloud candidate-expansion behavior includes approximately:

- candidate-file recall: 96.7%
- macro candidate precision: 5.6%
- 7,988 candidates
- 7,276 false-positive candidates
- 10 remaining candidate misses

Current direct/1-hop mode is materially more precise but substantially lower coverage.

These numbers are baseline observations only.

Recompute them from the committed raw artifacts before using them.

Do not copy these values into new output without validating them.

---

# PHASE 0 — FREEZE THE BASELINE

Create:

```text
experiments/rcir_v8/
  baseline/
  datasets/
  ground_truth/
  policies/
  results/
  reports/
  scripts/
```

Store:

- PolyFlow commit SHA
- target repository SHA
- benchmark task definitions
- environment
- Python version
- relevant toolchain versions
- baseline raw outputs
- exact commands
- random seeds where applicable

Do not modify the frozen baseline.

---

# PHASE 1 — AUDIT CURRENT RETRIEVAL ARCHITECTURE

Inspect at minimum:

```text
rcir/src/rcir/retrieval/hybrid.py
rcir/src/rcir/retrieval/scorer.py
rcir/src/rcir/impact.py
rcir/src/rcir/graph/
rcir/src/rcir/hierarchy/
rcir/src/rcir/contract/
experiments/nextcloud_validation/scripts/agent_harness.py
orchestrator/agent_loop.py
orchestrator/tools.py
orchestrator/runner.py
```

Document:

1. lexical retrieval
2. symbol matching
3. graph expansion
4. edge direction handling
5. hop handling
6. confidence/resolution handling
7. candidate merging
8. ranking
9. token budgeting
10. ground-truth methodology

Produce:

`experiments/rcir_v8/reports/current_architecture.md`

Do not implement v8 until this audit exists.

---

# PHASE 2 — CORRECT THE EVALUATION CONTRACT FIRST

Implement ranked retrieval evaluation.

Required metrics:

```text
Recall@5
Recall@10
Recall@20
Recall@50
Precision@5
Precision@10
Precision@20
Precision@50
MRR
nDCG
candidate_count
token_budgeted_coverage
silent_misses
known_unresolved
unsupported
latency_ms
peak_memory_mb
```

Report both:

- macro averages
- micro/global aggregates

Never call file-level retrieval an edge metric.

---

# PHASE 3 — CREATE TRUE EDGE-LEVEL GROUND TRUTH

Add explicit relation ground truth where possible.

Schema:

```json
{
  "source": {
    "entity_id": "...",
    "file": "...",
    "line": 0
  },
  "relationship": "calls",
  "target": {
    "entity_id": "...",
    "file": "...",
    "line": 0
  },
  "evidence_source": "manual|compiler|runtime|historical_diff|generated_contract",
  "verified": true
}
```

Edge-level metrics must only use edge-level ground truth.

File-level metrics must stay labelled file-level.

---

# PHASE 4 — IMPLEMENT CHANGE SPECIFICATION

Create a formal change representation.

Suggested module:

```text
rcir/src/rcir/query/
  change_spec.py
  intent_parser.py
```

Suggested structure:

```json
{
  "operation": "rename|signature_change|behavior_change|route_change|schema_change|event_change|config_change|permission_change|service_boundary_change",
  "target_entities": [],
  "changed_facets": [],
  "requested_scope": "local|module|cross_module|repository",
  "language": null,
  "risk_hints": []
}
```

Natural language is converted to `ChangeSpecification`.

The parser must support deterministic/manual construction for benchmarks so LLM interpretation does not contaminate retrieval evaluation.

---

# PHASE 5 — IMPLEMENT STABLE ENTITY IDENTITY

Create a repository-wide entity model.

Suggested:

```text
rcir/src/rcir/entities/
  entity.py
  resolver.py
  registry.py
```

An entity must capture:

```text
repository
language
file
namespace/package
module/service
symbol kind
owner
symbol name
signature fingerprint
```

Do not match generic symbols such as `getId` solely by string occurrence.

Entity ambiguity must be explicit.

---

# PHASE 6 — BUILD MULTI-VIEW GRAPH LAYERS

Do not immediately destroy the existing graph format.

Add views or indexes over it.

Required views:

## Symbol

```text
defines
calls
imports
inherits
implements
overrides
constructs
reads
writes
```

## Boundary

```text
route_to_controller
frontend_to_route
grpc_client_to_rpc
event_to_listener
queue_producer_to_consumer
spec_to_generated_client
```

## State/configuration

```text
config_key
env_var
db_table
db_field
migration
serializer
feature_flag
```

## Verification/build

```text
source_to_test
module_to_build_target
generated_source
integration_test
lint_target
```

## Historical

```text
cochange_file
cochange_symbol
production_test_cochange
```

Historical relationships are auxiliary evidence.

They must never be labelled static-exact dependencies.

---

# PHASE 7 — REPLACE GENERIC BFS WITH TRAVERSAL POLICIES

Implement:

```text
TraversalPolicy
```

The traversal decision must depend on:

```text
change operation
edge type
edge direction
hop distance
resolution class
module boundary
entity compatibility
```

Examples:

## rename

Prefer:

```text
definition
imports
callers
overrides
implementations
tests
```

## signature change

Prefer:

```text
definition
callers
interfaces
implementations
overrides
serializers
generated clients
tests
```

## route change

Prefer:

```text
route declaration
controller
frontend clients
SDK/generated clients
route tests
```

## schema field change

Prefer:

```text
schema
migration
ORM
serializer
API contract
frontend type
validation
tests
```

## event change

Prefer:

```text
publisher
event type
listeners
event registration
tests
```

Do not blindly traverse all relationships in both directions for two hops.

---

# PHASE 8 — BUILD A HIGH-RECALL CANDIDATE GENERATOR

Candidate generation is allowed to over-retrieve.

Sources can include:

```text
exact entity lookup
direct graph edges
policy-controlled graph expansion
BM25/TF-IDF
repository symbol map
historical co-change
boundary graph
build/test graph
```

Candidate generation must be separate from final context selection.

Output:

```json
{
  "entity_id": "...",
  "candidate_sources": [],
  "graph_paths": [],
  "hop_distance": 0
}
```

---

# PHASE 9 — BUILD EVIDENCE VECTORS

Do not expose one fake probability.

For every candidate record:

```json
{
  "entity_match": "...",
  "resolution_class": "...",
  "edge_types": [],
  "type_compatibility": "...",
  "change_type_compatibility": "...",
  "boundary_contract": "...",
  "lexical_score": 0.0,
  "module_distance": 0,
  "hop_distance": 0,
  "historical_cochange": 0.0,
  "test_relationship": "...",
  "runtime_evidence": false,
  "contradictions": []
}
```

A candidate may carry multiple evidence sources.

---

# PHASE 10 — BUILD THE RANKER / PRUNER

Implement a deterministic ranker first.

Do not begin with machine learning.

Suggested experimental features:

```text
exact entity match
static exact edge
typed inferred edge
change-type compatible relationship
receiver/type compatibility
same module/service
boundary contract
test relationship
lexical relevance
historical co-change
hop distance penalty
generic symbol penalty
ambiguous entity penalty
unresolved penalty
hub-degree penalty
```

Hard contradictions should remove candidates.

Examples:

```text
wrong receiver type
wrong namespace
incompatible route
unrelated event type
unrelated config subsystem
```

Keep scoring transparent.

Log every component.

---

# PHASE 11 — RUN ABLATIONS BEFORE BUILDING MORE FEATURES

Run:

## P0

Current 2-hop RCIR.

## P1

Typed directional traversal.

## P2

P1 + change-type policies.

## P3

P2 + stable entity identity/type compatibility.

## P4

P3 + lexical/BM25 reranking.

## P5

P4 + build/test/module evidence.

## P6

P5 + historical co-change.

For every policy produce the same metrics.

Create:

```text
experiments/rcir_v8/results/policy_p0.json
...
experiments/rcir_v8/results/policy_p6.json
```

and:

```text
experiments/rcir_v8/reports/ablation_report.md
```

Do not implement P5/P6 merely because they sound sophisticated.

If P3 beats P4, keep P3.

Prefer the simplest architecture supported by evidence.

---

# PHASE 12 — DEFINE DEVELOPMENT, VALIDATION, AND TEST SETS

Prevent benchmark overfitting.

Create:

```text
datasets/dev.json
datasets/validation.json
datasets/test.json
```

No tuning on test.

Include task categories across:

```text
method/interface
events
configuration
routes
schema/database
frontend/backend
DI
cross-service contracts
generated clients
build/test
```

Use real historical changes where practical.

---

# PHASE 13 — BUILD CONTEXT COMPILER

Candidate ranking and LLM context are different tasks.

Implement:

```text
rcir/src/rcir/context/compiler.py
```

The compiler chooses per entity:

```text
signature
definition
specific line range
caller snippet
interface
route declaration
schema fragment
test fragment
summary
full implementation
```

Each context entry must provide:

```json
{
  "entity_id": "...",
  "rank": 0,
  "reason": "...",
  "evidence": [],
  "granularity": "...",
  "source_file": "...",
  "source_lines": [],
  "estimated_tokens": 0
}
```

Respect a token budget.

Do not dump the candidate set into the LLM.

---

# PHASE 14 — INTRODUCE ITERATIVE RETRIEVAL

The coding agent may request additional context.

Flow:

```text
initial compact context
→ agent reasoning
→ targeted context request
→ RCIR retrieval
→ incremental context
→ edit
```

Track:

```text
context requests
tokens added
files inspected
relevant files retrieved
irrelevant files retrieved
```

---

# PHASE 15 — FIX THE CODING AGENT EDIT LOOP

Implement `apply_patch`.

Do not rely only on exact `old_str/new_str`.

Requirements:

```text
unified diff input
path sandboxing
syntax validation
diff preview
rollback
changed-file tracking
```

Retain old edit tool only as fallback.

---

# PHASE 16 — TEST TURN BUDGETS

Use identical coding tasks.

Run:

```text
5 turns
10 turns
20 turns
```

Use the same model and context.

Record:

```text
success
files modified
tool calls
tokens
tests
duration
diff size
retries
provider errors
```

Do not infer that five-turn failure means RCIR failure.

---

# PHASE 17 — ADAPTIVE AGENT ORCHESTRATION

Preserve existing Maker / Reviewer / Implementer / Gatekeeper / Historian roles.

Do not necessarily invoke every role for every task.

Implement a deterministic task-risk router.

Examples:

```text
small bug:
Retriever → Implementer → Reviewer → Gatekeeper

cross-module:
Maker → Retriever → Implementer → Reviewer → Gatekeeper → Historian

architecture:
Maker → Reviewer → Maker → Implementer → Reviewer → Gatekeeper → Historian
```

Compare token cost and task success against fixed six-stage orchestration.

---

# PHASE 18 — MODEL EXPERIMENT DISCIPLINE

Keep RCIR evaluation separate from model evaluation.

For paired baseline-versus-RCIR experiments use:

```text
same model
same repository
same task
same tools
same turn budget
same test command
same temperature/config
```

Record exact provider/model identifier.

If testing a stronger local model, create a separate experiment.

Do not silently replace historical results generated by another model.

---

# PHASE 19 — SUCCESS GATES

Do not promise these values.

Treat them as experimental milestones.

## Retrieval gate A

Preserve useful high coverage:

```text
Recall@50 >= 90%
```

while substantially reducing current candidate volume.

## Retrieval gate B

First major milestone:

```text
high recall
macro candidate precision >= 20%
```

without increasing silent misses materially.

## Retrieval gate C

Stretch goal:

```text
candidate recall approximately >= 95%
macro precision approximately >= 35%
strong Recall@20 and Recall@50
bounded context near 4k tokens
```

Do not modify gates after seeing frozen test results without documenting the change.

## Static-exact gate

Static-exact relations must be held to much higher precision standards than inferred candidate retrieval.

---

# PHASE 20 — VALID E2E AGENT SUCCESS

An agent task is successful only if:

```text
actual source changed
non-empty git diff exists
required behavior changed
tests executed after the change
acceptance tests pass
no relevant regression discovered
Gatekeeper approves based on evidence
```

Pre-existing passing tests on unchanged code are NOT task success.

---

# PHASE 21 — EXTERNAL VALIDATION LADDER

After Nextcloud v8 stabilizes:

```text
OpenTelemetry Demo
→ Odoo
→ Frappe + ERPNext
→ Kubernetes
```

Do not tune the system independently until it magically performs well on each repository.

Record cross-repository degradation honestly.

---

# PHASE 22 — REPORTS

Create:

```text
experiments/rcir_v8/reports/
  current_architecture.md
  issue_register.md
  benchmark_contract.md
  ablation_report.md
  edge_ground_truth_report.md
  ranking_report.md
  context_efficiency_report.md
  agent_execution_report.md
  failure_catalog.md
  final_assessment.md
  reproduction.md
```

Raw JSON must exist behind every major table.

---

# REQUIRED FAILURE CATALOG

Every failure should contain:

```text
failure_id
repository
commit
task
expected
observed
failure_class
severity
root_cause
silent_miss
known_unresolved
reproducible
fix_attempted
before
after
regression_test
```

---

# STOP CONDITIONS

Stop an experiment when:

1. it is reproducible
2. result is recorded
3. failure is classified
4. raw evidence exists

Do not keep modifying the system until the benchmark becomes positive.

If an architectural idea fails, record the failure and revert it.

---

# WHAT NOT TO DO

Do not:

- optimize only for raw recall
- call file recall edge recall
- hide low precision
- use one homogeneous BFS for every change type
- assign probability meaning to ordinal resolution classes
- train on test tasks
- fake an agent diff
- treat unchanged passing tests as implementation success
- add UI features before benchmark correctness
- rewrite all parsers without evidence
- remove negative benchmark results
- add repository-specific hacks that do not generalize
- hardcode Nextcloud names into RCIR core

---

# FINAL DELIVERABLE

At the end, produce an evidence-backed recommendation:

## Option A — v8 architecture validated

State which components improved results and show ablations.

## Option B — partial validation

State which components helped and which failed.

## Option C — redesign rejected

If v8 does not materially improve useful retrieval or agent performance, state that clearly.

The purpose of the experiment is not to validate the design.

The purpose is to discover whether the design deserves to exist.

Begin with PHASE 0 and proceed sequentially.