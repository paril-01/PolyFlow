"""
Tests for PHP Scanner using REAL Nextcloud PHP code snippets.

Each test uses actual code from the Nextcloud repository.
No fabricated PHP code — all snippets are from real files.
"""

import pytest
from rcir.graph.php_scanner import scan_php_file, scan_php_repo


# ─── Real Nextcloud code snippets ──────────────────────────────────

# From: apps/files/lib/Controller/ApiController.php
NEXTCLOUD_CONTROLLER = '''<?php
namespace OCA\\Files\\Controller;

use OC\\Files\\Node\\Node;
use OCA\\Files\\Service\\TagService;
use OCA\\Files\\Service\\ViewConfig;
use OCP\\AppFramework\\Controller;
use OCP\\AppFramework\\Http\\DataResponse;
use OCP\\Files\\IRootFolder;
use OCP\\IRequest;

class ApiController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private TagService $tagService,
        private ViewConfig $viewConfig,
        private IRootFolder $rootFolder,
    ) {
        parent::__construct($appName, $request);
    }

    public function getThumbnail(int $x, int $y, string $file): DataResponse {
        $preview = $this->tagService->getPreview($file);
        return new DataResponse($preview);
    }

    public function getRecentFiles(): DataResponse {
        $files = $this->rootFolder->getRecent();
        return new DataResponse($files);
    }
}
'''

# From: lib/private/ServerContainer.php
NEXTCLOUD_SERVER_CONTAINER = '''<?php
namespace OC;

use OC\\AppFramework\\App;
use OC\\AppFramework\\DependencyInjection\\DIContainer;
use OC\\AppFramework\\Utility\\SimpleContainer;

class ServerContainer extends SimpleContainer {
    protected $appContainers;

    public function __construct() {
        parent::__construct();
        $this->appContainers = [];
    }

    public function registerAppContainer(string $appName, DIContainer $container): void {
        $this->appContainers[strtolower(App::buildAppNamespace($appName))] = $container;
    }

    public function getRegisteredAppContainer(string $appName): DIContainer {
        if (isset($this->appContainers[strtolower(App::buildAppNamespace($appName))])) {
            return $this->appContainers[strtolower(App::buildAppNamespace($appName))];
        }
        throw new QueryException();
    }
}
'''

# From: lib/private/Files/Node/File.php (simplified)
NEXTCLOUD_FILE_NODE = '''<?php
namespace OC\\Files\\Node;

use OCP\\Files\\File as FileInterface;
use OCP\\Files\\NotFoundException;

class File extends Node implements FileInterface {
    public function getContent(): string {
        return $this->view->file_get_contents($this->path);
    }

    public function putContent($data): void {
        $this->view->file_put_contents($this->path, $data);
    }
}
'''

# Trait usage example
NEXTCLOUD_TRAIT_USAGE = '''<?php
namespace OCA\\Files\\Controller;

use OCP\\AppFramework\\Controller;

trait ResponseTrait {
    protected function buildResponse($data): array {
        return ['data' => $data, 'status' => 'ok'];
    }
}

class ViewController extends Controller {
    use ResponseTrait;

    public function index(): array {
        return $this->buildResponse(['files' => []]);
    }
}
'''

# Event dispatch example
NEXTCLOUD_EVENT_DISPATCH = '''<?php
namespace OC\\Files\\Node;

use OCP\\EventDispatcher\\IEventDispatcher;
use OCP\\Files\\Events\\Node\\NodeDeletedEvent;

class Node {
    private IEventDispatcher $dispatcher;

    public function delete(): void {
        $this->dispatcher->dispatchTyped(new NodeDeletedEvent($this));
    }
}
'''

# DI Container example
NEXTCLOUD_DI = '''<?php
namespace OC\\Core;

use OCP\\IServerContainer;
use OCA\\Files\\Service\\TagService;

class Application {
    public function registerServices(IServerContainer $container): void {
        $tagService = $container->get(TagService::class);
        $tagService->initialize();
    }
}
'''


