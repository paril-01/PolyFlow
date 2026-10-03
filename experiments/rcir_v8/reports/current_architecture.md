# RCIR v8 — Current Architecture Audit (PHASE 1)

**Baseline Commit:** `226cfc6b3b8663f98dd97f0327529f765ac36284`
**Audit Date:** 2026-10-04
**Auditor:** Automated architectural analysis

---

## 1. LEXICAL RETRIEVAL

**Module:** `rcir/src/rcir/retrieval/scorer.py` → `TFIDFScorer`

**Implementation:**
- stdlib-only TF-IDF (no external dependencies)
- Tokenization: `_TOKEN_SPLIT` (non-alphanumeric split) + `_CAMEL_SPLIT` (camelCase decomposition)
- Document construction (`_build_node_document`): concatenates node path, kind, argument names/annotations, decorators, return annotation, bases, children
- IDF: `log(N / df)` — standard log-IDF, no smoothing
- TF: normalized by document length (`tf / doc_len`)
- No BM25, no k1/b saturation, no length normalization beyond raw TF division

**Issues:**
1. **No sublinear TF saturation.** A term appearing 10× gets 10× the weight of 1× — BM25's `k1`/`b` parameters would dampen this.
2. **No IDF smoothing.** Terms appearing in exactly 1 document get `log(N)` IDF regardless of corpus size.
3. **Document model is signature-only.** Docstrings, comments, and string literals are not indexed. A query about "thumbnail" won't match a function whose body contains `thumbnail` unless it's in the path or args.
4. **No field weighting.** A match in the symbol name should carry far more weight than a match in an argument annotation, but both contribute equally to the TF-IDF score.

**Verdict:** Functional but shallow. Pass 2 (symbol match) partially compensates, but the lack of body text indexing is a structural limitation.

---

## 2. SYMBOL MATCHING

**Module:** `rcir/src/rcir/retrieval/hybrid.py` → `_pass2_symbol_match`

**Implementation:**
- Extracts symbol name (last component after `::` or `/`)
- Three scoring tiers:
  - Exact symbol name match: +5.0 per query token
  - Token overlap in symbol part: +2.0 per common token
  - Substring match in full path: +0.5 per query token
- No type awareness, no namespace resolution, no overload disambiguation

**Issues:**
1. **Generic symbol collision.** `getId` matches every class that has a `getId()` — no receiver/owner disambiguation. This is explicitly called out in the v8 spec (PHASE 5).
2. **No case-insensitive deduplication.** `IConfig` vs `iconfig` handled via tokenization, but `IConfig` as a symbol name matches any `config` substring.
3. **Fixed scoring weights.** The 5.0/2.0/0.5 constants are hardcoded, not tunable. No ablation evidence exists for these values.

**Verdict:** Useful for high-confidence exact matches but produces massive noise on common symbol names.

---

## 3. GRAPH EXPANSION (PASS 3)

**Module:** `rcir/src/rcir/retrieval/hybrid.py` → `_pass3_graph_traversal`

**Implementation:**
- BFS from top-20 seed nodes (selected by merged Pass 1 + Pass 2 scores)
- Bidirectional: traverses both outgoing and incoming edges
- Max 2 hops
- Minimum confidence threshold: 0.3
- Score propagation: `current_score * confidence * (0.5 ^ hop)`
- No edge-type filtering — all edge types traversed equally
- No direction-aware policy — a `calls` edge traversed backward (finding callers) treated same as forward (finding callees)

