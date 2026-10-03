# RCIR v8 — Benchmark Contract & Evaluation Framework (PHASE 2)

**Status:** APPROVED & FROZEN  
**Baseline Commit:** `226cfc6b3b8663f98dd97f0327529f765ac36284`  
**Target Repository:** Nextcloud Server (`da57df078d0808a7235a0177bd99d23c010b472e`)  
**Specification Reference:** `enhancemts - 01.md` (PHASE 2)

---

## 1. Executive Summary

This document establishes the formal, immutable benchmark contract for the **RCIR v8 Evidence-Guided Repository Intelligence Redesign**.

Prior versions of RCIR evaluated retrieval primarily as an unranked, binary set-membership problem. That contract permitted a 2-hop candidate expansion to claim **"96.7% candidate recall"** by returning **7,988 candidates**, of which **7,276 were false positives** (a 5.6% macro candidate precision).

Under this new v8 contract, retrieval is formally evaluated as a **ranked retrieval problem**. Context provided to coding agents is bounded, and candidates must be ranked so that true dependencies appear at ranks where real LLM context windows can consume them.

When evaluated under this contract, the existing RCIR v7 baseline reveals its true performance:
- **Recall@5:** 9.0%
- **Recall@10:** 10.1%
- **Recall@20:** 11.8%
- **Recall@50:** 12.3%
- **Precision@5:** 16.0%
- **Precision@50:** 5.2%
- **MRR:** 0.5059
- **nDCG@50:** 0.1924

This empirical finding proves that **96.7% unranked candidate coverage does not translate into useful context for coding agents** because 87.7% of relevant files are ranked past position 50, buried beneath thousands of false positive files.

---

## 2. Evaluation Contract Principles

### Principle 1: Ranked Evaluation is Mandatory
File-level candidate retrieval without ranking is invalid as a measure of coding-agent assistance. All retrieval policies must produce an ordered sequence of candidates.

### Principle 2: Strict Metric Distinction
- **Candidate Pool Metrics:** Measure whether dependencies were reachable within the candidate expansion graph (unranked pool).
- **Ranked Retrieval Metrics (Recall@K, Precision@K, MRR, nDCG):** Measure whether dependencies appear at usable positions within bounded context.
- **Token-Budgeted Coverage:** Measures whether dependencies fit within a fixed token envelope (default: 4,000 tokens).
- **Edge-Level Metrics:** Must ONLY be evaluated against true edge-level ground truth (`edge_ground_truth.json`). File-level retrieval must NEVER be described as edge retrieval.

### Principle 3: No Fabricated Success (Rule 0)
- Negative results are valid.
- Evaluators must never be modified to agree with RCIR output.
- Target answers must never be hardcoded into RCIR.
- Missing values must be recorded as `NOT MEASURED`, `UNSUPPORTED`, or `BLOCKED`.

---

## 3. Required Metrics Specification

| Metric | Type | Definition / Formula | Purpose |
|---|---|---|---|
| `Recall@K` (K ∈ {5,10,20,50}) | Ranked | $\frac{\lvert \text{Relevant} \cap \text{Retrieved}[:K] \rvert}{\lvert \text{Relevant} \rvert}$ | Measures coverage at realistic LLM prompt cutoffs |
| `Precision@K` (K ∈ {5,10,20,50}) | Ranked | $\frac{\lvert \text{Relevant} \cap \text{Retrieved}[:K] \rvert}{K}$ | Measures density of signal in top positions |
| `MRR` | Ranked | $\frac{1}{\text{rank of first relevant entity}}$ | Measures how quickly the agent encounters its first true dependency |
| `nDCG@50` | Ranked | $\frac{\text{DCG@50}}{\text{IDCG@50}}$ where $\text{DCG} = \sum_{i=1}^{50} \frac{\text{rel}_i}{\log_2(i+1)}$ | Measures graded ranking quality across top-50 results |
| `candidate_count` | Pool | Total unique files/entities retrieved before ranking | Measures graph expansion blast radius |
| `token_budgeted_coverage` | Budget | $\frac{\lvert \text{Relevant} \cap \text{BudgetedContract} \rvert}{\lvert \text{Relevant} \rvert}$ | Measures coverage strictly within the 4k/8k token budget |
| `silent_misses` | Completeness | $\text{Relevant} \setminus \text{Retrieved}_{\text{all}}$ | Ground-truth dependencies completely missed by the pipeline |
| `known_unresolved` | Transparency | Count of edges flagged explicitly as dynamic/unresolvable | Auditable gaps in static analysis |
| `unsupported` | Scope | Dependencies outside language or repository scope | Explicit boundaries of capability |
| `latency_ms` | Resource | End-to-end wall clock execution time in milliseconds | Performance overhead |
| `peak_memory_mb` | Resource | Peak memory footprint in megabytes | Resource constraint tracking |

Both **Macro Averages** (unweighted mean across tasks) and **Micro Aggregates** (global pooled sums) are reported.

---

## 4. Frozen P0 Baseline Results

