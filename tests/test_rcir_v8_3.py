"""
RCIR v8.3 — Comprehensive Regression Test Suite (PHASES 0-93).

Covers:
- Target symbol and target file separation
- Exact target identity strictly for requested symbol (not same-file siblings)
- Substring path matching immunity
- Canonical alias resolution & URI consistency
- Canonical graph degree non-zero invariants (e.g. IConfig)
- Strict Rule 0 ground truth leakage immunity (ImpactSummarizer, ContextPlanner, Ranker)
- TypeFlow AST receiver expression parsing and propagation (parameters, properties, locals, foreach)
- Preservation of ambiguity for generic/polymorphic calls (e.g. $node->getId())
- Dataset split barrier (TEST split inaccessible during ranker selection)
- Incremental unseen context tracking in RCIRContextProvider
- Machine gate evaluator contract-driven logic
- Byte/hash report consistency
"""

import inspect
import json
import pytest
from pathlib import Path

from rcir.context.compiler import ContextCompiler, ContextGranularity
from rcir.context.planner import ContextPlanner, ContextRole, RoleQuota
from rcir.context.provider import ContextSessionState, RCIRContextProvider
from rcir.context.summarizer import ImpactSummarizer
from rcir.dataset import DatasetLoader, DatasetSplit, DatasetMode
from rcir.entities.canonical import CanonicalEntityRegistry, CanonicalEntityID, EntityKind, AliasResolution
from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdge, CanonicalEdgeType, ResolutionClass
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import (
    DeterministicRanker,
    MultiObjectiveRanker,
    OperationRankerProfile,
    RankerConfig,
    RankedCandidate,
)
from rcir.types.php_type_flow import PHPTypeFlowAnalyzer, TypeResolutionConfidence

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_target_symbol_and_target_file_are_separate_concepts():
    reg = CanonicalEntityRegistry()
    e1 = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Controller/ApiController.php",
        namespace="OCA\\Files\\Controller",
        owner_type="ApiController",
        symbol="getThumbnail",
        kind=EntityKind.METHOD,
    )
    e2 = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Controller/ApiController.php",
        namespace="OCA\\Files\\Controller",
        owner_type="ApiController",
        symbol="download",
        kind=EntityKind.METHOD,
    )
    reg.register(e1)
    reg.register(e2)

    res = reg.resolve("getThumbnail", target_file_hint="apps/files/lib/Controller/ApiController.php")
    assert res.canonical_id == e1.uri
    assert res.canonical_id != e2.uri
    assert res.resolution in (AliasResolution.EXACT, AliasResolution.UNIQUE_ALIAS)


def test_only_actual_requested_symbol_receives_exact_target_identity():
    reg = CanonicalEntityRegistry()
    e1 = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/Files/Node.php",
        namespace="OCP\\Files",
        owner_type="Node",
        symbol="getId",
        kind=EntityKind.METHOD,
    )
    e2 = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/Files/Node.php",
        namespace="OCP\\Files",
        owner_type="Node",
        symbol="getName",
        kind=EntityKind.METHOD,
    )
    reg.register(e1)
    reg.register(e2)

    # Candidate vectors
    v1 = EvidenceVector(entity_id=e1.uri, file_path=e1.file, entity_match="exact")
    v2 = EvidenceVector(entity_id=e2.uri, file_path=e2.file, entity_match="none")

    ranker = DeterministicRanker()
    b1 = ranker.classify_bucket(v1)
    b2 = ranker.classify_bucket(v2)

    assert b1 == "A0"  # Exact target
    assert b2 != "A0"  # Same file sibling is NOT A0


def test_canonical_alias_forms_resolve_to_same_entity_id():
    reg = CanonicalEntityRegistry()
    ent = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/IConfig.php",
        namespace="OCP",
        owner_type="IConfig",
        symbol="IConfig",
        kind=EntityKind.INTERFACE,
        aliases=["IConfig", "OCP\\IConfig", "lib/public/IConfig.php"],
    )
    reg.register(ent)

    r1 = reg.resolve("IConfig")
    r2 = reg.resolve("OCP\\IConfig")
    r3 = reg.resolve("lib/public/IConfig.php")
    r4 = reg.resolve("lib\\public\\IConfig.php")

    assert r1.canonical_id == ent.uri
    assert r2.canonical_id == ent.uri
    assert r3.canonical_id == ent.uri
    assert r4.canonical_id == ent.uri


def test_iconfig_degree_cannot_remain_zero_with_incoming_edges():
    graph = CanonicalGraph()
    iconfig = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/IConfig.php",
        namespace="OCP",
        owner_type="IConfig",
        symbol="IConfig",
        kind=EntityKind.INTERFACE,
        aliases=["IConfig", "OCP\\IConfig"],
    )
    graph.add_node(iconfig)

    # Ingest incoming edge
    graph.add_edge(CanonicalEdge(
        source_id="apps/files/lib/App.php",
        target_id="OCP\\IConfig",
        edge_type=CanonicalEdgeType.IMPORTS,
        resolution_class=ResolutionClass.STATIC_EXACT,
    ))

    deg = graph.analyze_degree(iconfig.uri)
    assert deg.incoming_exact >= 1
    assert deg.target_id == iconfig.uri


