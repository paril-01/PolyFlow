# RCIR v8.2 — Impact Plane Report

> Source artifact: `results/impact_plane.json`, `results/context_plane.json`

## Summary

| Metric | Value | Target |
|--------|-------|--------|
| Global Pool Recall | 97.09% | ≥ 95% |
| Macro Pool Recall | 88.03% | ≥ 95% |
| Worst Task Recall | 66.67% | ≥ 90% |
| Total Silent Misses | 21 | ≤ 15 |
| Total Ground Truth | 721 | — |

## Per-Task Breakdown

| Task | GT Count | Pool Size | Pool Recall | Silent Misses |
|------|----------|-----------|-------------|---------------|
| TASK-1 | 24 | 188 | 95.83% | 1 |
| TASK-2 | 138 | 3166 | 89.13% | 15 |
| TASK-3 | 18 | 932 | 88.89% | 2 |
| TASK-4 | 538 | 1338 | 99.63% | 2 |
| TASK-5 | 3 | 175 | 66.67% | 1 |

## Analysis

- **Global Pool Recall** of 97.09% **passes** the ≥ 95% target.
- **Macro Pool Recall** of 88.03% is **below** the ≥ 95% target, dragged down by tasks with lower individual recall.
- **Worst Task Recall** of 66.67% is **below** the ≥ 90% per-task floor.
- 21 silent misses exceed the ≤ 15 threshold.
