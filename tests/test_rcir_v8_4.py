"""
RCIR v8.4 Test Suite — Canonical Graph, Type Flow, Token Budget, and Determinism.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rcir.context.compiler import ContextCompiler
from rcir.context.planner import ContextPlanner
from rcir.context.tokenizer import get_default_token_counter
from rcir.entities.canonical import (
    AliasResolution,
    CanonicalEntityID,
    CanonicalEntityRegistry,
    EntityKind,
)
from rcir.graph.canonical_graph import (
    CanonicalEdge,
    CanonicalEdgeType,
    CanonicalGraph,
    ResolutionClass,
    ResolutionLedger,
)
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import (
    DeterministicRanker,
    MultiObjectiveRanker,
    OperationRankerProfile,
    RankedCandidate,
    RankerConfig,
    ScoreBreakdown,
)
from rcir.types.php_type_flow import (
    PHPTypeFlowAnalyzer,
    TypeResolutionConfidence,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_canonical_entity_uri_kind_formatting_and_parsing():
    # 1. Interface
    e_iface = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/IConfig.php",
        namespace="OCP",
        owner_type="IConfig",
        symbol="IConfig",
        kind=EntityKind.INTERFACE,
    )
    assert e_iface.uri == "php://OCP\\IConfig"
    parsed_iface = CanonicalEntityID.from_uri(e_iface.uri)
    assert parsed_iface.namespace == "OCP"
    assert parsed_iface.symbol == "IConfig"

    # 2. Method
    e_method = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Controller/ApiController.php",
        namespace="OCA\\Files\\Controller",
        owner_type="ApiController",
        symbol="getThumbnail",
        kind=EntityKind.METHOD,
    )
    assert e_method.uri == "php://OCA\\Files\\Controller\\ApiController::getThumbnail"
    parsed_method = CanonicalEntityID.from_uri(e_method.uri)
    assert parsed_method.symbol == "getThumbnail"
    assert parsed_method.owner_type == "ApiController"

    # 3. File
    e_file = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Controller/ApiController.php",
        namespace="",
        owner_type="",
        symbol="ApiController",
        kind=EntityKind.FILE,
    )
    assert e_file.uri == "php://apps/files/lib/Controller/ApiController.php"


def test_canonical_registry_disambiguates_file_and_class():
    reg = CanonicalEntityRegistry()

    # File entity
    f_ent = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Helper.php",
        namespace="",
        owner_type="",
        symbol="Helper",
        kind=EntityKind.FILE,
    )
    # Class entity in same file
    c_ent = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Helper.php",
        namespace="OCA\\Files",
        owner_type="Helper",
        symbol="Helper",
        kind=EntityKind.CLASS,
    )
    # Method entity in same class
    m_ent = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="apps/files/lib/Helper.php",
        namespace="OCA\\Files",
        owner_type="Helper",
        symbol="formatFileInfo",
        kind=EntityKind.METHOD,
    )

    reg.register(f_ent)
    reg.register(c_ent)
    reg.register(m_ent)

    # Resolving the file path resolves to the FILE entity
    res_file = reg.resolve("apps/files/lib/Helper.php")
    assert res_file.canonical_id == f_ent.uri
    assert res_file.resolution == AliasResolution.UNIQUE_ALIAS

    # Resolving the class name resolves to the CLASS entity
    res_class = reg.resolve("OCA\\Files\\Helper")
    assert res_class.canonical_id == c_ent.uri

    # Resolving method resolves to METHOD entity
    res_method = reg.resolve("formatFileInfo", target_file_hint="apps/files/lib/Helper.php")
    assert res_method.canonical_id == m_ent.uri


def test_resolution_ledger_invariant():
    ledger = ResolutionLedger()
    ledger.record("php://A", "php://B", ResolutionClass.STATIC_EXACT)
    ledger.record("php://A", "php://C", ResolutionClass.STATIC_INFERENCE)
    ledger.record("php://A", "php://D", ResolutionClass.AMBIGUOUS)
    ledger.record("php://B", "php://E", ResolutionClass.DYNAMIC_UNRESOLVED)
    ledger.record("php://B", "php://F", ResolutionClass.UNSUPPORTED)
    ledger.record("php://C", "php://G", ResolutionClass.NOT_ANALYZED)

    data = ledger.to_dict()
    assert data["total_evaluated"] == 6
    summary = data["summary"]
    assert (
        summary["static_exact"]
        + summary["static_inference"]
        + summary["ambiguous"]
        + summary["dynamic_unresolved"]
        + summary["unsupported"]
        + summary["not_analyzed"]
        == data["total_evaluated"]
    )


def test_canonical_graph_normalizes_edge_endpoints():
    reg = CanonicalEntityRegistry()
    cg = CanonicalGraph(registry=reg)

    cls_id = CanonicalEntityID(
        repository="nextcloud-server",
        language="php",
        file="lib/public/IConfig.php",
        namespace="OCP",
        owner_type="IConfig",
        symbol="IConfig",
        kind=EntityKind.INTERFACE,
        aliases=["IConfig", "OCP\\IConfig"],
    )
    reg.register(cls_id)

    # Add edge using raw alias "OCP\IConfig"
    edge = CanonicalEdge(
        source_id="apps/files/lib/App.php",
        target_id="OCP\\IConfig",
        edge_type=CanonicalEdgeType.IMPORTS,
        resolution_class=ResolutionClass.STATIC_EXACT,
    )
    cg.add_edge(edge)

    # Edge endpoints must be canonical
    assert edge.target_id == "php://OCP\\IConfig"
    # Raw target preserved in evidence
    assert edge.evidence["raw_target"] == "OCP\\IConfig"

    # Edge query works via canonical ID
    incoming = cg.get_incoming_edges("php://OCP\\IConfig")
    assert len(incoming) == 1
    assert incoming[0].target_id == "php://OCP\\IConfig"


def test_structured_lexical_php_type_flow():
    code = """<?php
