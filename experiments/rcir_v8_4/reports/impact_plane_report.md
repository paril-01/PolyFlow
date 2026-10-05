# RCIR v8.4 Impact Plane Benchmark Report

**Architecture**: Dual-Plane (Plane A: Structural Retrieval; Plane B: Ranking & Context)  

## 1. Cross-Split Candidate Recall
| Split | Tasks | Macro Recall | Micro Recall | Worst Task Recall | Silent Misses |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEV** | 8 | **71.04%** | 72.22% | 33.33% | 10 |
| **VALIDATION** | 6 | **56.39%** | 58.33% | 25.00% | 10 |
| **TEST (SEALED)** | 6 | **48.61%** | 50.00% | 25.00% | 12 |

## 2. Critical Dependency Recall
- **TEST Critical Micro Recall**: **64.29%**
- **Worst Task on TEST**: `TASK-TEST-02` (25.00%)
