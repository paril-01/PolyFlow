# RCIR v8.1 — Benchmark Contract & Evaluation Specification

**Version:** 8.1  
**Status:** FROZEN  
**Applies to:** RCIR v8.1 Architecture, Retrieval Experiments, and Benchmark Runners  
**Specification Reference:** `enhancements - 02.md` (PHASE 2 & PHASE 3)

---

## 1. Motivation & Correction of Flawed v8 Gate

In RCIR v8, the frozen evaluation contract declared:
$$\text{Recall@50} \ge 90\%$$

As audited in Phase 1, **this requirement is mathematically impossible** for any benchmark task where the ground-truth set $|R| > 50$.

For example, in `TASK-4` (Dependency Injection Service Resolution for `IConfig`), the ground-truth set contains $|R| = 538$ files. By definition:
$$\max(\text{Recall@50}) = \frac{\min(50, 538)}{538} = \frac{50}{538} \approx 9.29\%$$

Attempting to evaluate a static intelligence system against an impossible metric led to distorted conclusions and early candidate-truncation heuristics (`max_candidates = 60..150`), which discarded 443 out of 721 dependencies (38.56% pool recall).

RCIR v8.1 eliminates this flaw by establishing a **Dual-Plane Evaluation Contract** that separates **Dependency Coverage (Plane A)** from **Context Density (Plane B)**, and introduces **Graded Ground Truth**.

---

## 2. Graded Relevance Taxonomy (Phase 3)

Not all affected files are equally critical to completing or verifying a code change. Ground truth is partitioned into four independent tiers:

| Tier | Name | Definition | Example (`TASK-1`: `getThumbnail`) | Example (`TASK-3`: `NodeDeletedEvent`) |
|---|---|---|---|---|
| **3** | `MUST_CHANGE` | Core interface definitions, direct modification targets, breaking contracts | `routes.php`, `IProviderV2.php`, `Generator.php` | `NodeDeletedEvent.php`, `BeforeNodeDeletedEvent.php`, `HookConnector.php` |
| **2** | `MUST_INSPECT` | Direct implementations, direct test suites, immediate callers/adapters | Provider implementations (`Image.php`, `Bitmap.php`), `ApiControllerTest.php` | Direct listeners (`Trashbin.php`, `NodeDeletedListener.php`), `HookConnectorTest.php` |
| **1** | `SUPPORTING_CONTEXT` | Peripheral consumers, wiring, fixtures, helpers, autoloaders | `CDR.php`, `Imaginary.php`, remote preview mocks | Application manifests (`Application.php`), autoload maps |
| **0** | `IRRELEVANT` | Unrelated codebase files | All other repository files | All other repository files |

