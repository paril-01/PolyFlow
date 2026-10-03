# RCIR v8.2 — Generalization & Performance Report

> Source artifact: `results/performance_benchmark.json`

## Benchmark Configuration

- Repetitions: 5
- Tasks Evaluated: 5
- Graph Nodes: 50,346
- Graph Edges: 143,225

## Latency (milliseconds)

| Stage | Median | P95 | Mean | Min | Max |
|-------|--------|-----|------|-----|-----|
| Graph Hydration | 1023.99 | 1041.95 | 952.08 | 790.3 | 1041.95 |
| Candidate Generation | 273.62 | 592.89 | 307.0 | 112.57 | 616.48 |
| Cascaded Ranking | 24.25 | 94.07 | 30.84 | 3.61 | 94.79 |
| Context Compilation | 19.81 | 47.39 | 27.0 | 11.6 | 48.59 |
| **Total Pipeline** | **343.28** | **965.11** | 432.58 | 170.47 | 984.33 |

## Memory

| Metric | Value |
|--------|-------|
| Heap Peak Median | 3.44 MB |
| Process RSS Start | 27.05 MB |
| Process RSS End | 328.77 MB |
| Process RSS Delta | 301.71 MB |

## Generalization Status

The current benchmark is limited to the Nextcloud repository (50K+ nodes, 143K+ edges).
Phase 67 (external generalization test) requires evaluation on additional repositories
to confirm that RCIR v8.2 generalizes beyond this single codebase.
