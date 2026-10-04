# RCIR v8.3 — Canonical Graph Fabric & Endpoint Normalization Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Graph Fabric**: 12,621 canonical entities | 143,225 typed edges  
**Architectural Component**: `CanonicalGraph`, `CanonicalEntityRegistry`, `ResolutionLedger`

## 1. Canonical Identity Architecture
RCIR v8.3 replaces unstructured file/string identifiers with strongly typed URIs:
- `php://<Namespace>\<Class>::<Method>`
- `ts://<ModulePath>::<Export>`

### Entity Registry Breakdown
- **Total Registered Entities**: 12621
- **Entity Kinds**:
  - `file`: 2761
  - `route`: 144
  - `method`: 4224
  - `class`: 4542
  - `interface`: 590
  - `trait`: 42
  - `config`: 318
- **Language Breakdown**:
  - `ts`: 656
  - `js`: 1918
  - `php`: 10047

## 2. Benchmark Target Canonical Degree Analysis
| Target Entity | Exact Incoming | Inferred Incoming | Exact Outgoing | Total Policy Degree | Degree Mode |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `php://OCP\IConfig` | 1,470 | 0 | 0 | 1,470 | High Degree |
| `php://OCP\Files\Node::getId` | 599 | 0 | 2 | 599 | High Degree |
| `php://OCA\Files\Controller\ApiController::getThumbnail` | 6 | 0 | 39 | 45 | Medium Degree |
| `php://OCP\Files\Events\Node\NodeDeletedEvent` | 10 | 0 | 0 | 10 | Medium Degree |
| `ts://apps/files/src/services/Recent.ts::getRecentSearch` | 1 | 0 | 79 | 80 | Medium Degree |

## 3. Resolution Ledger Summary
- **Total Edges Evaluated**: 143225
- **Resolution Status Breakdown**:
  - `static_exact`: 68451
  - `static_inference`: 74774
