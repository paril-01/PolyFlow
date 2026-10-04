# RCIR v8.3 — Multi-Objective Ranking & Ablation Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Selected Configuration**: `Coverage_Only`  
**Selection Objective**: Maximized harmonic trade-off between MRR and nDCG@50 on VALIDATION split (Phase 41)

## 1. Full Ranker Ablation Comparison (All Tasks Macro Averages)
| Configuration | P@20 | P@50 | nDCG@50 | MRR | Key Trait |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `R0_Baseline` | 39.53% | 40.13% | 0.5058 | 0.7000 | Baseline |
| `Cascaded_Fixed` | 39.53% | 40.13% | 0.5048 | 0.7000 | First-hit |
| `Cascaded_Operation_Profiles` | 34.53% | 34.53% | 0.4786 | 0.7000 | Ablation |
| `Anchor_Only` | 34.53% | 34.53% | 0.4786 | 0.7000 | First-hit |
| `Coverage_Only` | 38.53% | 39.73% | 0.4687 | 0.7000 | Selected |
| `MultiObjective_Anchor_Coverage_RRF` | 39.53% | 40.53% | 0.4923 | 0.7000 | First-hit |

## 2. Split Enforcement & Selection Integrity
- **DEV Set (TASK-1, TASK-3)**: Used for algorithmic tuning and exploratory analysis.
- **VALIDATION Set (TASK-2, TASK-5)**: Sole deterministic driver of ranker selection.
- **TEST Set (TASK-4)**: Kept inaccessible during ranker selection; evaluated exactly once for formal reporting.
