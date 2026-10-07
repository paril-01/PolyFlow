"""
Stage 9: Source-Derived Discovery & No Hardcoded Answer Injection Tests.

Verifies:
1. Event dispatchers are discovered from actual source text/declarations.
2. Removing the event dispatch statement eliminates it from discovered candidates.
3. Unrelated events do not receive the dispatcher.
4. Route declarations are discovered by parsing routes.php; moving/removing changes discovery.
5. Config/DI dependencies are discovered from actual usage; removing references eliminates them.
6. Test files are discovered because of actual test code references, not basename magic.
7. Static AST test: No generic retrieval code contains fixed Nextcloud benchmark-answer paths.
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))

from rcir.adapters.nextcloud import NextcloudSourceDerivedAdapter
from rcir.entities.canonical import CanonicalEntityID, EntityKind


def test_synthetic_event_dispatcher_discovery_and_removal():
    """Verify event dispatcher is found when source dispatches, and absent when removed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        src_file = root / "src" / "Service" / "OrderService.php"
        src_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Source file dispatches OrderCreatedEvent
        src_file.write_text(
            "<?php\nclass OrderService {\n  public function create() {\n    $event = new OrderCreatedEvent();\n    $this->dispatcher->dispatchTyped($event);\n  }\n}\n",
            encoding="utf-8",
        )

        dummy_node = CanonicalEntityID(
            repository="test",
            language="php",
            file="src/Service/OrderService.php",
            namespace="App\\Service",
            owner_type="",
            symbol="OrderService",
            kind=EntityKind.CLASS,
        )
        nodes = {"php://App\\Service\\OrderService": dummy_node}

        matches = NextcloudSourceDerivedAdapter.discover_event_dispatchers(
            root, "App\\Events\\OrderCreatedEvent", nodes
        )
        assert len(matches) == 1
        assert matches[0].file_path == "src/Service/OrderService.php"
        assert matches[0].evidence_type == "event_dispatch"

        # 2. Removing dispatch declaration removes the candidate
        src_file.write_text(
            "<?php\nclass OrderService {\n  public function create() {\n    // Dispatch removed!\n  }\n}\n",
            encoding="utf-8",
        )
        matches_after_removal = NextcloudSourceDerivedAdapter.discover_event_dispatchers(
            root, "App\\Events\\OrderCreatedEvent", nodes
        )
        assert len(matches_after_removal) == 0

        # 3. Unrelated event does not discover the dispatcher
        src_file.write_text(
            "<?php\nclass OrderService {\n  public function create() {\n    new OrderCreatedEvent();\n  }\n}\n",
            encoding="utf-8",
        )
        unrelated_matches = NextcloudSourceDerivedAdapter.discover_event_dispatchers(
            root, "App\\Events\\InvoicePaidEvent", nodes
        )
        assert len(unrelated_matches) == 0


def test_synthetic_route_discovery():
    """Verify routes are discovered from routes.php declarations and react to changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        routes_file = root / "apps" / "files" / "appinfo" / "routes.php"
        routes_file.parent.mkdir(parents=True, exist_ok=True)

        routes_file.write_text(
            "<?php return ['routes' => [['name' => 'api#getThumbnail', 'url' => '/api/thumbnail']]];",
            encoding="utf-8",
        )

        matches = NextcloudSourceDerivedAdapter.discover_routes(
            root, "apps/files/lib/Controller/ApiController.php", "getThumbnail"
        )
        assert len(matches) == 1
        assert matches[0].file_path == "apps/files/appinfo/routes.php"
        assert matches[0].evidence_type == "route_to_controller"

        # Moving / removing routes declaration eliminates it
        routes_file.write_text("<?php return ['routes' => []];", encoding="utf-8")
        matches_empty = NextcloudSourceDerivedAdapter.discover_routes(
            root, "apps/files/lib/Controller/ApiController.php", "getThumbnail"
        )
        # Controller 'api' not in routes
        assert len(matches_empty) == 0


def test_synthetic_config_di_discovery():
    """Verify config/DI is discovered from actual usage in target file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        target = root / "apps" / "files" / "lib" / "Service" / "MyService.php"
        target.parent.mkdir(parents=True, exist_ok=True)

        # Create config file
        sys_cfg = root / "lib" / "private" / "SystemConfig.php"
        sys_cfg.parent.mkdir(parents=True, exist_ok=True)
        sys_cfg.write_text("<?php class SystemConfig {}", encoding="utf-8")

        # Target uses SystemConfig
        target.write_text("<?php class MyService { public function __construct(SystemConfig $c) {} }", encoding="utf-8")
        matches = NextcloudSourceDerivedAdapter.discover_config_di(root, "apps/files/lib/Service/MyService.php", {})
        assert len(matches) == 1
        assert matches[0].file_path == "lib/private/SystemConfig.php"

        # Target does NOT use config
        target.write_text("<?php class MyService { public function __construct() {} }", encoding="utf-8")
        matches_none = NextcloudSourceDerivedAdapter.discover_config_di(root, "apps/files/lib/Service/MyService.php", {})
        assert len(matches_none) == 0


def test_synthetic_test_file_discovery():
    """Verify test file is discovered only if test code actually references target."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        test_file = root / "tests" / "ApiControllerTest.php"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Test references ApiController
        test_file.write_text("<?php class ApiControllerTest extends TestCase { use ApiController; }", encoding="utf-8")
        matches = NextcloudSourceDerivedAdapter.discover_tests(
            root, "apps/files/lib/Controller/ApiController.php", "ApiController"
        )
        assert len(matches) == 1
        assert "ApiControllerTest.php" in matches[0].file_path

        # Unrelated test
        test_file.write_text("<?php class ApiControllerTest extends TestCase { // unreferenced }", encoding="utf-8")
        matches_unrelated = NextcloudSourceDerivedAdapter.discover_tests(
            root, "apps/files/lib/Controller/OtherController.php", "OtherController"
        )
        assert len(matches_unrelated) == 0


def test_static_ast_no_hardcoded_benchmark_answers_in_retrieval_runner():
    """
    Repository-level static test:
    Verify that retrieval_runner.py does NOT contain hardcoded Nextcloud benchmark answer paths.
    """
    retrieval_script = REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts" / "retrieval_runner.py"
    assert retrieval_script.exists()

    content = retrieval_script.read_text(encoding="utf-8")

    forbidden_paths = [
        "apps/files/appinfo/routes.php",
        "lib/private/Files/Node/HookConnector.php",
        "lib/private/Files/Node/Folder.php",
        "lib/private/Files/Node/Root.php",
        "lib/private/SystemConfig.php",
        "lib/private/AllConfig.php",
        "apps/files/lib/Service/UserConfig.php",
        "apps/files/tests/Controller/",
    ]

    for forbidden in forbidden_paths:
        assert forbidden not in content, (
            f"FORBIDDEN: retrieval_runner.py contains hardcoded benchmark answer path '{forbidden}'. "
            f"All discovery candidates must be derived dynamically from source or canonical graph."
        )
