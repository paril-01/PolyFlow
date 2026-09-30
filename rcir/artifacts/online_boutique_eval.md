# RCIR Generalized Benchmark Report: microservices-demo

- **Repository Path**: `C:\Users\Paril Rupani\.gemini\antigravity-ide\brain\214c90a1-3995-48a9-a408-5acad77eafd5\scratch\microservices-demo`
- **Execution Mode**: Blind / Zero-Prior-Knowledge
- **Zero-Cloud Enforcement**: PASS (Zero Network Sockets)
- **Total Scan Duration**: 12.25s

## 1. Graph Topology & Contract Extraction

| Metric | Count |
|---|---|
| Source Files Indexed | 59 |
| Total Graph Nodes | 452 |
| Total Extracted Edges | 719 |
| Cross-Service Links | 1 |

## 2. Synthetic Mutation Benchmark (v7 §6.1.B)

- **Total Injected Mutations**: 5
- **Total Expected Call Sites**: 17
- **Total Call Sites Detected**: 16
- **Silent Misses (False Negatives)**: 1
- **Overall Mutation Recall**: **94.1%**
- **Overall Mutation Precision**: **88.9%**

| Mutation ID | Original Symbol | Target File | Expected | Detected | Recall | Precision |
|---|---|---|---|---|---|---|
| `mut_rpc_GetCart` | `GetCart` | `protos/demo.proto` | 4 | 4 | 100.0% | 100.0% |
| `mut_rpc_AddItem` | `AddItem` | `protos/demo.proto` | 3 | 3 | 100.0% | 100.0% |
| `mut_rpc_EmptyCart` | `EmptyCart` | `protos/demo.proto` | 4 | 4 | 100.0% | 100.0% |
| `mut_rpc_GetProduct` | `GetProduct` | `protos/demo.proto` | 3 | 3 | 100.0% | 75.0% |
| `mut_rpc_GetQuote` | `GetQuote` | `protos/demo.proto` | 3 | 2 | 66.7% | 66.7% |

## 3. End-to-End Dynamic Task Success (v7 §6.2)

- **Total Tasks Evaluated**: 5
- **Context Contract Coverage Rate**: **90.0%**
- **End-to-End Task Success Rate**: **80.0%**

| Task ID | Target Symbol | Expected Files | Contract Complete | Syntax Valid | Overall Success |
|---|---|---|---|---|---|
| `dyn_task_cartservice_additem` | `CartService.AddItem` | 4 | PASS | PASS | **PASS** |
| `dyn_task_recommendationservice_listrecommendations` | `RecommendationService.ListRecommendations` | 4 | PASS | PASS | **PASS** |
| `dyn_task_productcatalogservice_listproducts` | `ProductCatalogService.ListProducts` | 4 | PASS | PASS | **PASS** |
| `dyn_task_shippingservice_getquote` | `ShippingService.GetQuote` | 4 | FAIL | PASS | **FAIL** |
| `dyn_task_emailservice_sendorderconfirmation` | `EmailService.SendOrderConfirmation` | 4 | PASS | PASS | **PASS** |