**Issues:**
1. **This is the primary source of the 94%+ false-positive rate.** BFS at 2 hops from 20 seeds across both directions on 109K edges creates a massive candidate set. Every node within 2 hops of any popular symbol gets included.
2. **No edge-type policy.** A `rename` operation should follow `callers + imports + overrides`, not traverse `config_service` edges bidirectionally. All edge types get equal treatment.
3. **No change-type awareness.** The traversal doesn't know what kind of change is being requested. A schema field change should traverse `schema → migration → ORM → serializer`, not random BFS.
4. **No module boundary penalty.** Crossing service boundaries costs nothing in the scoring — a 2-hop path that crosses 3 modules gets the same weight as one within the same package.
5. **Bidirectional traversal doubles the candidate explosion.** Incoming edges (callers) should only be followed for specific change types (rename, signature change). For many operations, only outgoing edges (callees, dependencies) matter.
6. **Hub contamination.** When a seed node happens to be a hub (high in-degree), its outgoing edges alone can pull in hundreds of candidates.

**Verdict:** This is the core architectural problem. The BFS is change-type-unaware, direction-unaware, and edge-type-unaware. It achieves high recall by brute force but produces catastrophic noise.

---

## 4. EDGE DIRECTION HANDLING

**Current behavior:** Both directions traversed uniformly in Pass 3 (lines 150-163 of `hybrid.py`).

**Impact:** For a node with N outgoing and M incoming edges, BFS generates O(N+M) candidates per hop. At 2 hops, this is O((N+M)²) in the worst case, bounded only by graph connectivity.

**What should happen:**
- **rename**: follow callers (incoming `calls` edges), importers (incoming `imports`), overrides (incoming `overrides`) — NOT callees
- **signature change**: follow callers + interface implementors — NOT unrelated inheritors
- **schema change**: follow ORM mappings + serializers + API contracts — NOT all callers of the class

**Verdict:** Undifferentiated direction handling is a primary contributor to low precision.

---

## 5. HOP HANDLING

**Current behavior:**
- `max_hops=2` hardcoded in `_pass3_graph_traversal`
- Score decay: `0.5^hop` per hop (50% at hop 1, 25% at hop 2)
- No adaptive hop depth based on change type or module structure

**Issues:**
1. **2 hops is too many for some change types, too few for others.** A rename within a single file needs 1 hop (callers). A cross-service schema migration may need 3+ hops through middleware layers.
2. **Fixed decay is not evidence-based.** The 0.5 factor is hardcoded. No experiment compares different decay functions.
3. **No early termination.** If the candidate set exceeds a threshold, traversal should stop early. Currently it always completes all 2 hops.

**Verdict:** The hop policy needs to be change-type-dependent and bounded by candidate count.

---

## 6. CONFIDENCE / RESOLUTION HANDLING

**Module:** `rcir/src/rcir/graph/edges.py`

**Implementation:**
- Four resolution types: `static_exact` (1.0), `static_inference` (0.7), `dynamic_unresolved` (0.3), `unsupported` (0.0)
- Confidence used as edge weight in Pass 3 traversal
- Resolution derived from analysis mechanism (AST-based for Python, regex-based for PHP)

**Issues:**
1. **Confidence is not a probability.** The values 1.0/0.7/0.3 are ordinal categories, not calibrated probabilities. The code treats them as multiplicative weights, which is mathematically unsound but practically functional.
2. **No per-edge-type calibration.** An `imports` edge at `static_inference` (0.7) is fundamentally different from a `calls` edge at `static_inference` (0.7) — the former is almost certainly correct (PHP `use` statement parsing), the latter may be wrong (method name pattern match).
3. **Missing resolution categories.** The current system has no `heuristic`, `historical`, or `test_relationship` resolution types that v8 requires.

**Verdict:** Functional but coarse. The ordinal encoding works but prevents fine-grained ranking.

---

## 7. CANDIDATE MERGING

**Module:** `rcir/src/rcir/retrieval/hybrid.py` → `hybrid_retrieve`

**Implementation:**
- Pass 1 + Pass 2 merged via additive scores (line 224)
- Pass 3 merged into final with 0.5 weight multiplier (lines 234-238)
- Final ranking by descending merged score
- Relevance floor: `top_score * min_relative_score` (default 0.15)

