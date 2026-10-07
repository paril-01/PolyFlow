"""
Stage 13 Regression Tests: Source Adapter Truthfulness, Type Flow Derivation, and Determinism Integrity (Issues 24-36, 46, 47).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5"))

from rcir.adapters.nextcloud import NextcloudSourceDerivedAdapter
from rcir.retrieval.candidate_generator import CandidateRecord
from rcir.retrieval.evidence_vector import EvidenceVector, EvidenceVectorBuilder
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.types.php_type_flow import PHPTypeFlowAnalyzer, TypeResolutionConfidence


def test_discover_routes_rejects_wildcard_lines():
    """Issue 24 & 25: discover_routes must not match loose lines containing 'routes' and 'url'."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        routes_file = repo_root / "apps" / "files" / "appinfo" / "routes.php"
        routes_file.parent.mkdir(parents=True, exist_ok=True)

        # File with routes and url, but for an entirely different controller 'sharing'
        routes_content = """<?php
return [
    'routes' => [
        ['name' => 'sharing#show', 'url' => '/share', 'verb' => 'GET'],
    ]
];
"""
        routes_file.write_text(routes_content, encoding="utf-8")

        # Looking for ApiController
        matches = NextcloudSourceDerivedAdapter.discover_routes(
            repo_root, "apps/files/lib/Controller/ApiController.php", "getThumbnail"
        )
        assert len(matches) == 0, "Must not match routes for different controller"

        # Now add route specifically for ApiController
        valid_routes = """<?php
return [
    'routes' => [
        ['name' => 'api#getThumbnail', 'url' => '/api/thumb', 'verb' => 'GET'],
        ['name' => 'sharing#show', 'url' => '/share', 'verb' => 'GET'],
    ]
];
"""
        routes_file.write_text(valid_routes, encoding="utf-8")
        matches_valid = NextcloudSourceDerivedAdapter.discover_routes(
            repo_root, "apps/files/lib/Controller/ApiController.php", "getThumbnail"
        )
        assert len(matches_valid) == 1
        assert matches_valid[0].evidence_type == "route_to_controller"


def test_discover_event_dispatchers_separates_relations_and_deduplicates():
    """Issue 26 & 27: Separate event_dispatch from event_construct, and deduplicate."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)

        # File 1: Only instantiates event, does NOT dispatch
        f1 = repo_root / "src" / "ConstructorOnly.php"
        f1.parent.mkdir(parents=True, exist_ok=True)
        f1.write_text("<?php class A { public function run() { $e = new OrderEvent(); } }", encoding="utf-8")

        # File 2: Dispatches event
        f2 = repo_root / "src" / "Dispatcher.php"
        f2.write_text("<?php class B { public function run() { $this->dispatcher->dispatch(new OrderEvent()); } }", encoding="utf-8")

        from rcir.graph.canonical_graph import CanonicalEntityID, EntityKind
        node1 = CanonicalEntityID("repo", "php", "src/ConstructorOnly.php", "App", "", "A", EntityKind.CLASS)
        node2 = CanonicalEntityID("repo", "php", "src/Dispatcher.php", "App", "", "B", EntityKind.CLASS)
        nodes = {"php://A": node1, "php://B": node2}

        matches = NextcloudSourceDerivedAdapter.discover_event_dispatchers(repo_root, "App\\OrderEvent", nodes)
        assert len(matches) == 2

        types_by_file = {m.file_path: m.evidence_type for m in matches}
        assert types_by_file["src/ConstructorOnly.php"] == "event_construct"
        assert types_by_file["src/Dispatcher.php"] == "event_dispatch"


def test_discover_config_di_dynamic_resolution():
    """Issue 28: Discover config dynamically from CanonicalGraph nodes without static table."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        target = repo_root / "apps" / "test" / "lib" / "Service.php"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("<?php class Service { public function __construct(CustomConfig $c) {} }", encoding="utf-8")

        from rcir.graph.canonical_graph import CanonicalEntityID, EntityKind
        cfg_node = CanonicalEntityID("repo", "php", "apps/test/lib/CustomConfig.php", "App", "", "CustomConfig", EntityKind.CLASS)
        nodes = {"php://CustomConfig": cfg_node}

        cfg_file = repo_root / "apps" / "test" / "lib" / "CustomConfig.php"
        cfg_file.write_text("<?php class CustomConfig {}", encoding="utf-8")

        matches = NextcloudSourceDerivedAdapter.discover_config_di(repo_root, "apps/test/lib/Service.php", nodes)
        assert len(matches) == 1
        assert matches[0].file_path == "apps/test/lib/CustomConfig.php"


def test_evidence_vector_preserves_source_evidence_records():
    """Issue 30: EvidenceVector must preserve and serialize source_evidence_records."""
    ev = EvidenceVector(
        entity_id="php://test",
        file_path="src/test.php",
        source_evidence_records=[
            {"adapter": "nextcloud", "file": "apps/files/routes.php", "relation": "route", "confidence": 0.85}
        ]
    )
    d = ev.to_dict()
    assert "source_evidence_records" in d
    assert len(d["source_evidence_records"]) == 1
    assert d["source_evidence_records"][0]["relation"] == "route"

    cand = CandidateRecord(
        entity_id="php://cand",
        file_path="src/cand.php",
        source_evidence_records=[{"evidence": "ok"}]
    )
    spec = ChangeSpecification(operation=ChangeOperation.BEHAVIOR_CHANGE, requested_symbol="test")
    vec = EvidenceVectorBuilder.build_vector(cand, spec, set())
    assert len(vec.source_evidence_records) == 1
    assert vec.source_evidence_records[0]["evidence"] == "ok"


def test_php_type_flow_dynamic_return_type_derivation():
    """Issue 31: Derive method return types from source declarations without hardcoded seeds."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)

        # Create class file with typed return
        class_file = repo_root / "lib" / "public" / "Files" / "CustomFolder.php"
        class_file.parent.mkdir(parents=True, exist_ok=True)
        class_code = """<?php
namespace OCP\\Files;
use OCP\\Files\\Node;

class CustomFolder {
    public function getEntry(string $name): Node {
        return new Node();
    }
}
"""
        class_file.write_text(class_code, encoding="utf-8")

        analyzer = PHPTypeFlowAnalyzer(repo_root=repo_root)
        # Summaries initially empty
        assert ("OCP\\Files\\CustomFolder", "getEntry") not in analyzer.method_summaries

        # Test caller file that invokes $folder->getEntry('foo')->getId()
        caller_code = """<?php
namespace App;
use OCP\\Files\\CustomFolder;

class Consumer {
    public function run(CustomFolder $folder): void {
        $entry = $folder->getEntry("foo");
        $entry->getId();
    }
}
"""
        sites = analyzer.analyze_source_content(caller_code, file_path="Consumer.php")
        assert len(sites) >= 2
        entry_call = next(s for s in sites if s.receiver_expr == "$entry")
        assert "Node" in (entry_call.inferred_type or "")
        assert entry_call.confidence in (TypeResolutionConfidence.PROVEN_EXACT, TypeResolutionConfidence.INTERFACE_BOUND)


def test_evaluate_determinism_missing_config_raises():
    """Issue 47: evaluate_determinism must fail if selected_ranker_config.json is absent."""
    from evaluate_determinism import evaluate_determinism
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_env = MagicMock()
        mock_env.results_root = Path(tmp_dir) / "non_existent_results"
        mock_env.results_root.mkdir(parents=True, exist_ok=True)
        with patch("evaluate_determinism.get_default_environment", return_value=mock_env):
            with pytest.raises(FileNotFoundError):
                evaluate_determinism()