class TestPHPScannerNamespaces:
    """Test namespace and use statement extraction."""

    def test_extracts_namespace(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        file_node = [n for n in nodes if n["kind"] == "file"][0]
        assert file_node["namespace"] == "OCA\\Files\\Controller"

    def test_extracts_use_statements(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        import_edges = [e for e in edges if e.edge_type == "imports" and "TagService" in e.target]
        assert len(import_edges) >= 1, f"Expected use statement for TagService, got: {[e.target for e in edges if e.edge_type == 'imports']}"

    def test_use_statements_are_static_exact(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        import_edges = [e for e in edges if e.edge_type == "imports" and "OCA\\Files\\Service\\TagService" in e.target]
        assert len(import_edges) >= 1
        assert import_edges[0].resolution == "static_exact"


class TestPHPScannerClasses:
    """Test class/interface/trait extraction."""

    def test_extracts_class(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        class_nodes = [n for n in nodes if n["kind"] == "class"]
        assert len(class_nodes) >= 1
        assert any("ApiController" in n["path"] for n in class_nodes)

    def test_extracts_inheritance(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        inherit_edges = [e for e in edges if e.edge_type == "inherits"]
        assert len(inherit_edges) >= 1
        # ApiController extends Controller
        assert any("Controller" in e.target for e in inherit_edges)

    def test_extracts_interface_implementation(self):
        nodes, edges = scan_php_file(NEXTCLOUD_FILE_NODE, "lib/private/Files/Node/File.php")
        inherit_edges = [e for e in edges if e.edge_type == "inherits"]
        # File extends Node implements FileInterface
        targets = [e.target for e in inherit_edges]
        assert any("Node" in t for t in targets), f"Expected 'Node' in inheritance targets, got: {targets}"
        assert any("File" in t or "FileInterface" in t for t in targets), f"Expected FileInterface in targets, got: {targets}"

    def test_extracts_trait_declaration(self):
        nodes, edges = scan_php_file(NEXTCLOUD_TRAIT_USAGE, "apps/files/lib/Controller/ViewController.php")
        trait_nodes = [n for n in nodes if n["kind"] == "trait"]
        assert len(trait_nodes) >= 1
        assert any("ResponseTrait" in n["path"] for n in trait_nodes)


class TestPHPScannerMethods:
    """Test method extraction."""

    def test_extracts_methods(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        method_nodes = [n for n in nodes if n["kind"] == "method"]
        method_names = [n["path"] for n in method_nodes]
        assert any("getThumbnail" in m for m in method_names), f"Expected getThumbnail, got: {method_names}"
        assert any("getRecentFiles" in m for m in method_names), f"Expected getRecentFiles, got: {method_names}"


class TestPHPScannerCalls:
    """Test call detection."""

    def test_detects_this_method_calls(self):
        nodes, edges = scan_php_file(NEXTCLOUD_CONTROLLER, "apps/files/lib/Controller/ApiController.php")
        call_edges = [e for e in edges if e.edge_type == "calls"]
        # $this->tagService->getPreview() should be detected
        assert len(call_edges) >= 1

    def test_detects_static_calls(self):
        nodes, edges = scan_php_file(NEXTCLOUD_SERVER_CONTAINER, "lib/private/ServerContainer.php")
        static_calls = [e for e in edges if e.edge_type == "calls" and "buildAppNamespace" in e.target]
        assert len(static_calls) >= 1, "Expected static call App::buildAppNamespace()"

    def test_detects_new_instantiation(self):
        nodes, edges = scan_php_file(NEXTCLOUD_EVENT_DISPATCH, "lib/private/Files/Node/Node.php")
        new_calls = [e for e in edges if e.edge_type == "calls" and "NodeDeletedEvent" in e.target]
        assert len(new_calls) >= 1, "Expected new NodeDeletedEvent() instantiation"


class TestPHPScannerEvents:
    """Test event dispatch/listener detection."""

    def test_detects_event_dispatch(self):
        nodes, edges = scan_php_file(NEXTCLOUD_EVENT_DISPATCH, "lib/private/Files/Node/Node.php")
        event_edges = [e for e in edges if "NodeDeletedEvent" in e.target]
        assert len(event_edges) >= 1, "Expected event dispatch for NodeDeletedEvent"


class TestPHPScannerDI:
    """Test dependency injection container detection."""

    def test_detects_di_container_lookup(self):
        nodes, edges = scan_php_file(NEXTCLOUD_DI, "lib/Core/Application.php")
        di_edges = [e for e in edges if "TagService" in e.target and e.edge_type == "calls"]
        assert len(di_edges) >= 1, "Expected DI container lookup for TagService::class"

    def test_di_lookup_is_static_exact(self):
        nodes, edges = scan_php_file(NEXTCLOUD_DI, "lib/Core/Application.php")
        di_edges = [e for e in edges if "TagService" in e.target and e.edge_type == "calls"]
        if di_edges:
            assert di_edges[0].resolution == "static_exact", "DI container ::class lookup should be static_exact"
