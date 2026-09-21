# RCIR — Build Plan v7
### Formally-Defined, Layered, Auditable Dependency Intelligence

v7 incorporates a rigorous technical/product review of v6 — 18 issues, all accepted, 6 "surgical changes" implemented, plus one addition of my own: an explicit staged-checkpoint structure, because this critique (correctly) roughly doubles the benchmarking scope again, and an ever-growing plan that never ships anything is its own failure mode.

**The core thesis is unchanged and, per the reviewer, the strongest part of the plan — keep it:** zero-cloud, statically-sound, confidence-audited dependency analysis across service/language boundaries where IDE tooling stops working. Everything in v7 tightens the definitions and evidence underneath that thesis; nothing replaces it.

---

## 0. What changed, at a glance

| v6 concept | v7 replacement | Why |
|---|---|---|
| "Exact, audited completeness" (undefined) | Formal soundness / recall / auditability, with a defined denominator (§1) | v6's "exact" conflated three different properties |
| `complexity_signal` | `structural_complexity_signal` — explicitly *not* a difficulty estimator (§4) | Structural scope ≠ reasoning difficulty (the race-condition counterexample is decisive) |
| Human-judged complexity as routing ground truth | Empirical per-tier model success rate (§4.2) | What matters is which model succeeds, not what a human guesses |
| "Context rot → lead thesis" | "Context efficiency → research hypothesis, tested not assumed" (§2) | Matches what Anthropic's own guidance actually says (verified primary source, not paraphrase) |
| Online Boutique as sole benchmark | Three benchmark classes: controlled / synthetic / real-world (§6.1) | One fixture can't establish generality |
| "No existing tool combines all four" | "Our survey did not identify..." (§7) | Universal negatives aren't defensible claims |
| Flat Context Contract | Layered: `query` / `analysis` / `structure` / `retrieval` / `routing` (§5) | Different semantic layers were flattened into one object |
| Undefined "zero-cloud" | Precisely scoped: core analysis path only, network-isolation-testable (§3) | Must not be invalidated later by telemetry/licensing/updates |
| Unbounded cross-service scope | Explicit tiers 1-4, Tier 4 not promised until benchmarked tractable (§2.1) | "Months building a distributed-systems analyzer" is a real risk |

---

## 1. Formal redefinition of the core claim

**Not**: "exact, audited completeness."

**Instead, three separated properties, each independently measured:**

1. **Soundness**: if RCIR reports edge `A → B`, is it real? (Precision)
2. **Recall**: of all edges that actually exist, how many does RCIR find? (Requires a defined denominator — see below.)
3. **Auditability**: can RCIR explain *why* it believes an edge exists, or *why* it couldn't resolve one?

**Edge classification** (replaces the earlier informal confidence float):
```
static_exact      — resolved via protobuf/typed interface, no ambiguity
static_inferred    — resolved via pattern-matching (route strings, naming conventions)
dynamic_unresolved — a call exists, destination could not be statically determined
unsupported        — outside current analysis scope entirely (not even attempted)
```

**The completeness denominator** — this is the fix for v6's undefined "247 out of what?":
```
U = the complete set of ground-truth dependency edges relevant to a given change,
    established independently of RCIR (manual verification or synthetic injection, §6.1)

Recall    = discovered_ground_truth_edges / |U|
Precision = correct_discovered_edges / total_discovered_edges
Unresolved = ground-truth edges RCIR explicitly flags as unresolvable (a *known* gap,
             different from a silent miss)
```

**Restated core claim**: *RCIR provides statically sound dependency edges where its analysis assumptions are satisfied, and explicitly reports unresolved or ambiguous edges outside those assumptions — measured as precision and recall per edge class, against an independently-established ground truth.* This is harder to attack academically or commercially than "exact and complete."

---

## 2. Context efficiency — downgraded from thesis to tested hypothesis

**v6 said**: minimal context → equal-or-better task success, as the lead technical justification.

