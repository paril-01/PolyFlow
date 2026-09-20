# RCIR — Build Plan v3 (Implementation-Ready)
### Dependency-Graph Context Runtime: Scoped, Honest, Buildable, Verifiable

v3 is written to be handed directly to an LLM coding agent (Claude Code, Cursor, etc.) working inside the repo. Every phase in §10 is now a concrete task list with file paths, responsibilities, and a **Definition of Done that requires a real, runnable verification command** — not a description of intended behavior. This exists specifically because the PolyFlow audit earlier in this project found 281 "modules" that were templated scaffolding with no real logic behind them. That failure mode is now a named, standing rule (§0.1) — not a thing to remember informally.

---

## 0. What this document is

A build plan for one scoped system: a lightweight, self-hostable middleware layer that sits between a repository and an LLM/IDE, answers context questions with a token-budgeted, structurally-derived slice of the codebase, keeps that slice cheap to maintain as the code changes, and is benchmarked against real baselines with a real compile/test harness — not retrieval-quality proxies alone.

It is **not** a claim of an unprecedented invention. It is a specific combination and a specific research question, built on named prior art, tested honestly.

### 0.1 Anti-Fabrication Discipline — standing rule, applies to every phase

This rule exists because of a specific, verified finding: sampling PolyFlow's `enterprise-platform-pure/` modules found every `process()` function returning `{"processed": True, "input_keys": [...]}` regardless of domain, and every governance block containing the identical literal `"alternatives_considered": ["rust", "elixir"]` — 281 files of templated scaffolding presented as working features. That is the exact failure this project must not repeat, at any phase, at any scale.

**Rules, non-negotiable:**
1. **No function returns a hardcoded or templated result that would be identical regardless of input.** If a `process_module()`-style function returns the same shape of output for a Flask repo and a Django repo without the content actually differing based on real analysis of each, it's a stub — label it as one explicitly, or don't commit it.
2. **Every phase's Definition of Done requires running a real command against a real, non-trivial input** (a cloned open-source repo, not a 10-line toy file) and reporting actual output — not "this should work" or "implemented as specified."
3. **No test exists solely to make its own stub pass.** A test that asserts `extract_graph(toy_file) == hardcoded_expected_graph` where `toy_file` was constructed *to match* the hardcoded expectation is not a real test — write tests against independently-known ground truth (e.g., "this function calls exactly these 3 functions, verified by reading the source") or against real external repos where the answer isn't chosen to fit the code.
4. **If a component is genuinely not yet implemented, mark it `# TODO: not implemented` and make it fail loudly (raise `NotImplementedError`) — never silently return a plausible-looking fake value.** A loud failure is debuggable; a silent fake success is the exact PolyFlow-module problem.
5. **Before claiming a phase complete, run the verification command in §10 for that phase and paste the actual terminal output into the phase's tracking issue/commit message.** Not a summary of what it should show — the actual output.
6. **Sample your own work the way an external auditor would.** At the end of each phase, pick 2-3 outputs at random (not the ones you tested during development) and manually check they're real. This is literally the check that found the PolyFlow issue — it took under 5 minutes and should be a standing habit, not a one-off.

---

## 1. Problem statement (grounded)

1. **Context cost is a documented 2026 problem, independent of the AI-layoffs debate.** Uber and Microsoft have both depleted AI budgets faster than expected because usage doesn't scale with value ("tokenmaxxing"). Gartner projects AI agent software spend at $207B in 2026, up 139% YoY.
2. **Large, dense repositories make "what context does the LLM need" a real retrieval problem**, independent of any org's budget.

### 1a. What NOT to claim
- Not "AI cost caused 2026 layoffs" — "AI washing" is a documented, named phenomenon this year. Use token-cost inefficiency as evidence, not the layoffs headline.
- Not unprecedented (§2).
- Not a claim of market dominance or individual irreplaceability.

---

## 2. Prior art