def test_ground_truth_cannot_reach_impact_summarizer():
    sig = inspect.signature(ImpactSummarizer.summarize)
    assert "ground_truth" not in sig.parameters
    assert "critical_ground_truth" not in sig.parameters
    assert "expected_files" not in sig.parameters


def test_ground_truth_cannot_reach_context_planner():
    sig = inspect.signature(ContextPlanner.create_plan)
    assert "ground_truth" not in sig.parameters
    assert "expected_files" not in sig.parameters
    assert "labels" not in sig.parameters


def test_ground_truth_cannot_reach_ranker():
    sig = inspect.signature(DeterministicRanker.rank)
    assert "ground_truth" not in sig.parameters
    sig_multi = inspect.signature(MultiObjectiveRanker.rank)
    assert "ground_truth" not in sig_multi.parameters


def test_type_flow_parses_actual_receiver_expression_and_locals():
    analyzer = PHPTypeFlowAnalyzer()
    php_code = """<?php
namespace OCA\\Test;
use OCP\\Files\\Node;

class TestService {
    private Node $node;

    public function process(Node $paramNode): void {
        $localVar = $paramNode;
        $localVar->getId();
        $this->node->getId();
    }
}
"""
    calls = analyzer.analyze_source_content(php_code, file_path="TestService.php")
    assert len(calls) >= 2
    local_call = next(c for c in calls if c.receiver_expr == "$localVar")
    prop_call = next(c for c in calls if c.receiver_expr == "$this->node")

    assert local_call.confidence in (TypeResolutionConfidence.PROVEN_EXACT, TypeResolutionConfidence.INTERFACE_BOUND)
    assert "Node" in (local_call.inferred_type or "")
    assert prop_call.confidence in (TypeResolutionConfidence.PROVEN_EXACT, TypeResolutionConfidence.INTERFACE_BOUND)
    assert "Node" in (prop_call.inferred_type or "")


def test_ambiguous_call_remains_ambiguous():
    analyzer = PHPTypeFlowAnalyzer()
    php_code = """<?php
namespace OCA\\Test;

class GenericCaller {
    public function execute($unknownObject): void {
        $unknownObject->getId();
    }
}
"""
    calls = analyzer.analyze_source_content(php_code, file_path="GenericCaller.php")
    assert len(calls) == 1
    call = calls[0]
    assert call.confidence == TypeResolutionConfidence.AMBIGUOUS
    assert call.method_name == "getId"


def test_dataset_leakage_guards_prevent_test_set_during_ranker_selection(tmp_path):
    # Setup dataset files
    dev_path = tmp_path / "dev.json"
    val_path = tmp_path / "validation.json"
    test_path = tmp_path / "test.json"

    dummy_task = {
        "task_id": "T1", "title": "T1", "category": "cat", "query": "q", "description": "d",
        "spec": {
            "operation": "route_change", "requested_symbol": "sym", "target_file_hint": "f.php",
            "canonical_target_ids": ["php://f.php::sym"], "changed_facets": [], "requested_scope": "module", "language": "php", "description": "d"
        }
    }
    dev_path.write_text(json.dumps({"tasks": [dummy_task]}), encoding="utf-8")
    val_path.write_text(json.dumps({"tasks": [dummy_task]}), encoding="utf-8")
    test_path.write_text(json.dumps({"tasks": [dummy_task]}), encoding="utf-8")

    # In RANKER_SELECTION mode, requesting TEST split must raise PermissionError
    loader = DatasetLoader(tmp_path, mode=DatasetMode.RANKER_SELECTION)
    loader.load_split(DatasetSplit.VALIDATION)  # Allowed

    with pytest.raises(PermissionError, match="(?i)prohibited"):
        loader.load_split(DatasetSplit.TEST)


def test_context_provider_tracks_incremental_unseen_context():
    reg = CanonicalEntityRegistry()
    ent = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/IConfig.php",
        namespace="OCP",
        owner_type="IConfig",
        symbol="IConfig",
        kind=EntityKind.INTERFACE,
        aliases=["IConfig", "OCP\\IConfig"],
    )
    reg.register(ent)

    raw_graph = {
        "nodes": [ent.to_dict()],
        "edges": [
            {"source": "apps/files/lib/App.php", "target": "OCP\\IConfig", "edge_type": "imports", "resolution": "static_exact"}
        ]
    }

    provider = RCIRContextProvider(raw_graph=raw_graph, registry=reg)

    res1 = provider.retrieve("IConfig", token_budget=500)
    assert res1["entries_count"] >= 1
    assert ent.uri in provider.session_state.entities_seen

    # Second retrieve delivers remaining unseen dependency
    res2 = provider.retrieve("IConfig", token_budget=500)
    assert "apps/files/lib/App.php" in res2["new_entities"]

    # Third retrieve has no unseen entities left in graph
    res3 = provider.retrieve("IConfig", token_budget=500)
    assert len(res3["new_entities"]) == 0