**Issues:**
1. **Additive merging of incommensurable scores.** Pass 1 (TF-IDF, typically 0-2) and Pass 2 (symbol match, typically 0-15) are on different scales. Pass 2 dominates when it fires.
2. **Fixed 0.5 weight for graph expansion.** No evidence for this weight. It could be too high (admitting too many graph-discovered nodes) or too low (losing legitimate transitive dependencies).
3. **No normalization.** Scores from different passes are not normalized to a common scale before merging.

**Verdict:** The merging strategy is ad hoc. Score normalization and evidence-based weighting would improve precision.

---

## 8. RANKING

**Current behavior:** Single composite score (Pass 1 + Pass 2 + 0.5*Pass 3), sorted descending. No multi-factor ranking beyond the merged score.

**Missing:**
- No candidate-level evidence vectors (v8 PHASE 9)
- No contradiction detection (wrong receiver type, wrong namespace)
- No generic symbol penalty
- No hub-degree penalty
- No module-distance penalty
- No change-type compatibility scoring

**Verdict:** The ranking is effectively a single number. This makes it impossible to debug why a false positive ranks higher than a true positive. v8 requires transparent, multi-factor scoring.

---

## 9. TOKEN BUDGETING

**Module:** `rcir/src/rcir/retrieval/hybrid.py` → `_estimate_tokens` + budget loop

**Implementation:**
- Token estimation: `text_length / 4` with minimum 15 tokens per node
- Fine granularity: includes path + args + return annotation + decorators + estimated line count × 40
- Coarse granularity: path length / 4, minimum 15
- Adaptive downgrade: if a node exceeds remaining budget at fine, try coarse
- Budget enforcement: hard stop when budget exhausted

**Issues:**
1. **Token estimation is crude.** `text_length / 4` is a rough heuristic. Real tokenizer counts would vary by 20-40% depending on the model's BPE vocabulary.
2. **No priority-based budgeting.** Top-ranked candidates should get fine granularity; low-ranked ones should get coarse or be summarized. Currently, order of iteration determines who gets fine vs. coarse.
3. **No iterative refinement.** The budget is filled in a single pass. v8 PHASE 14 requires iterative retrieval where the agent can request more context.

**Verdict:** Functional MVP but lacks the sophistication for useful context compilation.

---

## 10. GROUND-TRUTH METHODOLOGY

**Current implementation:**
- 10 hand-curated edge-level ground truth cases (`ground_truth_edges.json`)
- 7 controlled mutation cases with grep-based ground truth
- 5 historical PR cases
- Ground truth is file-level for mutations, edge-level for the 10 curated cases
- Evaluation mixes file-level recall (for 2-hop expansion) with edge-level recall (for curated cases)

**Issues:**
1. **Only 10 edge-level cases.** This is too small for statistical significance. v8 PHASE 3 requires expanding this substantially.
2. **File-level vs edge-level confusion.** The "96.7% recall" figure is candidate-file recall (2-hop expansion), not edge recall. The edge recall is 70% (7/10 true positives). These must be clearly separated.
3. **No dev/validation/test split.** All 10 cases are used for both development and evaluation. v8 PHASE 12 requires formal splits.
4. **Ground truth categories are unbalanced.** 2 inheritance, 1 import, 1 DI, 1 interface, 1 route, 1 method_call, 1 static_call, 1 event, 1 frontend_backend. Categories with only 1 case cannot produce meaningful per-category metrics.
5. **No ranked retrieval evaluation.** Current evaluation is binary (found/not found). v8 PHASE 2 requires Recall@K, Precision@K, MRR, nDCG.

**Verdict:** The ground truth is a starting point, not a benchmark suite. It needs substantial expansion and formalization.

---

## ARCHITECTURE SUMMARY

### Data Flow