The baseline policy **P0** represents the untouched RCIR v7 implementation (2-hop undirected BFS + TF-IDF + symbol matching).

**Raw Evidence:** `experiments/rcir_v8/results/policy_p0.json`  
**Ground Truth:** `experiments/rcir_v8/ground_truth/ground_truth_files_v7.json` (721 total relevant files across 5 tasks)

### Macro Averages vs. Micro Aggregates

| Metric | Macro Average | Micro Aggregate | Notes |
|---|---|---|---|
| **Recall@5** | **0.0903** (9.0%) | 0.0055 (0.6%) | Minimal early recall |
| **Recall@10** | **0.1014** (10.1%) | 0.0069 (0.7%) | Slight gain from top-10 |
| **Recall@20** | **0.1183** (11.8%) | 0.0139 (1.4%) | Modest gain |
| **Recall@50** | **0.1227** (12.3%) | 0.0180 (1.8%) | Only 12.3% of relevant files in top-50 |
| **Precision@5** | **0.1600** (16.0%) | 0.1600 (16.0%) | ~1 in 6 top-5 files is relevant |
| **Precision@10** | **0.1000** (10.0%) | 0.1000 (10.0%) | 1 in 10 files is relevant |
| **Precision@20** | **0.1000** (10.0%) | 0.1000 (10.0%) | 2 in 20 files are relevant |
| **Precision@50** | **0.0520** (5.2%) | 0.0520 (5.2%) | 94.8% irrelevant at K=50 |
| **MRR** | **0.5059** | — | Top hit generally found within rank 2 |
| **nDCG@50** | **0.1924** | — | Strong penalty for late-ranking true positives |
| **Total Candidates** | **7,988** | 7,988 | Full 2-hop blast radius |
| **Silent Misses** | **10** | 10 | 98.6% candidate reachability (96.7% macro) |
| **Mean Latency** | **11,924 ms** | — | ~11.9s per task (dominated by BFS edge scan) |
| **Peak Memory** | **94.6 MB** | — | Stable memory footprint |

### Per-Task Breakdown (P0 Baseline)

| Task ID | Domain / Symbol | GT Count | Candidates | Recall@5 | Recall@20 | Recall@50 | Prec@5 | Prec@50 | MRR | Misses | Latency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **TASK-1** | Controller (`getThumbnail`) | 24 | 1,611 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0154 | 0 | 12.35s |
| **TASK-2** | Interface (`getId`) | 138 | 2,212 | 0.0072 | 0.0362 | 0.0580 | 0.2000 | 0.1600 | 0.5000 | 7 | 11.55s |
| **TASK-3** | Event (`NodeDeletedEvent`) | 18 | 476 | 0.1111 | 0.2222 | 0.2222 | 0.4000 | 0.0800 | 1.0000 | 2 | 11.82s |
| **TASK-4** | DI (`IConfig`) | 538 | 3,475 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0141 | 1 | 11.77s |
| **TASK-5** | Cross-Stack (`Recent.ts`) | 3 | 214 | 0.3333 | 0.3333 | 0.3333 | 0.2000 | 0.0200 | 1.0000 | 0 | 12.13s |

---

## 5. Architectural Diagnosis from P0 Evidence

1. **The "Candidate Coverage Illusion":**
   RCIR v7 successfully reaches 711 of 721 ground truth files (98.6% candidate coverage, only 10 silent misses). However, in TASK-1 and TASK-4, **Recall@50 is 0.0%**. The relevant files exist in the candidate set, but they are pushed beyond rank 50 by generic symbol matches and uncontrolled 2-hop BFS neighbors.

2. **TASK-1 Controller Route Failure:**
   The target `ApiController.php` was ranked #1, but the 24 ground truth files (routes, preview providers, tests) were overwhelmed by hundreds of unrelated preview system classes because Pass 1 (TF-IDF) matched every file containing preview keywords.

3. **TASK-4 DI Explosion:**
   `IConfig` is injected across hundreds of classes. Unrestricted BFS traversed from `IConfig` to every consumer, and then 2 hops to all callees of those consumers, creating 3,475 candidates and burying the actual container binding and direct consumers.

4. **TASK-3 and TASK-5 Show the Value of High Specificity:**
   When the target symbol is rare (`NodeDeletedEvent`, `Recent.ts`), MRR is 1.0000, and Precision@5 reaches 20-40%. Specificity, not expansion, drives useful ranking.

---

## 6. Success Gates for v8 Redesign

As mandated by Phase 19:
- **Retrieval Gate A:** Preserve high coverage ($\text{Recall@50} \ge 90\%$) while radically reducing candidate volume.
- **Retrieval Gate B:** Macro candidate precision $\ge 20\%$ without increasing silent misses materially.
- **Retrieval Gate C (Stretch):** Candidate recall $\ge 95\%$, macro precision $\ge 35\%$, bounded context near 4k tokens.

Every subsequent policy ($P1 \dots P6$) will be evaluated against this contract using the identical metrics and task suite.