**Verified against Anthropic's actual published guidance** (fetched directly, not relayed): the real claim is more conditional than v6's framing. Anthropic explicitly discusses **hybrid strategies** — some context loaded up front, some retrieved just-in-time — as often *better* than either pure-minimal or pure-maximal, particularly for dynamic content, and explicitly states "minimal does not necessarily mean short." Context rot (confirmed real, Chroma's 18-model study) supports *curation*, not a specific claim that RCIR's particular selection algorithm beats all alternatives.

**v7 statement**: *Context efficiency and signal quality are a research hypothesis, supported by general context-engineering literature, to be validated specifically on coding tasks via the benchmark in §6.3 — not asserted as a product guarantee until measured.*

This is a downgrade in confidence, not in ambition — §6.3's experiment is unchanged in design, just correctly labeled as a test, not a pre-proven claim.

---

## 3. Zero-cloud — precisely scoped

**v6's version** ("no outbound network calls") is right but under-specified — a future licensing check, telemetry ping, or auto-update call would silently invalidate the whole claim without anyone noticing until an enterprise security review catches it.

**v7 definition, split explicitly:**
```
CORE ANALYSIS PATH (the claim that matters, CI-enforced, §own subsection below):
  Graph extraction, hierarchy, invalidation, retrieval, routing signal computation
  → MUST run correctly with all outbound network interfaces blocked.
  This is binary, tested on every commit, and is the actual product claim.

PRODUCT DEPLOYMENT (explicitly separate, not covered by the zero-cloud claim
  unless independently verified):
  License checks, telemetry, crash reporting, update checks, plugin marketplace
  calls, package/dependency metadata lookups.
  → These may exist in a shipped product. If they do, document exactly what
    they transmit (metadata, not code) and offer an offline/air-gapped mode
    that disables all of them, verified separately.
```

**CI check** (unchanged mechanism from v5, now scoped correctly): run the *core analysis path only* inside a network-namespace-isolated sandbox. A single call anywhere in that path fails the build. This must not be quietly broadened later by a well-meaning telemetry feature.

---

## 4. Structural complexity signal — reframed, not a difficulty estimator

**The decisive counterexample** (from the review, worth keeping verbatim as the canonical illustration in any future writeup): a rename touching 247 nodes across 12 services can be mechanically trivial; a 5-line race-condition fix touching 3 files in 1 service can be extremely hard to reason about. Structural blast radius and reasoning difficulty are different axes. v6's `complexity_signal` implicitly conflated them.

**v7: rename the field, restate the claim.**
```json
"structural_complexity_signal": {
  "nodes_touched": 3,
  "cross_service_edges_involved": 0,
  "low_confidence_edge_fraction": 0.0,
  "change_scope": "local" | "module" | "cross_service"
}
```
**Explicit statement, carried into every doc/pitch from here on**: *this estimates structural scope, not reasoning difficulty. It is a routing feature, not a complete difficulty estimator.* That one sentence, stated every time this field is discussed, protects the whole pillar from the objection that killed v6's framing.

### 4.1 What actually determines routing (redefined)
**Not**: does `structural_complexity_signal` match human-judged complexity.
**Instead**: *given a task's structural features, can RCIR predict the cheapest model tier that achieves a required success probability* — an empirical, not a subjective, target.

### 4.2 Routing ground truth (redefined, replaces v6's 5-commit sanity check)
```
For each task in the eval set (§6.2), run it against multiple model tiers
(cheap / balanced / frontier), record actual success rate per tier:

Task X:  cheap: 3/10 success | balanced: 8/10 | frontier: 10/10

Routing target: predict the cheapest tier whose success rate meets a
stated threshold (e.g. ≥80%), from structural features alone.
```
**Minimum eval-set size**: hundreds of tasks, not five — v6's 5-commit check had a stated circularity risk (hand-picking obvious examples proves nothing). Structure the eval set with **held-out labels**: ~100 each of local/body changes, interface changes, cross-module changes, cross-service changes, and mixed/ambiguous changes (500 total), and don't let whoever builds the router see the labels while selecting examples.

**Scope note**: this alone is a real, multi-week data-generation and multi-model-execution effort (500 tasks × 3 model tiers × however many retries for a stable success rate ≈ thousands of model calls). Sequence this after §6.1's controlled/synthetic benchmarks are working, not in parallel with them — see §8 Staged Checkpoints.

---

## 5. Context Contract — restructured into semantic layers

v6's flat object mixed analysis-confidence, structural characteristics, retrieval output, and routing into one undifferentiated blob. Not urgent to change today, but worth fixing before this becomes a public API contract other tools depend on:

```json
{
  "query": { "text": "...", "change_type": "interface_rename" },
  "analysis": {
    "coverage": { "resolved": 247, "unresolved": 3, "denominator_basis": "U_v1_ground_truth" },
    "confidence": { "static_exact": 240, "static_inferred": 7, "dynamic_unresolved": 3 },
    "unresolved_locations": [
      {"path": "billing-service/src/handlers.py:142", "edge_class": "dynamic_unresolved", "reason": "getattr() dynamic dispatch"}
    ]
  },
  "structure": {
    "structural_complexity_signal": { "nodes_touched": 3, "cross_service_edges_involved": 0, "change_scope": "local" }
  },
  "retrieval": {
    "nodes": [ /* unchanged node schema from v4-v6 */ ],
    "token_budget_used": 3400,
    "token_budget_total": 8000
  },
  "routing": {
    "suggested_tier": "balanced",
    "rationale": "local change scope, but 1 dynamically-unresolved edge — routed above cheap tier out of caution",
    "note": "advisory only; estimates structural scope and known-unknowns, not reasoning difficulty"
  }
}
```

---

## 6. Benchmark plan — three classes, rigorous methodology

### 6.1 Three benchmark classes (replaces Online-Boutique-only)

**A. Controlled** — Online Boutique (carried from v5/v6). Purpose: deterministic ground truth, reproducibility, controlled mutation injection.

**B. Synthetic mutation** (new) — take real open-source repositories and *automatically* inject changes with a known, generated answer key: rename an API, rename a field, change a function signature, change a protobuf field, change an HTTP endpoint, change an event topic, change a config key. Because the mutation is generated, the ground truth is generated too — this produces hundreds to thousands of cases cheaply, versus 10-15 hand-built tasks. **This is the single highest-leverage addition in this revision** — it's what makes §1's precision/recall numbers statistically meaningful rather than anecdotal.

**C. Real-world** (new) — 3-5 genuinely independent multi-service open-source projects beyond Online Boutique, to test whether results generalize or are an artifact of one codebase's structure being unusually friendly to the parser.

### 6.2 Augment comparison — frozen experimental protocol (new, replaces v6's underspecified comparison)
Before running any RCIR-vs-Augment number, freeze and document: repository version, model + model version, system prompt, agent, task prompt, tool permissions, token budget, temperature, max iterations, timeout, network conditions, indexing state, retry count, and the exact success definition. **Separate two different benchmarks that v6 conflated:**
- **Dependency-discovery benchmark**: which system identifies the correct affected call sites? (Tests §1's soundness/recall claims directly.)
- **Agent-task benchmark**: which system helps an agent successfully complete the change end-to-end? (Tests the commercial value proposition; this is the kind of benchmark Augment's own 300-PR/900-attempt evaluation is — match that rigor, don't compare an apples number to their oranges number.)

### 6.3 Context-efficiency hypothesis test (was v6's "context rot" experiment, now correctly framed as testing §2's hypothesis)
**Five conditions, not three** (v6's 3-condition design risked a strawman — deliberately bloated context isn't what real competing systems return):
```
A. Full repository (unfiltered baseline)
B. RCIR (minimal, structurally-selected)
C. Artificially bloated RCIR (RCIR's nodes + 3-5x plausible-but-irrelevant files —
   useful as a lower bound, not as "the comparison")
D. Strong semantic retrieval baseline (a real embedding-based system, not a strawman)
E. Strong hybrid retrieval baseline (semantic + lexical + reranking — matches how
   real competing systems, e.g. Context-Engine-style tools, actually work)
```
Testing RCIR against D and E is the real test of the hypothesis; A and C are reference points, not the comparison that matters.

### 6.4 Adversarial test suite (new, strengthens the auditability claim specifically)
Deliberately construct cases designed to break static analysis: dynamic dispatch, aliasing, generated clients, wrapper functions, re-exported symbols, reflection, dependency injection, service-discovery indirection, environment-specific routes, string-built URLs, protobuf-generated code, event-topic string composition, feature flags, conditional imports, dead code, duplicate service names, versioned APIs. For each: report `Detected / Missed / False positive / Unresolved / Reason`. **A tool that says "I found 244/247 and here are the 3 I couldn't verify, and here's exactly why" is a stronger, more sellable claim than one that silently reports 247/247 — this test suite is what proves the auditability half of the pitch, not just the recall number.**

### 6.5 Metrics, finalized
Recall and precision **per edge class** (§1), unresolved rate, false-negative severity (a missed doc-reference edge is not equivalent to a missed production-payment-service caller — weight by real-world impact once the eval set supports it), end-to-end task success (§6.2's agent-task benchmark), token cost, latency, and routing accuracy against empirical per-tier success rate (§4.2).

---

## 7. Competitive claims — softened, still meaningful

**Not**: "no existing tool combines all four properties."
**Instead**: *"Our current competitive survey did not identify a system combining zero-outbound-code-flow, statically-audited cross-boundary dependency analysis, and explicit unresolved-edge reporting; this is a claim we continue to validate as the market moves."* Slower to say, much harder to knock down in thirty seconds by someone finding one counterexample.

---

## 8. Layered architecture — graph as the unquestionable core

**Restructured per the review's point 11-12**, formalizing what was already implicit in v4-v6's "graph as source of truth":

```
                    Dependency Graph (source of truth, unchanged since v4)
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              Impact API      Context API    Structural Metrics API
              (humans /       (agents —      (routing — §4, entirely
               change mgmt,    §5's           optional, deletable
               §9's Change     retrieval      without touching the
               Impact Report)  layer)         graph or context layer)
```

**Hard rule, stated explicitly (was implicit before)**: routing-specific metadata, embeddings, heuristics, or model-feedback signals **never get written into the core dependency graph**. The structural complexity signal is computed as a derived view, same principle as the hierarchy itself (unchanged since v3). If the routing pillar fails experimentally (§4.2's empirical test comes back weak), it must be deletable without touching the graph, the invalidation engine, or the context-retrieval layer. This independence is what makes it safe for routing to be the pillar most likely to underdeliver — it can fail alone.

---

## 9. The actual commercial artifact — reframed per the review's sharpest point

**Enterprises don't buy "dependency intelligence."** They buy **reduced risk of breaking production when changing shared code**, and **proof that the check was done.** The `analysis` block in §5's Context Contract is not just an internal data structure — formatted for a human, it's the actual product:

```
CHANGE IMPACT REPORT
Change: User.email → User.emailAddress

Affected: 247 static call sites (240 exact, 7 inferred)
Cross-service: 12 (Identity, Payments, Orders, Notifications)
Unresolved: 3 — manual review required (locations + reasons listed)
Confidence: 97.8%
Generated-code dependencies: 1
Configuration-dependent: 2
```

**This is something an engineering org can put directly into a change-management/release workflow.** It's more immediately sellable than the routing signal, and more defensible than a bare recall percentage — it's evidence, not just a number. **Do not let the routing pillar (§4) compete for roadmap priority against this** — it's real and worth building (§8's independence guarantees it can be built and dropped in without risk), but the Change Impact Report is the artifact the pitch, the demo, and the first customer conversation should center on.

---

## 10. Cross-service scope — explicit tiers, Tier 4 not promised yet

Carried from v5/v6's engineering surface, now with hard scope boundaries the review correctly flagged as missing:

```
Tier 1 (build first): gRPC/protobuf (structured, most tractable), static HTTP routes
Tier 2: configuration-mediated edges (docker-compose, k8s manifests)
Tier 3: message/event systems (Kafka/RabbitMQ topic matching — expect lower precision, say so)
Tier 4 (do not promise until §6's benchmark says it's tractable): dynamic dispatch,
  reflection, generated/runtime-discovered edges, service-mesh-mediated calls
```
Every edge still carries the `static_exact / static_inferred / dynamic_unresolved / unsupported` classification from §1 — Tier 3/4 edges will skew toward the lower-confidence classes, and that's reported honestly, not hidden.

---

## 11. Staged checkpoints — my addition, to manage the scope this review correctly grew again

This review is right on every point and, fully adopted, roughly doubles the benchmarking/eval workload on top of what was already v6's largest section (cross-service resolution + zero-cloud verification + routing). Left unchecked, "make everything rigorous before shipping anything" becomes its own failure mode. Sequence it:

**Checkpoint 1 — Core claim, minimum viable rigor**: Tier 1 cross-service resolution only, Online Boutique only (§6.1.A), formal precision/recall/soundness per §1, zero-cloud CI from day one (§3). Ship this before touching anything else — it's the smallest slice that tests the actual core thesis (§1's restated claim) with real rigor.

**Checkpoint 2 — Generalization**: add synthetic mutation benchmark (§6.1.B) and Tier 2 cross-service scope. This is where the recall/precision numbers become statistically meaningful rather than anecdotal on one repo.

**Checkpoint 3 — Commercial artifact**: build the Change Impact Report (§9) formatting layer on top of Checkpoint 2's data — this is mostly presentation work over already-computed data, cheap relative to the analysis engine, and it's the thing to actually show a prospective customer.

**Checkpoint 4 — Real-world validation + adversarial suite**: 3-5 real multi-service repos (§6.1.C), the adversarial test suite (§6.4), Tier 3 cross-service scope.

**Checkpoint 5 — Routing** (independent, per §8's architectural guarantee, can slot in whenever or be dropped): the 500-task empirical routing eval (§4.2), `structural_complexity_signal` and the `routing` block of the Context Contract.

**Do not start Checkpoint 5 before Checkpoint 3 exists.** The Change Impact Report is the sellable artifact; routing is a bonus feature layered on independent infrastructure. If time or resources run short, Checkpoints 1-3 are the version that still has something real to show; Checkpoint 5 without 1-3 is a routing demo with no product underneath it.

---

## 12. Carried forward unchanged from v3-v6

Anti-Fabrication Discipline (9 rules — no input-independent outputs, no self-validating stub tests, loud failure over silent fake success, real-repo verification commands per phase); relationship to PolyFlow/agents (hash-chain versioning pattern reused, guard-engine shape reused, 281 hollow modules explicitly excluded, standalone repo placement); state-split incremental invalidation (interface/behavioral/data-contract propagation rule, §5 of v4); the underlying dependency-graph-as-source-of-truth architecture (§3-4 of v4, now formalized further in §8 above).

---

## 13. One-paragraph pitch (v7)

*"When you rename a field or change an interface in a large, polyglot, multi-service codebase, existing AI coding tools tell you what's probably relevant — RCIR tells you, with an auditable confidence breakdown, what's structurally certain, what's inferred, and what it explicitly cannot resolve and why. It runs entirely on your infrastructure, verified by network-isolation testing, not a compliance policy. The output — a Change Impact Report — is something an engineering organization can put directly into a release process, not just a context dump for an LLM. Built for regulated-data organizations where code cannot leave the premises, and for any team where a missed cross-service call site is a production incident, not a context-quality inconvenience."*

---

## 14. Changelog v6 → v7

All 18 issues from the review accepted; the 6 "surgical changes" implemented as: (1) formal exactness/completeness definitions with denominator (§1), (2) layered graph→three-API architecture with a hard no-contamination rule (§8), (3) context rot downgraded to tested hypothesis, grounded in the actual verified Anthropic source rather than paraphrase (§2), (4) routing signal renamed and reframed as structural-not-difficulty (§4), (5) three-class benchmark replacing single-fixture reliance, plus frozen Augment-comparison protocol and adversarial test suite (§6), (6) universal competitive claim softened to a survey-scoped claim (§7). Additional: precise zero-cloud scoping separating core analysis path from product deployment concerns (§3), Change Impact Report elevated to the primary commercial artifact ahead of routing (§9), explicit Tier 1-4 cross-service scope boundary with Tier 4 gated on benchmark evidence (§10), and staged checkpoints added independently to prevent the now-larger scope from becoming unshippable (§11).