namespace OCA\\Files\\Controller;

use OCP\\IConfig;
use OCP\\AppFramework\\Http\\DataResponse;

class ApiController {
    /** @var IConfig */
    private $config;

    public function __construct(IConfig $config) {
        $this->config = $config;
    }

    public function getThumbnail(): DataResponse {
        $cfg = $this->config;
        $val = $cfg->getUserValue("files", "max_size", "1024");
        return new DataResponse(["size" => $val]);
    }
}
"""
    analyzer = PHPTypeFlowAnalyzer(repo_root=REPO_ROOT)
    call_sites = analyzer.analyze_source_content(code, file_path="apps/files/lib/Controller/ApiController.php")

    # Verify receiver of $cfg->getUserValue is resolved to IConfig
    assert len(call_sites) >= 1
    cfg_call = next(cs for cs in call_sites if cs.method_name == "getUserValue")
    assert cfg_call.receiver_expr == "$cfg"
    assert "OCP\\IConfig" in cfg_call.candidate_types


def test_strict_token_budget_invariant_on_rendered_markdown():
    tokenizer = get_default_token_counter()
    compiler = ContextCompiler(repo_root=REPO_ROOT, tokenizer=tokenizer)

    # Create dummy candidates
    cands = []
    for i in range(25):
        cands.append(
            RankedCandidate(
                rank=i + 1,
                entity_id=f"php://OCA\\Files\\Service{i}::doAction",
                file_path=f"apps/files/lib/Service{i}.php",
                total_score=1.0 - (i * 0.03),
                evidence=EvidenceVector(
                    entity_id=f"php://OCA\\Files\\Service{i}::doAction",
                    file_path=f"apps/files/lib/Service{i}.php",
                    hop_distance=1,
                ),
                breakdown=ScoreBreakdown(),
            )
        )

    spec = ChangeSpecification(
        operation=ChangeOperation.BEHAVIOR_CHANGE,
        requested_symbol="Service0",
        canonical_target_ids=["php://OCA\\Files\\Service0::doAction"],
    )

    for budget in [2000, 4000, 8000]:
        plan = ContextPlanner.create_plan(cands, token_budget=budget, spec=spec)
        compiled = compiler.compile(
            ranked_candidates=cands,
            token_budget=budget,
            pinned_targets=set(spec.canonical_target_ids),
            plan=plan,
        )

        rendered_text = compiled.render_prompt_markdown()
        rendered_tokens = tokenizer.count(rendered_text)

        # STRICT INVARIANT: Final rendered markdown prompt MUST NOT exceed token budget
        assert compiled.total_estimated_tokens <= budget
        assert rendered_tokens <= budget


def test_multiobjective_ranker_determinism():
    cands = [
        EvidenceVector(
            entity_id="php://OCP\\IConfig",
            file_path="lib/public/IConfig.php",
            entity_match="exact",
            traversal_score=1.0,
            hop_distance=0,
        ),
        EvidenceVector(
            entity_id="php://OCA\\Files\\App",
            file_path="apps/files/lib/App.php",
            edge_types=["calls"],
            resolution_class="static_exact",
            hop_distance=1,
            traversal_score=0.85,
        ),
        EvidenceVector(
            entity_id="php://tests/ConfigTest",
            file_path="tests/lib/ConfigTest.php",
            edge_types=["calls"],
            resolution_class="static_exact",
            hop_distance=1,
            traversal_score=0.75,
        ),
    ]

    ranker = MultiObjectiveRanker(operation=ChangeOperation.CONFIG_CHANGE)
    res1 = ranker.rank(cands)
    res2 = ranker.rank(cands)

    assert len(res1) == len(res2)
    for c1, c2 in zip(res1, res2):
        assert c1.rank == c2.rank
        assert c1.entity_id == c2.entity_id
        assert c1.total_score == c2.total_score