```text
Repository Files
    │
    ▼
[extractor.py]  ─── AST parsing (Python) + regex (PHP/Go/Java/JS/TS)
    │                 + proto parsing + route discovery + config discovery
    │
    ▼
Graph { nodes: [], edges: [] }
    │
    ▼
[builder.py]  ─── Hierarchy: file→module→root tree + hub scores
    │
    ▼
Hierarchy { nodes: [], hub_scores: {} }
    │
    ▼
[hybrid.py]  ─── Three-pass retrieval:
    │              Pass 1: TF-IDF (all nodes)
    │              Pass 2: Symbol match (all nodes)
    │              Pass 3: BFS expansion (top-20 seeds, 2 hops, bidirectional)
    │              → Merge → Budget → ContextContract
    │
    ▼
[impact.py]  ─── Change Impact Report (symbol → blast radius)
    │              Also uses 2-hop transitive expansion
    │
    ▼
[agent_loop.py]  ─── ReAct tool-calling loop
                       → Coding agent with inspect/edit/test tools
```

### Module Inventory

| Module | File | LOC | Purpose |
|--------|------|-----|---------|
| Graph Extractor | `graph/extractor.py` | 614 | AST/regex graph extraction |
| Edge Types | `graph/edges.py` | 92 | Edge data model + confidence |
| PHP Scanner | `graph/php_scanner.py` | ~770 | PHP class/method/use extraction |
| PHP Routes | `graph/php_routes.py` | ~220 | Nextcloud/Symfony/Laravel route parsing |
| Proto Parser | `graph/proto_parser.py` | ~340 | Protobuf service/message extraction |
| Polyglot Scanner | `graph/polyglot_scanner.py` | ~820 | Go/C#/Java/JS/TS scanning |
| Config Discovery | `graph/config_discovery.py` | ~440 | Docker/K8s config service discovery |
| HTTP Routes | `graph/http_routes.py` | ~640 | HTTP route/client call matching |
| Hierarchy Builder | `hierarchy/builder.py` | 240 | file→module→root tree |
| Hub Scoring | `hierarchy/hubs.py` | 83 | Log-damped in-degree scoring |
| Granularity | `hierarchy/granularity.py` | ~95 | Coarse artifact detection |
| TF-IDF Scorer | `retrieval/scorer.py` | 176 | Query-to-node TF-IDF |
| Hybrid Retrieval | `retrieval/hybrid.py` | 363 | Three-pass retrieval + budgeting |
| Contract Schema | `contract/schema.py` | 348 | Context contract + validation |
| Impact Report | `impact.py` | 287 | Change blast radius report |
| Agent Loop | `orchestrator/agent_loop.py` | 324 | ReAct tool-calling agent |

### Key Architectural Problems (Ranked by Impact)

| # | Problem | Severity | v8 Phase |
|---|---------|----------|----------|
| 1 | **Undirected BFS produces 94%+ FP rate** | CRITICAL | 7 |
| 2 | **No change-type-aware traversal** | CRITICAL | 4, 7 |
| 3 | **No entity identity / generic symbol collision** | HIGH | 5 |
| 4 | **No multi-factor ranking / evidence vectors** | HIGH | 9, 10 |
| 5 | **No edge-type differentiation in traversal** | HIGH | 6, 7 |
| 6 | **Incommensurable score merging** | MEDIUM | 8, 10 |
| 7 | **Ground truth too small for evaluation** | MEDIUM | 3, 12 |
| 8 | **No ranked retrieval metrics** | MEDIUM | 2 |
| 9 | **No context compilation (dump vs. compile)** | MEDIUM | 13 |
| 10 | **No iterative retrieval** | LOW | 14 |

---

## NEXT STEP

PHASE 1 is complete. Proceed to **PHASE 2 — CORRECT THE EVALUATION CONTRACT FIRST**.

Implement ranked retrieval evaluation metrics (Recall@K, Precision@K, MRR, nDCG) before making any retrieval changes, so that every subsequent change can be measured against a consistent evaluation framework.