| Component | Prior art | What it does |
|---|---|---|
| Hierarchical abstraction levels | **RAPTOR** (2024) + successors | Recursive clustering + summarization; top-down AND collapsed-tree retrieval modes |
| Dense-graph navigation | **HNSW** (2016) | Skip-list + navigable-small-world graph |
| Graph-based context retrieval | **HippoRAG**, Personalized PageRank | Graph-walk retrieval |
| Cross-language canonical code representation | **SCIP/LSIF**, **Kythe**, **Glean** | Compiler-derived semantic indexes |
| Dependency-graph-ranked context selection | **Aider repo-map** | PageRank over call/import graph, token budget |
| Tiered code-context compression, MCP-native | **code-graph-mcp**, **CodeGraph**, **GitNexus** | L0-L3 tiers, incremental Merkle-tree indexing |
| Enterprise context engines | **Augment Code**, **Sourcegraph Cody Enterprise** | VPC/on-prem, SOC2/ISO42001 |
| Air-gapped compliance AI | **AirgapAI**, ibl.ai | On-prem, zero-cloud |

### Research question
> *We investigate whether dependency-derived hierarchical context organization, combined with state-split (interface/behavioral/data-contract) incremental invalidation, can reduce context maintenance and retrieval cost while preserving task-relevant context and end-to-end task success — compared to embedding-cluster hierarchies (RAPTOR) and flat dependency ranking (Aider repo-map).*

---

## 3. System architecture and relationship to existing repos

```
                         Repository
                             │
                             ▼
                  Semantic Representation
                    (AST + symbol table)
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
     Dependency Graph                  Interface/Behavior/
   (call graph + import graph,          Data-Contract State
    confidence-weighted edges)          (per node, §4.3)
              │                              │
              └──────────────┬───────────────┘
                              ▼
                   Hierarchy (derived view)
                              │
                              ▼
                   Change Classification (§5.1)
                              │
                              ▼
                 Selective Invalidation (§5)
                              │
                              ▼
              Context Retrieval — hybrid (§7)
                              │
                              ▼
                     Context Contract (§6)
                              │
                              ▼
                        LLM / IDE
                              │
                              ▼
              Verification — compile/test (§8)
```

### 3.1 What comes from PolyFlow / agents, honestly assessed

**Reused (pattern, not code — different problem domain):**
- **Hash-chain versioning.** PolyFlow's runtime creates a Merkle ledger node per execution (`polyflow/runtime.py`, verified live — real SHA-256 chain, not decorative). The *pattern* — content-addressed, monotonically-chained versioning — is directly applicable to RCIR's node versioning (§4.4). This is a real, working piece of prior code to model from, not something to import as-is, since PolyFlow's ledger versions `.poly` execution results and RCIR needs to version arbitrary-language AST-derived summaries. Re-implement the pattern in RCIR's own module; don't create a dependency on PolyFlow's package for this.
- **Guard-engine structure as an interface pattern**, not its logic. `polyflow/guards.py`'s design (a list of independent check functions, each returning pass/fail plus a message) is a reasonable shape for RCIR's own validation layer (e.g., checking that a computed interface-diff is well-formed before it's trusted). The actual regex-based checks in PolyFlow's guards are too weak for RCIR's needs (verified: `os.system()` after `import os` isn't caught) — do not reuse the checks themselves, only the "list of independent, composable checks" shape.

