# RCIR v8.3 — Impact Plane (Plane A) Evaluation Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Primary Metric**: Candidate Pool Recall across 2-Hop Traversal Horizon  
**Global Candidate Recall**: 93.20%  
**Macro Candidate Recall**: 70.56%  

## 1. Per-Task Impact Plane Performance
| Task ID | Target Entity | Ground Truth | Candidate Pool | Hits | Pool Recall | Pool Precision | Fanout Summary |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TASK-1` | `php://OCA\Files\Controller\ApiController::getThumbnail` | 24 | 153 | 2 | 8.33% | 1.31% | True |
| `TASK-3` | `php://OCP\Files\Events\Node\NodeDeletedEvent::NodeDeletedEvent` | 18 | 19 | 10 | 55.56% | 52.63% | False |
| `TASK-2` | `php://OCP\Files\Node::getId` | 138 | 359 | 124 | 89.86% | 34.54% | True |
| `TASK-5` | `ts://apps/files/src/services/Recent.ts::Recent::getRecentSearch` | 3 | 71 | 3 | 100.00% | 4.23% | True |
| `TASK-4` | `php://OCP\IConfig::IConfig` | 538 | 1172 | 533 | 99.07% | 45.48% | True |

## 2. Silent Miss Analysis
- **Total Silent Misses**: 98
- **Root Cause Categorization**:
  1. `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH`: Peripheral consumer files beyond 2 hops of static edge traversal.
  2. `DYNAMIC_CONTAINER_LOOKUP`: Indirect dependency injection lookups not resolved statically.
