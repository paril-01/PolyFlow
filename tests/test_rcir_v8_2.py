"""RCIR v8.2 Integration and Unit Tests.

Validates:
1. Adaptive Graph-Degree Dynamic Fanout (FanoutPolicy)
2. Semantic Type Flow (TypeFlowIndex)
3. Cascaded Ranker & Operation Profiles
4. Context Compiler (AST Spans & Budget Allocation)
5. Gate Evaluation Schema & Rules
6. Raw Artifact Integrity
"""

import json
import pytest
from pathlib import Path

from rcir.graph.traversal_policy import FanoutPolicy, FanoutMode
from rcir.types.type_flow import TypeFlowIndex, ReceiverResolutionStatus
from rcir.retrieval.ranker import (
    RankerConfig,
    DeterministicRanker,
    ScoreBreakdown,
    RankedCandidate,
)
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.context.compiler import ContextCompiler, CompiledContext
from rcir.query.change_spec import ChangeOperation


class TestDynamicFanout:
    def test_low_degree_fanout(self):
        policy = FanoutPolicy.evaluate(degree=3, operation=ChangeOperation.SIGNATURE_CHANGE)
        assert policy.mode == FanoutMode.LOW_DEGREE
        assert policy.max_indirect_candidates > 50

    def test_hub_node_fanout(self):
        policy = FanoutPolicy.evaluate(degree=120, operation=ChangeOperation.SIGNATURE_CHANGE)
        assert policy.mode == FanoutMode.HIGH_DEGREE
        assert policy.max_indirect_candidates <= 200

    def test_monotonicity(self):
        p_low = FanoutPolicy.evaluate(degree=2, operation=ChangeOperation.SIGNATURE_CHANGE)
        p_med = FanoutPolicy.evaluate(degree=25, operation=ChangeOperation.SIGNATURE_CHANGE)
        p_high = FanoutPolicy.evaluate(degree=150, operation=ChangeOperation.SIGNATURE_CHANGE)
        assert p_low.max_indirect_candidates >= p_med.max_indirect_candidates >= p_high.max_indirect_candidates


class TestSemanticTypeFlow:
    def test_type_flow_index_from_graph(self):
        raw_graph = {
            "nodes": {
                "service_a.py::UserModel": {"type": "class"},
                "service_a.py::get_user": {"type": "function", "return_type": "UserModel"},
                "service_b.py::handle_request": {"type": "function"},
            },
            "edges": [
                {
                    "source": "service_b.py::handle_request",
                    "target": "service_a.py::get_user",
                    "edge_type": "calls",
                }
            ],
        }
        index = TypeFlowIndex.from_graph(raw_graph)
        assert index is not None
        assert hasattr(index, "resolve_receiver") or hasattr(index, "type_signatures") or hasattr(index, "call_sites")


class TestCascadedRanker:
    def test_cascaded_ranking_behavior(self):
        config = RankerConfig(use_cascaded_ranking=True)
        ranker = DeterministicRanker(config)

        # Build vectors: target file, direct static exact caller, unrelated doc
        v_target = EvidenceVector(
            entity_id="src/cartservice/service.py::AddItem",
            file_path="src/cartservice/service.py",
            entity_match="exact",
            resolution_class="static_exact",
        )
        v_caller = EvidenceVector(
            entity_id="src/frontend/rpc.go::insertCart",
            file_path="src/frontend/rpc.go",
            resolution_class="static_exact",
            traversal_score=0.9,
            edge_types=["calls"],
        )
        v_doc = EvidenceVector(
            entity_id="docs/readme.md::heading",
            file_path="docs/readme.md",
            lexical_score=0.1,
        )

        ranked = ranker.rank([v_doc, v_caller, v_target])
        assert len(ranked) == 3
        # Target should be ranked #1
        assert ranked[0].file_path == "src/cartservice/service.py"
        # Direct static caller should be ranked #2
        assert ranked[1].file_path == "src/frontend/rpc.go"
        assert ranked[2].file_path == "docs/readme.md"


class TestContextCompiler:
    def test_budget_allocation(self, tmp_path):
        f = tmp_path / "test_file.py"
        f.write_text("\n".join([f"line_{i} = {i}" for i in range(100)]))

        compiler = ContextCompiler(repo_root=tmp_path)
        vec = EvidenceVector(
            entity_id=f"{f.name}::line_50",
            file_path=str(f),
            entity_match="exact",
        )
        cand = RankedCandidate(
            rank=1,
            entity_id=vec.entity_id,
            file_path=vec.file_path,
            total_score=100.0,
            evidence=vec,
            breakdown=ScoreBreakdown(),
        )

        compiled = compiler.compile(
            ranked_candidates=[cand],
            token_budget=500,
        )
        assert isinstance(compiled, CompiledContext)
        assert compiled.total_estimated_tokens <= 500
        assert compiled.candidates_included >= 1


class TestArtifactIntegrity:
    def test_results_exist_and_parse(self):
        results_dir = Path("experiments/rcir_v8_2/results")
        required_files = [
            "impact_plane.json",
            "context_plane.json",
            "silent_miss_catalog.json",
            "ranker_ablations.json",
            "selected_ranker_config.json",
            "type_flow_evaluation.json",
            "lexical_evaluation.json",
            "edge_recall_evaluation.json",
            "context_compiler_evaluation.json",
            "agent_turn_budget.json",
            "agent_ab_runs.json",
            "performance_benchmark.json",
            "gate_evaluation.json",
        ]
        for name in required_files:
            file_path = results_dir / name
            assert file_path.exists(), f"Missing required result artifact: {name}"
            with open(file_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                assert data is not None, f"Artifact {name} was empty or failed JSON decode"

    def test_reports_exist(self):
        reports_dir = Path("experiments/rcir_v8_2/reports")
        required_reports = [
            "v8_1_reassessment.md",
            "impact_plane_report.md",
            "ranking_report.md",
            "type_flow_report.md",
            "context_compiler_report.md",
            "edge_quality_report.md",
            "agent_turn_budget_report.md",
            "agent_ab_report.md",
            "generalization_report.md",
            "failure_catalog.md",
            "final_assessment.md",
            "reproduction.md",
        ]
        for name in required_reports:
            report_path = reports_dir / name
            assert report_path.exists(), f"Missing report: {name}"
            assert report_path.stat().st_size > 0, f"Report {name} is empty"

    def test_gate_evaluation_verdict(self):
        gate_path = Path("experiments/rcir_v8_2/results/gate_evaluation.json")
        with open(gate_path, "r", encoding="utf-8") as f:
            gate_data = json.load(f)
        assert "recommendation" in gate_data
        assert gate_data["recommendation"] in [
            "OPTION A — VALIDATED",
            "OPTION B — PARTIALLY VALIDATED",
            "OPTION C — REJECTED",
        ]

    def test_report_consistency(self):
        import sys
        sys.path.insert(0, "experiments/rcir_v8_2/scripts")
        from validate_report_consistency import validate_consistency
        # Should execute without throwing SystemExit or AssertionError
        validate_consistency()