**Explicitly NOT reused:**
- **`enterprise-platform-pure/`'s 281 modules.** These are non-functional scaffolding (§0.1). Do not use them as reference implementations, examples, or starting points for anything in RCIR. If they come up in a search of the PolyFlow repo during implementation, treat that as a hit to ignore, not a pattern to follow.
- **The `.poly` parser itself.** It parses a custom DSL (`@contract`, `@schema`, `@python[service]` blocks), not general-purpose source code. RCIR needs a real AST parser for whatever language is chosen in Phase 0 (Python's `ast` module, or `tree-sitter` for multi-language future work) — this is new code, not an adaptation of PolyFlow's parser.
- **The `agents` repo's AEF framework** — a prompting/process discipline for how an LLM should approach a task, not executable infrastructure (verified: nothing in the repo enforces that its playbooks are followed). It can inform *how* the coding agent building RCIR structures its own work session-to-session (e.g., a constitution-style checklist before each phase), but contributes no code and shouldn't be described as an integrated component.

**Deferred integration (explicitly out of scope for this build, per earlier scoping):**
- RCIR eventually serving as the context-provider for `.poly` file authoring inside PolyFlow. This requires RCIR to exist and work first. Do not build toward this now — it will pull scope back into `.poly`-specific parsing before the general-purpose system is proven.

### 3.2 Repository placement
Build RCIR as a **new, standalone repository** (`rcir/` — separate from `PolyFlow` and `agents`), reasons:
- It operates on arbitrary source repos (Python/TS/etc.), not `.poly` files — different input domain, no reason to nest it inside PolyFlow's package structure.
- Packaging (`pip install rcir`) is easier to reason about and test as an independent package.
- PolyFlow integration is deferred (§3.1) — a standalone repo keeps that integration a deliberate future step (import RCIR as a dependency) rather than an accidental coupling from day one.

---

## 4. Core data structures

### 4.1 Dependency Graph (source of truth)
Nodes = functions/methods/classes. Edges = calls, imports, inherits, each carrying:
```python
{"type": "calls", "confidence": 0.73, "resolution": "static_inference" | "static_exact" | "dynamic_unresolved"}
```

### 4.2 Hierarchy (derived view)
- Leaf = function/method → file → module → service/repo root.
- Cycles: SCC collapse, size-capped (threshold e.g. 30 nodes; above it, recurse into internal graph/hierarchy rather than one god-node).
- Multi-parent nodes: graph is source of truth; hierarchy assigns one canonical position for indexing, retrieval falls back to direct graph traversal when the hierarchy path doesn't cover a query (§7).
- Hub nodes: relevance-weighted prior in retrieval scoring, not unconditional inclusion.
- Non-function artifacts (SQL, YAML, Dockerfiles): whole-file granularity, flagged `"coarse"`.

### 4.3 Node state model (3 categories — interface, behavior, data-contract)
Dependency/config/test state deferred to v2 direction, per prior scoping decision — noted explicitly in writeup, not silently dropped.

### 4.4 Consistency model
Each node versioned (hash-chain pattern from §3.1); queries use snapshot isolation.

---

## 5. Core algorithm: State-Split Incremental Invalidation

```
On edit to node N:
  1. Recompute interface diff, behavioral diff, data-contract diff for N.
  IF interface or data-contract changed:
      → regenerate N's summary; propagate upward through the dependency hierarchy (blast radius)
  IF only behavioral state changed:
      → regenerate N's own summary; update immediate parent only if parent summary embeds child behavior; do NOT propagate further
```

### 5.1 Node metadata
```json
{
  "interface_status": "unchanged" | "changed",
  "body_status": "unchanged" | "changed",
  "data_contract_status": "unchanged" | "changed" | "n/a",
  "summary_version": "v183",
  "summary_source": "incremental_ast_analysis",
  "edge_confidence_floor": 0.73
}
```

### 5.2 Success metric
Two plots: invalidation cost vs. repo size (split by edit type), and end-to-end task success rate (§8.2) using the invalidated context vs. baselines.

---

## 6. Context Contract

```json
{
  "query": "<the LLM's question>",
  "nodes": [
    {
      "path": "src/foo/bar.py::process_request",
      "level": "function",
      "summary": "...",
      "raw_snippet": "...",
      "interface_status": "unchanged",
      "body_status": "changed",
      "summary_version": "v183",
      "summary_source": "incremental_ast_analysis",
      "granularity": "fine" | "coarse"
    }
  ],
  "token_budget_used": 3400,
  "token_budget_total": 8000,
  "coverage_warning": null | "cross-cutting query — hierarchy may have missed related nodes; graph traversal used as fallback"
}
```

---

## 7. Retrieval — hybrid, three passes
1. Flattened/collapsed-tree scoring across all levels (not gated by ancestor scores).
2. Direct symbol/keyword match.
3. Graph traversal outward from selected nodes by confidence-weighted edges.

Merge, dedupe, rank, fill token budget, report `coverage_warning` honestly. Hub nodes get a scoring boost in pass 1, not automatic inclusion.

---

## 8. Benchmark plan

### 8.1 Ground-truth eval set
2-3 repos × 10-12 tasks. Three label types per task: **modification set** (files a human changed), **reasoning/context set** (files needed to understand the change), **forbidden/irrelevant set** (plausible-looking wrong candidates).

### 8.2 End-to-end task success — the primary benchmark
```
Context Runtime → LLM → code edit → compile → test suite → pass/fail
```
Metrics: task completion rate, compile/syntax success, test pass rate, regression rate, tokens-per-successful-task.

### 8.3 Baselines
1. Full-context (report feasible/infeasible per repo-size tier)
2. RAPTOR-as-published
3. Aider repo-map
4. Your system, 3-way ablated: full system / minus invalidation / minus hierarchy

---

## 9. Known failure modes (carried from v2, unchanged — see v2 changelog for full derivation)

| # | Failure mode | Mitigation |
|---|---|---|
| 1 | Body-only edits silently stale a behavior-describing parent summary | State-split propagation (§5) |
| 2 | Opaque confidence score, no defined computation | Structured provenance fields (§5.1) |
| 3 | Graph→tree collapse loses multi-parent reachability | Graph is source of truth; graph-traversal fallback (§7) |
| 4 | SCC collapse creates ungranular "god nodes" | Size-capped recursive decomposition (§4.2) |
| 5 | Unconditional hub-node inclusion re-breaks token budget | Relevance-weighted prior (§4.2) |
| 6 | Dynamic dispatch/DI/reflection breaks static call-graph assumptions | Per-edge confidence + resolution type (§4.1) |
| 7 | Top-down retrieval misses high-value nodes under low-scoring ancestors | Hybrid retrieval (§7) |
| 8 | Ground truth conflates "files changed" with "context needed" | Three-label eval set (§8.1) |
| 9 | Benchmark measures retrieval quality, not working code | End-to-end compile/test harness (§8.2) |
| 10 | Full-context baseline silently infeasible at scale | Report feasible/infeasible per tier |
| 11 | **New: implementation is fabricated/templated rather than real** | **§0.1 Anti-Fabrication Discipline — verification command required per phase** |

---

## 10. Implementation roadmap — concrete, file-level, LLM-agent-executable

Each phase: files to create, responsibilities, and a **Definition of Done** that is a literal command to run plus what real (non-fabricated) output looks like. Do not mark a phase done without running its verification command and recording the actual output.

### Phase 0 — Foundations (weeks 1-2)
**Decision to make first:** language for v1. Recommend **Python** (mature `ast` module, no external parser dependency for v1; switch/extend to `tree-sitter` only if multi-language becomes necessary later).

**Files:**
- `rcir/graph/extractor.py` — walks a repo, builds the call/import graph using Python's `ast` module (`ast.parse`, visit `Call`, `Import`, `ImportFrom`, `FunctionDef`, `ClassDef` nodes)
- `rcir/graph/edges.py` — edge confidence tagging: `static_exact` for direct name resolution, `static_inference` for attribute-based calls resolved via type inference, `dynamic_unresolved` for `getattr`/dispatch-table patterns that can't be statically resolved
- `rcir/graph/scc.py` — Tarjan's or Kosaraju's SCC algorithm, size-capped collapsing (threshold configurable, default 30 nodes)
- `tests/test_extractor.py` — real tests (§0.1 rule 3)

**Definition of Done:**
```bash
git clone https://github.com/pallets/flask.git /tmp/flask
python -m rcir.graph.extractor /tmp/flask --output /tmp/flask_graph.json
python -c "import json; g=json.load(open('/tmp/flask_graph.json')); print(f'{len(g[\"nodes\"])} nodes, {len(g[\"edges\"])} edges')"
```
**Real output looks like:** hundreds of nodes, hundreds-to-thousands of edges, with actual Flask function/class names visible in the node list (`Flask.__init__`, `route`, `Blueprint.register`, etc.) — not a fixed count, not empty, not placeholder names. **If the node/edge count is suspiciously round or the names look generic, that's a red flag — check manually before proceeding (§0.1 rule 6).**

---

### Phase 1 — Hierarchy as a view (weeks 3-4)

**Files:**
- `rcir/hierarchy/builder.py` — constructs the function→file→module→service hierarchy from the graph (§4.2), does NOT mutate or replace the graph
- `rcir/hierarchy/hubs.py` — in-degree computation, hub scoring weight assignment
- `rcir/hierarchy/granularity.py` — non-function artifact fallback (SQL/YAML/Dockerfile detection, whole-file node creation)

**Definition of Done:**
```bash
python -m rcir.hierarchy.builder /tmp/flask_graph.json --output /tmp/flask_hierarchy.json
python -c "
import json
h = json.load(open('/tmp/flask_hierarchy.json'))
# Pick 3 random leaf nodes, print their full ancestor chain
import random
leaves = [n for n in h['nodes'] if n['level']=='function']
for n in random.sample(leaves, 3):
    print(n['path'], '->', n.get('ancestors'))
"
```
**Real output looks like:** three different, plausible ancestor chains (function → its actual containing file → actual containing module → root), each one different because the sampled functions are actually in different files. **If all three chains look identical or one of them is empty, the hierarchy builder is broken or stubbed — do not proceed to Phase 2.**

---

### Phase 2 — State-split invalidation (weeks 5-8)

**Files:**
- `rcir/state/diff.py` — interface diff (signature, exports, type shape), behavioral diff (body hash/AST-diff), data-contract diff (SQL string / schema literal detection inside function bodies)
- `rcir/state/propagate.py` — the propagation rule from §5
- `rcir/state/versioning.py` — hash-chain versioning, adapted from PolyFlow's Merkle-ledger pattern (§3.1) — **re-implemented here, not imported from PolyFlow**
- `tests/test_invalidation.py`

**Definition of Done — this is the phase where fabrication is easiest and most damaging, verify carefully:**
```bash
cd /tmp/flask
git log --oneline -20   # pick 5 real historical commits that changed function bodies without changing signatures
# For each commit, checkout before/after, run the diff detector, confirm:
python -m rcir.state.diff --before <sha>~1 --after <sha> --path /tmp/flask
```
**Real output looks like:** for a real historical commit that only changed a function body (verify this manually by reading the diff yourself first), the tool reports `interface_status: unchanged, body_status: changed`. **Construct this test from real commits you've read, not from a toy file you wrote to match the expected output (§0.1 rule 3) — the whole point is proving the detector works on code you didn't write to be easy.**

Also required: run the **invalidation-cost measurement** across at least 3 repo-size tiers (small/medium/large clones) and produce the actual plot described in §5.2 before marking this phase done — a plan for the plot is not the plot.

---

### Phase 3 — Hybrid retrieval + Context Contract (weeks 9-10)

**Files:**
- `rcir/retrieval/scorer.py` — TF-IDF or small embedding model scoring (start simple, per earlier scoping)
- `rcir/retrieval/hybrid.py` — the three-pass merge (§7)
- `rcir/contract/schema.py` — Context Contract data structure (§6), with validation (adapt the guard-engine "list of composable checks" shape from PolyFlow, §3.1 — not its regex logic)

**Definition of Done:**
```bash
python -m rcir.retrieval.hybrid /tmp/flask_hierarchy.json --query "why does route registration fail for blueprints with url_prefix" --budget 4000
```
**Real output looks like:** a Context Contract JSON where the returned nodes are plausibly related to blueprint/route registration (check manually — do the file paths make sense for this specific question?), not a fixed top-N by file size or alphabetical order. **Run 3 different, unrelated queries and confirm the returned node sets are meaningfully different from each other — if every query returns the same nodes, the scorer isn't actually scoring.**

---

### Phase 4 — Eval set + benchmark harness (weeks 11-14)

**Files:**
- `eval/labeling/` — the three-label ground truth per task (§8.1), stored as reviewable JSON/YAML, not generated by the system under test
- `eval/harness/sandbox.py` — per-repo sandboxed execution (dependency install, test runner invocation)
- `eval/harness/run_baseline.py` — runs a given baseline (RAPTOR / Aider repo-map / RCIR ablation variant) against a task, captures the LLM's patch, applies it, compiles, runs tests
- `eval/report.py` — aggregates results into the metrics in §8.4

**Definition of Done:**
```bash
python -m eval.harness.run_baseline --baseline rcir_full --repo flask --task task_003
```
**Real output looks like:** an actual patch diff, an actual compile/test log (pass or fail — either is valid, a fabricated "always pass" is not), and a recorded token count. **Run this for at least one task where you already know, from writing the ground truth yourself, that the correct fix requires touching 2+ files — if the harness reports success while only touching 1 file, investigate before trusting any aggregate numbers.**

---

### Phase 5 — Writeup (weeks 15-16)

- Report results honestly, including negative/mixed findings.
- Explicit prior-art section (§2).
- Explicit scoping decisions section: what was deferred (§4.3's 3-of-6 state categories, §8.3's 3-way-of-6-tier ablation) and why — stated as a decision, not discovered as a gap by a reader.
- **Include the actual verification transcripts from each phase's Definition of Done** (§0.1 rule 5) as an appendix — this is what makes the writeup itself resistant to the same fabrication risk the whole plan is designed against.

---

### Still explicitly out of scope
Multi-language support beyond Python, full 6-category state model, full 6-tier ablation ladder, PolyFlow integration, packaging/distribution polish, enterprise/compliance features, custom HNSW index, any go-to-market work.

---

## 11. Success criteria

- **(a)** Invalidation cost for body-only edits stays local while interface/data-contract edits scale with blast radius, **and** end-to-end task success is comparable to or better than RAPTOR/Aider baselines.
- **(b)** Any part doesn't hold, explained with the three-label eval set showing exactly where retrieval or invalidation failed.

Both are legitimate outcomes **only if every phase's Definition of Done was actually run and its real output recorded** (§0.1) — a result built on unverified phases is not a result, regardless of which of (a) or (b) it resembles.

---

## 12. One-paragraph pitch

*"Existing repo-context tools for LLM coding agents either cluster by embedding similarity (RAPTOR) or rank a flat dependency graph (Aider) — none build a context hierarchy from the dependency graph itself with state-split incremental invalidation, and none report end-to-end task success rather than retrieval-quality proxies alone. This project implements that combination, tests it against published baselines with a three-label ground-truth eval set and a real compile/test harness, and reports the result honestly — positive or negative — as a lightweight, self-hostable package."*

---

## 13. Changelog

**v1 → v2:** see prior version's §13 — state-split invalidation, structured provenance, graph-as-source-of-truth, hybrid retrieval, three-label eval set, end-to-end harness, scoped ablation, research-question framing. Full derivation and per-item disposition preserved in v2.

**v2 → v3:**
| Change | Reason |
|---|---|
| Added §0.1 Anti-Fabrication Discipline as a standing, numbered rule | Direct consequence of the PolyFlow 281-module audit finding; the user explicitly required this be documented, not just remembered |
| Added §3.1 explicit reuse/no-reuse map against PolyFlow and agents repos | User requested the plan account for what's already built |
| Added §3.2 repo placement decision (standalone repo, not nested in PolyFlow) | Needed for an implementer to actually start a repository |
| Rewrote §10 from phase descriptions into concrete file paths, responsibilities, and runnable Definition-of-Done commands | User requested the plan be directly executable by an LLM coding agent inside the IDE, with explicit cross-verification that nothing is mocked |
| Added failure mode #11 (fabricated/templated implementation) to §9 | Names the specific failure this version is designed to prevent |

---

## 14. Verification protocol — run this at the end of every phase, no exceptions

1. Run the phase's Definition of Done command from §10. Record the actual output (copy-paste, not paraphrase).
2. Pick 2-3 outputs you did NOT specifically test during development. Manually inspect them for plausibility (§0.1 rule 6) — this is the exact process that found PolyFlow's 281 hollow modules in under 5 minutes; it works because fabricated output is repetitive across samples in a way real analysis output isn't.
3. If any check in step 2 looks templated, repetitive, or suspiciously uniform across different inputs — stop, do not proceed to the next phase, fix the underlying component.
4. Commit the verification transcript alongside the phase's code, not just the code.
