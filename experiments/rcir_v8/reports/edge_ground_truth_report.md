# RCIR v8 — Edge-Level Ground Truth Report (PHASE 3)

**Status:** APPROVED  
**Target Repository:** Nextcloud Server (`da57df078d0808a7235a0177bd99d23c010b472e`)  
**Data Artifact:** `experiments/rcir_v8/ground_truth/edge_ground_truth.json`  
**Specification Reference:** `enhancemts - 01.md` (PHASE 3)

---

## 1. Ground Truth Principles & Schema

Under the v8 specification:
1. **File-level retrieval is never an edge metric.** File-level metrics measure whether a file path was present in the candidate list. Edge-level metrics measure whether a specific typed relationship $(u \xrightarrow{r} v)$ between two discrete entities was correctly extracted and resolved.
2. **Every edge must have line-level provenance and an evidence source.**
3. **No fabricated relations.** Every case is verified against real source code in the frozen repository.

### Ground Truth Schema (Phase 3)

```json
{
  "edge_id": "EDGE-GT-001",
  "category": "inheritance|imports|dependency_injection|route_to_controller|method_call|event_to_dispatcher|cross_stack_route|interface_implementation",
  "source": {
    "entity_id": "string",
    "file": "relative/path/to/file",
    "line": 0
  },
  "relationship": "inherits|imports|calls|implements",
  "target": {
    "entity_id": "string",
    "file": "relative/path/to/file",
    "line": 0
  },
  "evidence_source": "manual|compiler|runtime|historical_diff|generated_contract",
  "evidence_detail": "string",
  "verified": true
}
```

---

## 2. Verified Relation Cases

| Edge ID | Category | Source Entity & File:Line | Rel | Target Entity & File | Evidence Source & Detail |
|---|---|---|---|---|---|
| **EDGE-GT-001** | `inheritance` | `OCA\Files\Controller\ApiController`<br>`apps/files/lib/Controller/ApiController.php:56` | `inherits` | `OCP\AppFramework\Controller`<br>`lib/public/AppFramework/Controller.php` | `manual`<br>`class ApiController extends Controller` |
| **EDGE-GT-002** | `imports` | `apps/files/lib/Controller/ApiController.php`<br>`apps/files/lib/Controller/ApiController.php:14` | `imports` | `OCA\Files\Service\TagService`<br>`apps/files/lib/Service/TagService.php` | `manual`<br>`use OCA\Files\Service\TagService;` |
| **EDGE-GT-003** | `dependency_injection` | `OCA\Files\Controller\ApiController::__construct`<br>`apps/files/lib/Controller/ApiController.php:63` | `imports` | `OCA\Files\Service\TagService`<br>`apps/files/lib/Service/TagService.php` | `manual`<br>`private TagService $tagService` in constructor |
| **EDGE-GT-004** | `inheritance` | `OC\ServerContainer`<br>`lib/private/ServerContainer.php:24` | `inherits` | `OC\AppFramework\Utility\SimpleContainer`<br>`lib/private/AppFramework/Utility/SimpleContainer.php` | `manual`<br>`class ServerContainer extends SimpleContainer` |
| **EDGE-GT-005** | `interface_implementation` | `OC\Files\Node\File`<br>`lib/private/Files/Node/File.php:16` | `implements` | `OCP\Files\File`<br>`lib/public/Files/File.php` | `manual`<br>`class File extends Node implements \OCP\Files\File` |
| **EDGE-GT-006** | `route_to_controller` | `apps/files/appinfo/routes.php::Api#getThumbnail`<br>`apps/files/appinfo/routes.php:27` | `calls` | `OCA\Files\Controller\ApiController::getThumbnail`<br>`apps/files/lib/Controller/ApiController.php` | `manual`<br>`'name' => 'Api#getThumbnail'` route declaration |
| **EDGE-GT-007** | `method_call` | `OC\ServerContainer::registerAppContainer`<br>`lib/private/ServerContainer.php:57` | `calls` | `OC\AppFramework\App::buildAppNamespace`<br>`lib/private/AppFramework/App.php` | `manual`<br>`App::buildAppNamespace($appName)` call site |
| **EDGE-GT-008** | `event_to_dispatcher` | `OC\Files\Node\HookConnector::nodeDeleted`<br>`lib/private/Files/Node/HookConnector.php:126` | `calls` | `OCP\Files\Events\Node\NodeDeletedEvent::__construct`<br>`lib/public/Files/Events/Node/NodeDeletedEvent.php` | `manual`<br>`$event = new NodeDeletedEvent($node)` dispatch |
| **EDGE-GT-009** | `cross_stack_route` | `apps/files/src/services/Recent.ts::getRecentFiles`<br>`apps/files/src/services/Recent.ts:46` | `calls` | `apps/files/appinfo/routes.php::Api#getRecentFiles`<br>`apps/files/appinfo/routes.php:39` | `manual`<br>`getRecentSearch` hits `/api/v1/recent/` |
| **EDGE-GT-010** | `inheritance` | `OCP\Files\Events\Node\NodeDeletedEvent`<br>`lib/public/Files/Events/Node/NodeDeletedEvent.php:28` | `inherits` | `OCP\Files\Events\Node\NodeEvent`<br>`lib/public/Files/Events/Node/NodeEvent.php` | `manual`<br>`class NodeDeletedEvent extends NodeEvent` |

---

## 3. Evaluation of RCIR v7 Against Edge Ground Truth

When RCIR v7 is evaluated against these 10 verified edge relations:
- **True Positives (Exact Extraction):** 7 / 10
  - EDGE-GT-001 (inheritance: Controller) — PASSED
  - EDGE-GT-002 (imports: TagService) — PASSED
  - EDGE-GT-004 (inheritance: SimpleContainer) — PASSED
  - EDGE-GT-005 (implements: \OCP\Files\File) — PASSED
  - EDGE-GT-007 (calls: buildAppNamespace) — PASSED
  - EDGE-GT-008 (event: HookConnector -> NodeDeletedEvent) — PASSED
  - EDGE-GT-010 (inheritance: NodeEvent) — PASSED
- **Partial / Indirect Matches (Extracted as Inference or Heuristic):** 3 / 10
  - EDGE-GT-003 (DI resolution): TagService captured as import, but DI container type resolution flagged as static inference.
  - EDGE-GT-006 (route mapping): Route parsed by route scanner, but shortname convention `Api#getThumbnail` resolved via heuristic rather than symbol binding.
  - EDGE-GT-009 (cross-stack API call): URL string `/api/v1/recent/` matched by HTTP route analyzer, but direct AST call site absent (cross-language TypeScript $\to$ PHP boundary).
- **Silent Misses:** 0 / 10
- **Edge Extraction Recall:** **70.0% Exact** (100% reachability including inference).

---

## 4. Key Takeaways for RCIR v8 Architecture

1. **Static Inference Must Be Formally Separated from Static Exact:**
   The 3 partial matches demonstrate why ordinal confidence scores (1.0 vs 0.7) are not enough. Route conventions, DI container lookups, and HTTP endpoints represent different *classes* of edges, each requiring dedicated traversal and ranking policies.
2. **Boundary Contracts (Phase 6):**
   Edge GT-006 and GT-009 require explicit boundary layers:
   - `route_to_controller`
   - `frontend_to_route`
3. **Entity Resolution (Phase 5):**
   `Api#getThumbnail` requires resolving short-form controller aliases to full namespace FQCN (`OCA\Files\Controller\ApiController`).
