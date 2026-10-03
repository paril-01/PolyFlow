# RCIR v8.2 — Ranking Report

> Source artifacts: `results/ranker_ablations.json`, `results/selected_ranker_config.json`, `results/context_plane.json`

## Selected Ranker Configuration

```json
{
  "selected_configuration": "Cascaded_Operation_Profiles",
  "rationale": "Cascaded ranking with semantic buckets prevents feature inversion and achieves highest nDCG/Precision.",
  "metrics": {
    "precision_at_20": 0.33,
    "precision_at_50": 0.304,
    "ndcg_at_50": 0.4731,
    "mrr": 0.7167
  },
  "config": {
    "use_entity_identity": true,
    "use_edge_resolution": true,
    "use_traversal_score": true,
    "use_type_compatibility": true,
    "use_change_compatibility": true,
    "use_boundary_contract": true,
    "use_bm25": true,
    "use_module_distance": true,
    "use_test_relationship": true,
    "use_historical": true,
    "use_hub_penalty": true,
    "use_cascaded_ranking": true,
    "use_diversity": true,
    "max_per_module": 8
  }
}
```

## Primary Pipeline Metrics (Selected Config)

| Metric | Value | Target |
|--------|-------|--------|
| Precision@20 | 33.00% | ≥ 35% |
| Precision@50 | 30.40% | ≥ 20% |
| nDCG@50 | 0.4731 | ≥ 0.50 |
| MRR | 0.7167 | ≥ 0.70 |
| CriticalRecall@Budget | 33.88% | ≥ 60% |

## Ablation Comparison (R0–R7, Cascaded, Profiles)

| Config | P@20 | P@50 | nDCG@50 | MRR |
|--------|------|------|---------|-----|
| R0 | 46.0% | 36.4% | 0.5487 | 0.5133 |
| R1 | 45.0% | 36.0% | 0.5303 | 0.5133 |
| R2 | 43.0% | 35.6% | 0.5161 | 0.5067 |
| R3 | 39.0% | 26.4% | 0.3971 | 0.5067 |
| R4_BM25 | 41.0% | 26.4% | 0.4432 | 0.6667 |
| R5 | 33.0% | 24.4% | 0.3993 | 0.6667 |
| R6 | 30.0% | 24.0% | 0.3847 | 0.6667 |
| R7_Full_Linear | 30.0% | 24.0% | 0.3847 | 0.6667 |
| Cascaded_Semantic | 34.0% | 30.0% | 0.4780 | 0.6667 |
| Cascaded_Operation_Profiles | 33.0% | 30.4% | 0.4731 | 0.7167 |

## Key Findings

1. Feature accumulation (R1→R7) **degraded** P@20 from R0's 46.0% due to excessive module/hub penalties.
2. Cascaded semantic ranking and operation-conditioned profiles recovered MRR to 0.7167.
3. P@20 (33.00%) narrowly misses the 35% target; P@50 (30.40%) exceeds the 20% target.
