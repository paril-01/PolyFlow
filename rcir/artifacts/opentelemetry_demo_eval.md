# RCIR Generalized Benchmark Report: opentelemetry-demo

- **Repository Path**: `C:\Users\Paril Rupani\OneDrive - Shri Vile Parle Kelavani Mandal\Desktop\project\PolyFlow\repos\opentelemetry-demo`
- **Execution Mode**: Blind / Zero-Prior-Knowledge
- **Zero-Cloud Enforcement**: PASS (Zero Network Sockets)
- **Total Scan Duration**: 11.78s

## 1. Graph Topology & Contract Extraction

| Metric | Count |
|---|---|
| Source Files Indexed | 160 |
| Total Graph Nodes | 611 |
| Total Extracted Edges | 1176 |
| Cross-Service Links | 31 |

## 2. Synthetic Mutation Benchmark (v7 §6.1.B)

- **Total Injected Mutations**: 5
- **Total Expected Call Sites**: 12
- **Total Call Sites Detected**: 9
- **Silent Misses (False Negatives)**: 3
- **Overall Mutation Recall**: **75.0%**
- **Overall Mutation Precision**: **100.0%**

| Mutation ID | Original Symbol | Target File | Expected | Detected | Recall | Precision |
|---|---|---|---|---|---|---|
| `mut_rpc_GetCart` | `GetCart` | `pb/demo.proto` | 3 | 2 | 66.7% | 100.0% |
| `mut_rpc_AddItem` | `AddItem` | `pb/demo.proto` | 2 | 1 | 50.0% | 100.0% |
| `mut_rpc_EmptyCart` | `EmptyCart` | `pb/demo.proto` | 3 | 2 | 66.7% | 100.0% |
| `mut_rpc_ListProducts` | `ListProducts` | `pb/demo.proto` | 2 | 2 | 100.0% | 100.0% |
| `mut_rpc_GetProduct` | `GetProduct` | `pb/demo.proto` | 2 | 2 | 100.0% | 100.0% |

## 3. End-to-End Dynamic Task Success (v7 §6.2)

- **Total Tasks Evaluated**: 5
- **Context Contract Coverage Rate**: **83.3%**
- **End-to-End Task Success Rate**: **60.0%**

| Task ID | Target Symbol | Expected Files | Contract Complete | Syntax Valid | Overall Success |
|---|---|---|---|---|---|
| `dyn_task_cartservice_additem` | `CartService.AddItem` | 3 | FAIL | PASS | **FAIL** |
| `dyn_task_productcatalogservice_listproducts` | `ProductCatalogService.ListProducts` | 3 | PASS | PASS | **PASS** |
| `dyn_task_recommendationservice_listrecommendations` | `RecommendationService.ListRecommendations` | 2 | PASS | PASS | **PASS** |
| `dyn_task_paymentservice_charge` | `PaymentService.Charge` | 2 | FAIL | PASS | **FAIL** |
| `dyn_task_checkoutservice_placeorder` | `CheckoutService.PlaceOrder` | 2 | PASS | PASS | **PASS** |