### Graded Ranking Quality (nDCG)
Discounted Cumulative Gain is computed using standard exponential gain:
$$\text{DCG@K} = \sum_{i=1}^K \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$$
where $\text{rel}_i \in \{0, 1, 2, 3\}$. $\text{nDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$.

---

## 3. The Dual-Plane Contract (Phase 2 & Phase 4)

### Plane A — Change Impact Plane (Audit & Dependency Discovery)
- **Primary Objective:** Maximize dependency coverage; eliminate silent misses.
- **Contract Rules:**
  1. Direct exact relationships and direct typed inferred relationships must **NEVER** be discarded due to candidate count limits.
  2. Traversal caps (`max_candidates`) are strictly prohibited in Plane A.
  3. Output is an audit artifact containing all discovered direct dependencies, policy-compatible indirect dependencies, known unresolved entities, and unsupported patterns.
- **Plane A Target Gate:**
  $$\text{CandidatePoolRecall} = \frac{|R \cap \text{CandidatePool}|}{|R|} \ge 95.0\%$$
  $$\text{Silent Misses} \le 15 \text{ across all 721 benchmark files}$$

### Plane B — Agent Context Plane (Token-Bounded Prompt Compilation)
- **Primary Objective:** Compact, high-precision context compiled for downstream coding agents within LLM token budgets (e.g. 4,000 tokens).
- **Contract Rules:**
  1. Pruning and ranking are aggressive and deterministic.
  2. Context slices use **exact entity spans** (`start_line`, `end_line`, `call_line`), never blind file-head truncation.
  3. Plane B omissions must never be reported as Plane A misses.
- **Plane B Target Gates:**
  $$\text{Precision@20} \ge 35.0\%$$
  $$\text{Precision@50} \ge 20.0\%$$
  $$\text{nDCG@50} \ge 0.50$$
  $$\text{MRR} \ge 0.70$$
  $$\text{CriticalRecall@Budget} \ge 60.0\%$$

---

## 4. Complete Metric Suite Definitions

| Metric | Formula | Purpose |
|---|---|---|
| **CandidatePoolRecall** | $\frac{\|R \cap \text{CandidatePool}\|}{\|R\|}$ | Exhaustiveness of initial impact graph expansion |
| **CandidatePoolPrecision** | $\frac{\|R \cap \text{CandidatePool}\|}{\|\text{CandidatePool}\|}$ | Signal-to-noise ratio in impact pool |
| **SilentMisses** | $R \setminus \text{CandidatePool}$ | True dependencies dropped before ranking |
| **Recall@K** | $\frac{\|R \cap \text{Retrieved}_{1..K}\|}{\|R\|}$ | Ranked recall at cutoff $K \in \{5, 10, 20, 50\}$ |
| **Precision@K** | $\frac{\|R \cap \text{Retrieved}_{1..K}\|}{K}$ | Ranked precision at cutoff $K \in \{5, 10, 20, 50\}$ |
| **R-Precision / Recall@R** | $\frac{\|R \cap \text{Retrieved}_{1..\|R\|}\|}{\|R\|}$ | Scale-invariant precision at size of relevant set |
| **CriticalRecall@K** | $\frac{\|(R_2 \cup R_3) \cap \text{Retrieved}_{1..K}\|}{\|R_2 \cup R_3\|}$ | Recall specifically for MUST_CHANGE and MUST_INSPECT files |
| **CriticalRecall@Budget** | $\frac{\|(R_2 \cup R_3) \cap \text{CompiledContext}\|}{\|R_2 \cup R_3\|}$ | Critical entities actually delivered into token budget |
| **ContextPrecision** | $\frac{\|R \cap \text{CompiledContext}\|}{\|\text{CompiledContext}\|}$ | Relevance density of compiled prompt payload |
| **TokenWeightedPrecision** | $\frac{\sum_{f \in R \cap \text{Ctx}} \text{Tokens}(f)}{\text{TotalCompiledTokens}}$ | Context token utility efficiency |
| **TokenWeightedRecall** | $\frac{\sum_{f \in R \cap \text{Ctx}} \text{Tokens}(f)}{\text{TotalGroundTruthTokens}}$ | Ground-truth token coverage in prompt |
| **nDCG@50** | $\text{DCG@50} / \text{IDCG@50}$ (Graded) | Multi-tier ranking quality |
| **MRR** | $1 / \text{rank}_1$ | First relevant document discovery |

---

## 5. Decision Gates for Final Recommendation

At the conclusion of RCIR v8.1 evaluation, the architecture will be judged by the following strict falsifiable rules:

```text
IF:
    Plane A CandidatePoolRecall >= 95%
    AND Plane B Macro Precision@50 >= 20%
    AND Plane B Macro nDCG@50 >= 0.50
    AND Context Compiler delivers real entity line spans into budget
    AND CriticalRecall@Budget >= 60%
    AND Agent E2E evaluation produces verified, syntax-checked diffs
THEN:
    RECOMMENDATION = OPTION A — VALIDATED

ELSE IF:
    Plane A CandidatePoolRecall >= 90%
    AND Precision@50 materially improves over P0 (> 15%)
    AND Context Compiler operates deterministically
THEN:
    RECOMMENDATION = OPTION B — PARTIALLY VALIDATED

ELSE:
    RECOMMENDATION = OPTION C — REJECTED
```

No manual overriding of the decision gate is permitted. Every metric must be backed by a committed JSON artifact in `experiments/rcir_v8_1/results/`.
