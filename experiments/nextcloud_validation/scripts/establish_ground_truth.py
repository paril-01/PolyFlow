"""
Phase D: Independent Ground Truth Establishment for Nextcloud.

Establishes ground truth by INDEPENDENT source inspection — NOT from RCIR output.
Each ground truth edge is documented with:
- source and target
- edge type
- evidence source (how we know this edge exists)
- verification method

These cases are selected to be adversarial (Section 11):
- Framework indirection (DI container, controller routing)
- Inheritance chains
- Interface implementations
- Event listeners
- Dynamic configuration
- Frontend/backend boundaries
- Trait usage
"""

import json
from pathlib import Path

# Ground truth edges established by manual source inspection of Nextcloud.
# Each edge represents a REAL dependency relationship verified by reading the source code.

GROUND_TRUTH_EDGES = [
    # ─── CASE 1: Controller extends framework base class ─────────
    {
        "case_id": "GT-001",
        "category": "inheritance",
        "source": "apps/files/lib/Controller/ApiController.php::OCA\\Files\\Controller\\ApiController",
        "target": "OCP\\AppFramework\\Controller",
        "edge_type": "inherits",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "Line: 'class ApiController extends Controller' in apps/files/lib/Controller/ApiController.php",
        "verification_method": "grep -n 'class ApiController extends Controller' apps/files/lib/Controller/ApiController.php",
        "difficulty": "easy",
    },
    # ─── CASE 2: Use statement (import) ──────────────────────────
    {
        "case_id": "GT-002",
        "category": "imports",
        "source": "apps/files/lib/Controller/ApiController.php",
        "target": "OCA\\Files\\Service\\TagService",
        "edge_type": "imports",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "Line: 'use OCA\\Files\\Service\\TagService;' in apps/files/lib/Controller/ApiController.php",
        "verification_method": "grep -n 'use OCA.*TagService' apps/files/lib/Controller/ApiController.php",
        "difficulty": "easy",
    },
    # ─── CASE 3: DI Constructor type hint dependency ─────────────
    {
        "case_id": "GT-003",
        "category": "dependency_injection",
        "source": "apps/files/lib/Controller/ApiController.php::OCA\\Files\\Controller\\ApiController::__construct",
        "target": "OCA\\Files\\Service\\TagService",
        "edge_type": "imports",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "Constructor parameter: 'private TagService $tagService' in ApiController.__construct()",
        "verification_method": "grep -n 'TagService' apps/files/lib/Controller/ApiController.php",
        "difficulty": "medium",
        "notes": "DI container resolves TagService at runtime. RCIR must detect the type hint.",
    },
    # ─── CASE 4: ServerContainer extends SimpleContainer ─────────
    {
        "case_id": "GT-004",
        "category": "inheritance",
        "source": "lib/private/ServerContainer.php::OC\\ServerContainer",
        "target": "OC\\AppFramework\\Utility\\SimpleContainer",
        "edge_type": "inherits",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "Line: 'class ServerContainer extends SimpleContainer' in lib/private/ServerContainer.php",
        "verification_method": "grep -n 'extends SimpleContainer' lib/private/ServerContainer.php",
        "difficulty": "easy",
    },
    # ─── CASE 5: Interface implementation ────────────────────────
    {
        "case_id": "GT-005",
        "category": "interface_implementation",
        "source": "lib/private/Files/Node/File.php",
        "target": "OCP\\Files\\File",
        "edge_type": "inherits",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "Class File extends Node implements \\OCP\\Files\\File",
        "verification_method": "grep -n 'implements' lib/private/Files/Node/File.php",
        "difficulty": "medium",
        "notes": "Tests interface-to-implementation resolution across OC\\Files and OCP\\Files namespaces",
    },
    # ─── CASE 6: Route -> Controller mapping ─────────────────────
    {
        "case_id": "GT-006",
        "category": "route",
        "source": "apps/files/appinfo/routes.php",
        "target": "OCA\\Files\\Controller\\ApiController::getThumbnail",
        "edge_type": "calls",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "'name' => 'Api#getThumbnail', 'url' => '/api/v1/thumbnail/{x}/{y}/{file}'",
        "verification_method": "grep -n 'getThumbnail' apps/files/appinfo/routes.php",
        "difficulty": "hard",
        "notes": "Nextcloud routes use 'ControllerShortName#method' convention. RCIR must resolve 'Api#getThumbnail' to ApiController::getThumbnail. This is framework indirection.",
    },
    # ─── CASE 7: $this->method() call ────────────────────────────
    {
        "case_id": "GT-007",
        "category": "method_call",
        "source": "lib/private/ServerContainer.php::OC\\ServerContainer::__construct",
        "target": "OC\\ServerContainer::registerNamespace",
        "edge_type": "calls",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "$this->registerNamespace() called within ServerContainer methods",
        "verification_method": "grep -n 'this->registerNamespace' lib/private/ServerContainer.php",
        "difficulty": "easy",
    },
    # ─── CASE 8: Static method call across classes ───────────────
    {
        "case_id": "GT-008",
        "category": "static_call",
        "source": "lib/private/ServerContainer.php::OC\\ServerContainer::registerAppContainer",
        "target": "OC\\AppFramework\\App::buildAppNamespace",
        "edge_type": "calls",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "App::buildAppNamespace($appName) called in registerAppContainer()",
        "verification_method": "grep -n 'App::buildAppNamespace' lib/private/ServerContainer.php",
        "difficulty": "medium",
    },
    # ─── CASE 9: Event dispatch ──────────────────────────────────
    {
        "case_id": "GT-009",
        "category": "event",
        "source": "lib/private/Files/Node/Node.php",
        "target": "OCP\\Files\\Events\\Node\\NodeDeletedEvent",
        "edge_type": "calls",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "Event dispatched when a file/folder is deleted",
        "verification_method": "grep -rn 'NodeDeletedEvent' lib/private/Files/",
        "difficulty": "hard",
        "notes": "Event dispatch + listener registration is a common source of silent misses. The event class is in OCP, dispatched from OC, listened to in apps.",
    },
    # ─── CASE 10: Frontend -> Backend API boundary ───────────────
    {
        "case_id": "GT-010",
        "category": "frontend_backend",
        "source": "apps/files/src/services/Files.ts",
        "target": "/apps/files/api/v1/recent/",
        "edge_type": "calls",
        "evidence_source": "manual_source_inspection",
        "evidence_detail": "TypeScript frontend calls PHP backend OCS API endpoint for recent files",
        "verification_method": "grep -rn 'recent' apps/files/src/services/",
        "difficulty": "very_hard",
        "notes": "Cross-language boundary: TypeScript -> HTTP -> PHP. RCIR must detect the URL string in JS/TS and match it to the PHP route.",
    },
]


def main():
    output_dir = Path(__file__).resolve().parent.parent / "ground_truth"

    # Save ground truth
    gt_path = output_dir / "ground_truth_edges.json"
    gt_path.write_text(json.dumps(GROUND_TRUTH_EDGES, indent=2), encoding="utf-8")
    print(f"Ground truth saved to: {gt_path}")
    print(f"Total ground truth edges: {len(GROUND_TRUTH_EDGES)}")

    # Summary by category
    categories = {}
    for edge in GROUND_TRUTH_EDGES:
        cat = edge["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nBy category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:30s}  {count}")

    # Summary by difficulty
    difficulties = {}
    for edge in GROUND_TRUTH_EDGES:
        d = edge.get("difficulty", "unknown")
        difficulties[d] = difficulties.get(d, 0) + 1

    print("\nBy difficulty:")
    for d, count in sorted(difficulties.items()):
        print(f"  {d:30s}  {count}")


if __name__ == "__main__":
    main()
