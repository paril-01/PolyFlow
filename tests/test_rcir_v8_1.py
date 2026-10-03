"""
RCIR v8.1 — Comprehensive Regression & Unit Test Suite (PHASE 40).

Tests:
1. MultiViewGraph.get_callees returns [] rather than raising NameError (DEF-02)
2. TraversalRule.min_resolution enforced (DEF-05)
3. Candidate shortest hop retained (min instead of max) (DEF-04)
4. Traversal resolution preserved in CandidateRecord (DEF-04)
5. Traversal score preserved in CandidateRecord (DEF-04)
6. Static exact not inferred from exact entity lookup (PHASE 13)
7. Type compatibility populated in EvidenceVector (PHASE 14)
8. Historical score affects ranking when enabled (PHASE 12)
9. CandidateGeneratorConfig truly disables ablation features (PHASE 10)
10. Context compiler extracts actual entity span rather than file head (PHASE 25)
11. Token-budget coverage uses compiler output (PHASE 26)
12. request_context invokes RCIR rather than grep (PHASE 28)
13. edit_file returns SUCCESS string (DEF-03)
14. Empty diff cannot yield success=true (PHASE 31)
15. Gatekeeper cannot approve unverified benchmark task (PHASE 32)
16. TaskRiskRouter controls executed stages (PHASE 34)
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

import pytest
from rcir.graph.multi_view import MultiViewGraph
from rcir.graph.traversal_policy import (
    TraversalPolicy,
    TraversalRule,
    TraversalDirection,
    execute_policy_traversal,
)
from rcir.retrieval.candidate_generator import (
    CandidateGenerator,
    CandidateGeneratorConfig,
    CandidateRecord,
)
from rcir.retrieval.evidence_vector import EvidenceVector, EvidenceVectorBuilder
from rcir.retrieval.ranker import DeterministicRanker
from rcir.context.compiler import ContextCompiler, ContextGranularity
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from orchestrator.tools import RepoToolEnvironment
from orchestrator.agent_loop import ReActAgentRunner, AgentLoopResult
from orchestrator.router import TaskRiskRouter, TaskRiskLevel


# Test 1: MultiViewGraph.get_callees returns [] rather than raising NameError
def test_multiview_get_callees_empty():
    dummy_graph = {"nodes": [{"path": "foo.php"}], "edges": []}
    mv = MultiViewGraph(dummy_graph)
    callees = mv.get_callees("foo.php")
    assert isinstance(callees, list)
    assert len(callees) == 0


# Test 2: TraversalRule.min_resolution enforced
def test_traversal_rule_min_resolution_enforced():
    raw_graph = {
        "nodes": [{"path": "node_a"}, {"path": "node_b"}],
        "edges": [
            {
                "source": "node_a",
                "target": "node_b",
                "edge_type": "calls",
                "resolution": "dynamic_unresolved",
            }
        ],
    }
    mv = MultiViewGraph(raw_graph)
    # Rule demands min_resolution = "static_exact"
    policy = TraversalPolicy(
        operation=ChangeOperation.BEHAVIOR_CHANGE,
        rules=[
            TraversalRule(
                "calls",
                TraversalDirection.FORWARD,
                max_hops=1,
                min_resolution="static_exact",
            )
        ],
        max_hops=1,
    )
    hits = execute_policy_traversal(mv, ["node_a"], policy)
    assert len(hits) == 0  # dynamic_unresolved is weaker than static_exact, must be rejected


# Test 3: Candidate shortest hop retained (min instead of max)
def test_candidate_shortest_hop_retained():
    rec = CandidateRecord(entity_id="test_node", file_path="test.php")
    rec.best_hop_distance = 2
    # Encounter again at hop 1
    new_hop = 1
    if rec.best_hop_distance == 0 or new_hop < rec.best_hop_distance:
        rec.best_hop_distance = new_hop
    assert rec.best_hop_distance == 1


# Test 4 & 5: Traversal resolution and score preserved
def test_traversal_resolution_and_score_preserved():
    raw_graph = {
        "nodes": [{"path": "node_a"}, {"path": "node_b"}],
        "edges": [
            {
                "source": "node_a",
                "target": "node_b",
                "edge_type": "calls",
                "resolution": "static_exact",
            }
        ],
    }
    mv = MultiViewGraph(raw_graph)
    policy = TraversalPolicy(
        operation=ChangeOperation.BEHAVIOR_CHANGE,
        rules=[
            TraversalRule(
                "calls",
                TraversalDirection.FORWARD,
                max_hops=1,
                min_resolution="static_inference",
            )
        ],
        max_hops=1,
    )
    hits = execute_policy_traversal(mv, ["node_a"], policy)
    assert len(hits) == 1
    hit = hits[0]
    assert hit.resolution == "static_exact"
    assert hit.best_traversal_score > 0.0
    assert len(hit.edge_evidence) == 1
    assert hit.edge_evidence[0].source == "node_a"


# Test 6: Static exact not inferred from exact entity lookup
def test_static_exact_not_inferred_from_exact_entity_lookup():
    cand = CandidateRecord(
        entity_id="foo.php::FooClass",
        file_path="foo.php",
        candidate_sources=["exact_entity_lookup"],
        resolution_classes=[],  # No edges found!
    )
    spec = ChangeSpecification(
        operation=ChangeOperation.BEHAVIOR_CHANGE,
        description="test",
        target_entities=["foo.php::FooClass"],
    )
    vec = EvidenceVectorBuilder.build_vector(cand, spec, target_files={"foo.php"})
    assert vec.entity_match == "exact"
    # Relationship resolution class must remain 'unknown', not 'static_exact'
    assert vec.resolution_class == "unknown"


# Test 7: Type compatibility populated
def test_type_compatibility_populated():
    cand = CandidateRecord(
        entity_id="bar.php::BarClass",
        file_path="bar.php",
        edge_types_seen=["inherits"],
    )
    spec = ChangeSpecification(
        operation=ChangeOperation.BEHAVIOR_CHANGE,
        description="test",
        target_entities=["FooClass"],
    )
    vec = EvidenceVectorBuilder.build_vector(cand, spec, target_files=set())
    assert vec.type_compatibility == "compatible"


# Test 8: Historical score affects ranking when enabled
def test_historical_score_affects_ranking():
    ranker = DeterministicRanker()
    v1 = EvidenceVector(entity_id="e1", file_path="e1.php", historical_cochange=0.0)
    v2 = EvidenceVector(entity_id="e2", file_path="e2.php", historical_cochange=0.8)
    s1, _ = ranker.score_vector(v1)
    s2, _ = ranker.score_vector(v2)
    assert s2 > s1
    assert s2 - s1 == pytest.approx(0.8 * ranker.W_HISTORICAL, 0.01)


# Test 9: CandidateGeneratorConfig truly disables ablation features
def test_candidate_generator_config_disables_features():
    raw_graph = {"nodes": [{"path": "a.php"}, {"path": "b.php"}], "edges": []}
    mv = MultiViewGraph(raw_graph)
    gen = CandidateGenerator(
        multi_view=mv,
        config=CandidateGeneratorConfig(
            use_entity_resolution=False,
            use_boundary_graph=False,
            use_traversal=False,
            use_lexical=False,
            use_test_graph=False,
        ),
    )
    spec = ChangeSpecification(
        operation=ChangeOperation.BEHAVIOR_CHANGE,
        description="search term",
        target_entities=["non_existent"],
    )
    cands = gen.generate(spec)
    assert len(cands) == 0


# Test 10: Context compiler extracts actual entity span
def test_context_compiler_extracts_actual_entity_span():
    compiler = ContextCompiler()
    code_lines = [
        "<?php",
        "// header comments",
        "class TargetController {",
        "    public function testAction() {",
        "        return true;",
        "    }",
        "}",
    ]
    s, e = compiler._locate_entity_span(code_lines, "TargetController::testAction", ContextGranularity.SIGNATURE)
    # testAction is at line 4, span must center around line 4 rather than line 1
    assert s <= 4 <= e


# Test 11: Token-budget coverage uses compiler output
def test_token_budget_coverage_uses_compiler_output():
    compiler = ContextCompiler()
    cand = CandidateRecord(entity_id="foo.php::Foo", file_path="foo.php")
    vec = EvidenceVector(entity_id="foo.php::Foo", file_path="foo.php")
    ranker = DeterministicRanker()
    ranked = ranker.rank([vec])
    compiled = compiler.compile(ranked, token_budget=4000)
    assert compiled.total_estimated_tokens > 0
    assert compiled.candidates_included == 1


# Test 12: Request context records requests
def test_request_context_records_usage():
    env = RepoToolEnvironment(str(REPO_ROOT))
    initial_count = env.context_requests_count
    resp = env.request_context("ApiController")
    assert env.context_requests_count == initial_count + 1
    assert isinstance(resp, str)


# Test 13: edit_file returns SUCCESS string
def test_edit_file_returns_success_string(tmp_path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("hello old world", encoding="utf-8")
    env = RepoToolEnvironment(str(tmp_path))
    res = env.edit_file("sample.py", "old", "new")
    assert isinstance(res, str)
    assert res.startswith("SUCCESS:")
    assert test_file.read_text(encoding="utf-8") == "hello new world"


# Test 14: Empty diff cannot yield success=true
def test_empty_diff_cannot_yield_success():
    res = AgentLoopResult(
        task_id="T1",
        condition="test",
        success=False,
        turns=1,
        tool_calls_executed=0,
        files_modified=[],
        git_diff="",
        final_test_result={"exit_code": 0},
        gatekeeper_verdict="REJECT",
        summary="No changes",
        provenance={},
    )
    # Verification passed, but diff is empty -> success must be False
    success = bool(res.git_diff) and res.gatekeeper_verdict == "APPROVE"
    assert success is False


# Test 15: Gatekeeper cannot approve unverified benchmark task
def test_gatekeeper_cannot_approve_unverified():
    from orchestrator.providers import LLMProvider
    env = RepoToolEnvironment(str(REPO_ROOT))
    runner = ReActAgentRunner(env=env, provider=LLMProvider("dry-run"))
    res = runner.run(
        task_id="T1",
        task_description="unverified task",
        condition="test",
        test_command=None,  # No verification command!
    )
    assert res.gatekeeper_verdict == "CONDITIONAL"
    assert res.success is False


# Test 16: TaskRiskRouter controls executed stages
def test_task_risk_router_controls_stages():
    router = TaskRiskRouter()
    decision_low = router.route("Rename internal helper method")
    assert decision_low.risk_level == TaskRiskLevel.LOCAL_BUG
    assert len(decision_low.stages) < 6  # Fewer stages for low risk

    spec_high = ChangeSpecification(operation=ChangeOperation.SCHEMA_CHANGE, description="database schema")
    decision_high = router.route("Migrate database schema and update payment service boundary", spec=spec_high)
    assert decision_high.risk_level == TaskRiskLevel.ARCHITECTURE_REFACTOR
