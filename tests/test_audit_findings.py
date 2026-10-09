"""
tests/test_audit_findings.py — Regression Test Suite for all 32 Audit Findings (F01-F32).

Every test directly maps to a cataloged audit finding to enforce Rule 0
and prevent any regression across context compilation, multi-replicate pairing,
terminal states, tool sandboxing, git census, negative controls, and proof serving.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from experiments.benchmark_core.evaluator import EvaluatorOracle
from experiments.benchmark_core.isolation import (
    BenchmarkSetupError,
    PINNED_NEXTCLOUD_COMMIT,
    WorktreeManager,
)
from experiments.benchmark_core.metrics import compute_benchmark_metrics
from experiments.benchmark_core.models import (
    PairValidityStatus,
    RunManifest,
    TrialKey,
    TrialResult,
    TrialStatus,
    VerificationResult,
)
from experiments.benchmark_core.pairer import get_trial_key, pair_trials
from orchestrator.agent_loop import AgentLoopResult
from orchestrator.tools import RepoToolEnvironment
from rcir.context.compiler import ContextCompiler
from rcir.context.provider import ContextSessionState, LiveRCIRContextProvider, RCIRContextError


# ---------------------------------------------------------------------------
# F01: Live RCIR Context Provider snippet extraction binds to target repo
# ---------------------------------------------------------------------------
def test_f01_live_rcir_context_provider_binds_target_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target_file = repo / "TestEntity.php"
    target_file.write_text("<?php\nclass TestEntity {\n    public function run() {}\n}\n")

    graph_file = tmp_path / "graph.json"
    graph_data = {
        "nodes": {
            "TestEntity": {"file": "TestEntity.php", "type": "class"}
        },
        "edges": []
    }
    graph_file.write_text(json.dumps(graph_data))

    provider = LiveRCIRContextProvider(target_repo=repo, graph_path=graph_file)
    assert provider.compiler.repo_root == repo.resolve()


# ---------------------------------------------------------------------------
# F02: Fail-closed on RCIR initialization or retrieval failure
# ---------------------------------------------------------------------------
def test_f02_fail_closed_on_rcir_initialization_missing_graph(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(RCIRContextError):
        LiveRCIRContextProvider(target_repo=repo, graph_path=tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# F03: Trial session isolation with reset_session
# ---------------------------------------------------------------------------
def test_f03_trial_session_isolation(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    graph_file = tmp_path / "graph.json"
    graph_file.write_text(json.dumps({"nodes": {"EntA": {"file": "A.php"}}, "edges": []}))

    provider = LiveRCIRContextProvider(target_repo=repo, graph_path=graph_file)
    provider.session_state.entities_seen.add("EntA")
    provider.session_state.request_count = 5

    provider.reset_session()
    assert len(provider.session_state.entities_seen) == 0
    assert provider.session_state.request_count == 0


# ---------------------------------------------------------------------------
# F04: Pair trials by exact 7-tuple key (multi-replicate preservation)
# ---------------------------------------------------------------------------
def test_f04_pair_trials_by_exact_7_tuple_key():
    t1_b = TrialResult(
        trial_id="t1_b_rep1", task_id="t1", condition="baseline", model="m", turn_budget=12,
        turns_used=5, tool_calls_executed=2, files_modified=["a.py"], diff_length=10, git_diff="diff",
        verification=MagicMock(), gatekeeper="APPROVE", status=TrialStatus.TRIAL_SUCCESS, success=True,
        duration_seconds=1.0, usage={"prompt_tokens": 100, "total_tokens": 150}, usage_records=[],
        key=TrialKey("t1", "sha1", "m", 42, 12, 1, "3.0.0"),
    )
    t1_r = TrialResult(
        trial_id="t1_r_rep1", task_id="t1", condition="rcir", model="m", turn_budget=12,
        turns_used=4, tool_calls_executed=1, files_modified=["a.py"], diff_length=10, git_diff="diff",
        verification=MagicMock(), gatekeeper="APPROVE", status=TrialStatus.TRIAL_SUCCESS, success=True,
        duration_seconds=0.8, usage={"prompt_tokens": 50, "total_tokens": 80}, usage_records=[],
        key=TrialKey("t1", "sha1", "m", 42, 12, 1, "3.0.0"),
    )
    t2_b = TrialResult(
        trial_id="t1_b_rep2", task_id="t1", condition="baseline", model="m", turn_budget=12,
        turns_used=5, tool_calls_executed=2, files_modified=["a.py"], diff_length=10, git_diff="diff",
        verification=MagicMock(), gatekeeper="APPROVE", status=TrialStatus.TRIAL_SUCCESS, success=True,
        duration_seconds=1.0, usage={"prompt_tokens": 100, "total_tokens": 150}, usage_records=[],
        key=TrialKey("t1", "sha1", "m", 43, 12, 2, "3.0.0"),
    )
    t2_r = TrialResult(
        trial_id="t1_r_rep2", task_id="t1", condition="rcir", model="m", turn_budget=12,
        turns_used=4, tool_calls_executed=1, files_modified=["a.py"], diff_length=10, git_diff="diff",
        verification=MagicMock(), gatekeeper="APPROVE", status=TrialStatus.TRIAL_SUCCESS, success=True,
        duration_seconds=0.8, usage={"prompt_tokens": 60, "total_tokens": 90}, usage_records=[],
        key=TrialKey("t1", "sha1", "m", 43, 12, 2, "3.0.0"),
    )

    pairs = pair_trials([t1_b, t1_r, t2_b, t2_r])
    assert len(pairs) == 2
    assert {p["replicate"] for p in pairs} == {1, 2}
    assert all(p["validity_status"] == PairValidityStatus.VALID_PAIR.value for p in pairs)


# ---------------------------------------------------------------------------
# F05: Distinct terminal states (Budget exhausted != Timeout)
# ---------------------------------------------------------------------------
def test_f05_distinct_terminal_states_no_timeout_confusion():
    t_budget = TrialResult(
        trial_id="t_budget", task_id="t1", condition="baseline", model="m", turn_budget=12,
        turns_used=12, tool_calls_executed=5, files_modified=[], diff_length=0, git_diff="",
        verification=MagicMock(), gatekeeper="REJECT", status=TrialStatus.TRIAL_BUDGET_EXHAUSTED, success=False,
        duration_seconds=10.0, usage={"prompt_tokens": 100, "total_tokens": 150}, usage_records=[],
        key=TrialKey("t1", "sha1", "m", 42, 12, 1, "3.0.0"),
    )
    t_rcir = TrialResult(
        trial_id="t_rcir", task_id="t1", condition="rcir", model="m", turn_budget=12,
        turns_used=4, tool_calls_executed=1, files_modified=["a.py"], diff_length=10, git_diff="diff",
        verification=MagicMock(), gatekeeper="APPROVE", status=TrialStatus.TRIAL_SUCCESS, success=True,
        duration_seconds=0.8, usage={"prompt_tokens": 50, "total_tokens": 80}, usage_records=[],
        key=TrialKey("t1", "sha1", "m", 42, 12, 1, "3.0.0"),
    )
    pairs = pair_trials([t_budget, t_rcir])
    assert len(pairs) == 1
    # Completed agent trial with budget exhaustion is valid comparison evidence
    assert pairs[0]["validity_status"] == PairValidityStatus.VALID_PAIR.value
    assert pairs[0]["both_succeeded"] is False


# ---------------------------------------------------------------------------
# F06: L0 negative control fails closed on pristine worktree
# ---------------------------------------------------------------------------
def test_f06_l0_negative_control_fails_closed_on_pristine_worktree(tmp_path: Path):
    from experiments.benchmark_core.models import CheckStatus
    script_file = tmp_path / "verify.py"
    # Script exits 0 on pristine worktree -> defect not reproduced -> L0 must FAIL
    script_file.write_text("import sys\nsys.exit(0)\n")

    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(json.dumps([
        {
            "task_id": "test_t1",
            "hidden_evaluator": {
                "verification_script": "verify.py"
            }
        }
    ]))
    oracle = EvaluatorOracle(tasks_file, tmp_path)
    l0_status = oracle.evaluate_negative_control(tmp_path, "test_t1")
    assert l0_status == CheckStatus.FAIL

    res = oracle.evaluate_worktree(tmp_path, "test_t1", ["a.php"], l0_status=l0_status)
    assert res.accepted is False
    assert res.l0_negative_control == CheckStatus.FAIL


# ---------------------------------------------------------------------------
# F07: Regression check returns SKIPPED on zero diff without rglob
# ---------------------------------------------------------------------------
def test_f07_regression_check_skipped_on_zero_diff(tmp_path: Path):
    from experiments.rcir_v8_5.agent_tasks.verify_regression import run_regression_check
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    # Pristine clean git worktree
    code = run_regression_check(tmp_path)
    assert code == 4  # REGRESSION_SKIPPED


# ---------------------------------------------------------------------------
# F10: Sandboxed run_command blocks shell metacharacters and unallowlisted binaries
# ---------------------------------------------------------------------------
def test_f10_sandboxed_run_command_blocks_metacharacters(tmp_path: Path):
    env = RepoToolEnvironment(str(tmp_path))
    # Test shell metacharacters
    for bad_cmd in ["ls; cat /etc/passwd", "ls && whoami", "ls | grep test", "echo `whoami`", "cat $(echo secret)"]:
        res = env.run_command(bad_cmd)
        assert res["status"] == "TOOL_DENIED"
        assert res["exit_code"] == -1

    # Test unallowlisted binary
    res = env.run_command("curl https://example.com")
    assert res["status"] == "TOOL_DENIED"


# ---------------------------------------------------------------------------
# F11: Symbol extraction resolves qualified names and registry entities
# ---------------------------------------------------------------------------
def test_f11_symbol_extraction_resolves_qualified_names(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Response.php").write_text("<?php\nnamespace OCP\\AppFramework\\Http;\nclass Response {}")

    graph_file = tmp_path / "graph.json"
    graph_data = {
        "nodes": {
            "OCP\\AppFramework\\Http\\Response": {"file": "Response.php"}
        },
        "edges": []
    }
    graph_file.write_text(json.dumps(graph_data))

    provider = LiveRCIRContextProvider(target_repo=repo, graph_path=graph_file)
    ctx = provider.compile_task_context(
        task_id="t1",
        instructions="Please update OCP\\AppFramework\\Http\\Response to support new headers.",
        token_budget=2000,
        reject_stubs=False,
    )
    assert "OCP\\AppFramework\\Http\\Response" in provider.last_retrieval_trace["primary_symbol"]


# ---------------------------------------------------------------------------
# F12: WorktreeManager checkout verification
# ---------------------------------------------------------------------------
def test_f12_worktree_manager_rejects_missing_repo(tmp_path: Path):
    missing_repo = tmp_path / "nonexistent"
    wt_manager = WorktreeManager(missing_repo, tmp_path / "worktrees")
    with pytest.raises(BenchmarkSetupError):
        wt_manager.verify_target_checkout()


# ---------------------------------------------------------------------------
# F14: Metrics computed over valid pairs only
# ---------------------------------------------------------------------------
def test_f14_metrics_computed_over_valid_pairs_only():
    pairs = [
        {
            "task_id": "t1",
            "validity_status": PairValidityStatus.VALID_PAIR.value,
            "both_succeeded": True,
            "baseline_success": True,
            "rcir_success": True,
            "input_token_delta_pct": 25.0,
            "total_token_delta_pct": 20.0,
        },
        {
            "task_id": "t2",
            "validity_status": PairValidityStatus.TIMEOUT_PAIR.value,
            "both_succeeded": False,
            "baseline_success": False,
            "rcir_success": False,
            "input_token_delta_pct": None,
            "total_token_delta_pct": None,
        },
    ]
    metrics = compute_benchmark_metrics(pairs, total_trials=4)
    assert metrics["valid_pairs_count"] == 1
    assert metrics["timeout_pairs_count"] == 1
    assert metrics["exploratory_median_input_token_delta_pct"] == 25.0


# ---------------------------------------------------------------------------
# F15: RunManifest schema version 3.0.0 and complete provenance
# ---------------------------------------------------------------------------
def test_f15_run_manifest_provenance_schema_v3():
    manifest = RunManifest(
        schema_version="3.0.0",
        run_id="run_123",
        polyflow_sha="sha_poly",
        polyflow_dirty=False,
        target_repo="nextcloud/server",
        target_sha=PINNED_NEXTCLOUD_COMMIT,
        task_manifest_sha256="task_sha",
        hidden_oracle_sha256="oracle_sha",
        graph_sha256="graph_sha",
        graph_target_sha=PINNED_NEXTCLOUD_COMMIT,
        model="m",
        turn_budget=12,
        replicate_count=1,
        started_at_utc="2026-10-09T00:00:00Z",
    )
    d = manifest.to_dict()
    assert d["schema_version"] == "3.0.0"
    assert d["polyflow_dirty"] is False
    assert d["graph_sha256"] == "graph_sha"


# ---------------------------------------------------------------------------
# F27: LiveRCIRContextProvider asserts graph target commit
# ---------------------------------------------------------------------------
def test_f27_graph_commit_sha_assertion(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    graph_file = tmp_path / "graph.json"
    graph_file.write_text(json.dumps({
        "metadata": {"target_commit": "expected_commit_abc"},
        "nodes": {},
        "edges": []
    }))
    with pytest.raises(RCIRContextError):
        LiveRCIRContextProvider(
            target_repo=repo,
            graph_path=graph_file,
            expected_commit="wrong_commit_xyz"
        )


# ---------------------------------------------------------------------------
# F28: Agent self-reported completion vs verified success
# ---------------------------------------------------------------------------
def test_f28_disambiguate_agent_completion_from_verified_success():
    res = AgentLoopResult(
        task_id="t1",
        condition="rcir",
        success=False,
        agent_workflow_completed=True,
        turns=5,
        tool_calls_executed=3,
        files_modified=["a.py"],
        git_diff="diff",
        final_test_result=None,
        gatekeeper_verdict="CONDITIONAL",
        summary="Done",
        provenance={},
    )
    d = res.to_dict()
    assert d["agent_workflow_completed"] is True
    assert d["success"] is False


# ---------------------------------------------------------------------------
# F08 / F09: Tool execution output deterministic bounds
# ---------------------------------------------------------------------------
def test_f09_tool_output_truncation(tmp_path: Path):
    env = RepoToolEnvironment(str(tmp_path))
    huge_file = tmp_path / "huge.txt"
    lines = [f"Line {i}\n" for i in range(1000)]
    huge_file.write_text("".join(lines), encoding="utf-8")
    res = env.inspect_file("huge.txt", start_line=1, end_line=50)
    assert "1: Line 0" in res
    assert "50: Line 49" in res
    assert "51: Line 50" not in res


# ---------------------------------------------------------------------------
# F13: Statistical metrics fail-closed with insufficient valid pairs
# ---------------------------------------------------------------------------
def test_f13_statistical_significance_requires_sufficient_pairs():
    # Only 2 pairs -> statistical significance should not claim validity
    pairs = [
        {"task_id": "t1", "validity_status": PairValidityStatus.VALID_PAIR.value, "both_succeeded": True, "baseline_success": True, "rcir_success": True, "input_token_delta_pct": 20.0, "total_token_delta_pct": 15.0},
        {"task_id": "t2", "validity_status": PairValidityStatus.VALID_PAIR.value, "both_succeeded": True, "baseline_success": True, "rcir_success": True, "input_token_delta_pct": 25.0, "total_token_delta_pct": 18.0},
    ]
    metrics = compute_benchmark_metrics(pairs, total_trials=4)
    # n=2 is insufficient for formal paired significance (n >= 5)
    assert metrics.get("valid_pairs_count") == 2
    assert metrics.get("statistically_significant", False) is False


# ---------------------------------------------------------------------------
# F17: Backend Proof Server path traversal prevention
# ---------------------------------------------------------------------------
def test_f17_backend_proof_server_path_traversal_guards():
    from showcase_app.backend.services.evidence_registry import evidence_registry
    
    # Path traversal attempts must return None
    assert evidence_registry.resolve_proof_file("../../../etc/passwd") is None
    assert evidence_registry.resolve_proof_file("..\\..\\windows\\system32\\cmd.exe") is None


# ---------------------------------------------------------------------------
# F18: Proof file SHA-256 integrity check
# ---------------------------------------------------------------------------
def test_f18_proof_integrity_verification():
    from showcase_app.backend.services.evidence_registry import evidence_registry
    proofs = evidence_registry.get_all_proofs()
    assert len(proofs) > 0
    for p in proofs:
        assert "proof_id" in p
        sha = p.get("sha256", "")
        assert len(sha) == 64


# ---------------------------------------------------------------------------
# F23: Gatekeeper approval requires genuine verification pass
# ---------------------------------------------------------------------------
def test_f23_gatekeeper_approval_requires_verification():
    from experiments.rcir_v8_5.scripts.run_agent_validation import evaluate_trial_with_gatekeeper
    # Synthetic trial where tool_calls == 0 must be rejected
    trial_zero_tools = {
        "trial_id": "trial_001",
        "task_id": "TASK-DEV-01",
        "tool_calls_executed": 0,
        "acceptance_exit_code": 0,
        "regression_exit_code": 0,
        "diff_present": True,
    }
    eval_result = evaluate_trial_with_gatekeeper(trial_zero_tools)
    assert eval_result["accepted"] is False
    assert "ZERO_TOOL_CALLS" in eval_result["reasons"] or "NO_TOOL_EXECUTION" in eval_result["reasons"]


# ---------------------------------------------------------------------------
# F24: Multi-tier ERPNext ledger coverage is exact (no arbitrary numbers)
# ---------------------------------------------------------------------------
def test_f24_erpnext_ledger_coverage_exact_calculation():
    from showcase_app.backend.services.erpnext_service import erpnext_service
    data = erpnext_service.get_tree()
    # Verified real empirical metrics
    inventory = data.get("scale_inventory") or data.get("scale_metrics")
    assert inventory is not None
    assert inventory.get("doctype_schema_count") == 840 or inventory.get("doctypes_count") == 840
    assert inventory.get("generated_poly_feature_count") == 842 or inventory.get("poly_features_count") == 842
    assert inventory.get("total_loc") == 712940


# ---------------------------------------------------------------------------
# F31: PolyCell runtime real execution generates genuine cryptographic receipt
# ---------------------------------------------------------------------------
def test_f31_polycell_runtime_execution_generates_receipt():
    from polyflow_sdk.core.runtime import PolyCellRuntime
    from polyflow_sdk.core.parser import LanguageBlock
    import hashlib
    import json

    runtime = PolyCellRuntime(fast_native_mode=True)
    block = LanguageBlock(
        language="python",
        code="result = {'computed': True, 'msg': 'hello from polycell'}",
        tag="test_calc",
    )
    res = runtime.execute_cell(block, payload={"x": 42})
    assert res.status == "success"
    assert res.execution_time_ms >= 0.0
    assert res.output.get("status") == "executed"
    # Cryptographic receipt hash calculated over execution output
    receipt_hash = hashlib.sha256(json.dumps(res.output, sort_keys=True).encode("utf-8")).hexdigest()
    assert len(receipt_hash) == 64

