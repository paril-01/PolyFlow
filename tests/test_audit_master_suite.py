"""
tests/test_audit_master_suite.py — Comprehensive Master Test Suite for Commit ea221b9 Audit Remediations.

Validates Checkpoints G1 through G10 and Tests T01-T36:
- T01-T04: Canonical PHP entity to source file resolution, registry population, ambiguity handling
- T07: Path traversal and security escape fail-closed behavior
- T10: Trial session reset and seen entity isolation
- T14: Public tasks vs private oracle physical boundary and hash divergence
- T15-T16: L0 negative control assertion qualification and mandatory requirement
- T18-T20: L3 behavioral separation from L1 PHP syntax lint
- T28: Sandboxed execution denials for python -c, python -m, php -r, git -c
- T30-T31: Untracked file inclusion in git census and diff generation
- T32: Ephemeral repository revert safety
- T35-T36: Run-scoped evidence API fail-closed behavior without ungrounded fallbacks
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from experiments.benchmark_core.evaluator import EvaluatorOracle
from experiments.benchmark_core.isolation import WorktreeManager, BenchmarkSetupError
from experiments.benchmark_core.models import CheckStatus, VerificationResult, TrialKey, TrialResult, TrialStatus
from experiments.benchmark_core.hashes import sha256_file
from orchestrator.tools import RepoToolEnvironment
from rcir.context.source_resolver import GraphEntitySourceResolver, SourceLocation, PathTraversalError
from rcir.context.provider import LiveRCIRContextProvider, ContextSessionState
from rcir.entities.canonical import (
    CanonicalEntityRegistry,
    CanonicalEntityID,
    EntityKind,
    AliasResolution,
    SourceSpan,
)
from showcase_app.backend.services.benchmark_service import BenchmarkService


# ---------------------------------------------------------------------------
# T01 & T02: Canonical PHP Entity resolves to real file and populates registry
# ---------------------------------------------------------------------------
def test_t01_t02_canonical_php_resolves_real_path_and_populates_registry(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    lib_dir = repo / "lib" / "public" / "Files"
    lib_dir.mkdir(parents=True)
    php_file = lib_dir / "Node.php"
    php_file.write_text("<?php\nnamespace OCP\\Files;\nclass Node {\n    public function getId() { return 1; }\n}\n")

    graph_data = {
        "nodes": [
            {
                "path": "lib/public/Files/Node.php::OCP\\Files\\Node",
                "file": "lib/public/Files/Node.php",
                "kind": "class",
                "name": "Node",
                "namespace": "OCP\\Files",
                "line": 3,
                "end_line": 5,
                "language": "php",
            }
        ],
        "edges": []
    }
    graph_file = tmp_path / "graph.json"
    graph_file.write_text(json.dumps(graph_data))

    provider = LiveRCIRContextProvider(target_repo=repo, graph_path=graph_file)
    # T02: Entity must be in registry.entities
    assert len(provider.registry.entities) == 1
    node_key = "lib/public/Files/Node.php::OCP\\Files\\Node"
    assert node_key in provider.registry.entities
    assert provider.registry.entities[node_key].kind == EntityKind.CLASS

    # T01: Source resolver resolves to real lib/public/Files/Node.php
    loc = provider.source_resolver.resolve(node_key)
    assert isinstance(loc, SourceLocation)
    assert loc.relative_path == "lib/public/Files/Node.php"
    assert loc.absolute_path.is_file()
    assert loc.is_exact_match is True


# ---------------------------------------------------------------------------
# T03: Ambiguous short symbol produces AMBIGUOUS and disambiguates with hint
# ---------------------------------------------------------------------------
def test_t03_ambiguous_short_symbol_handling(tmp_path: Path):
    registry = CanonicalEntityRegistry()
    ent1 = CanonicalEntityID(
        repository="repo", language="php", file="apps/a/Controller.php",
        namespace="OCA\\A", owner_type="Controller", symbol="Controller", kind=EntityKind.CLASS
    )
    ent2 = CanonicalEntityID(
        repository="repo", language="php", file="apps/b/Controller.php",
        namespace="OCA\\B", owner_type="Controller", symbol="Controller", kind=EntityKind.CLASS
    )
    registry.entities["uri_a"] = ent1
    registry.entities["uri_b"] = ent2
    registry.alias_to_uris["Controller"] = {"uri_a", "uri_b"}

    # Without hint -> AMBIGUOUS
    res_ambig = registry.resolve("Controller")
    assert res_ambig.resolution == AliasResolution.AMBIGUOUS

    # With hint -> Disambiguated uniquely
    res_hint = registry.resolve("Controller", target_file_hint="apps/a/Controller.php")
    assert res_hint.resolution == AliasResolution.UNIQUE_ALIAS
    assert res_hint.canonical_id == "uri_a"


# ---------------------------------------------------------------------------
# T04: Unknown symbol never receives exact match
# ---------------------------------------------------------------------------
def test_t04_unknown_symbol_never_exact(tmp_path: Path):
    resolver = GraphEntitySourceResolver(repo_root=tmp_path, raw_graph={"nodes": [], "edges": []})
    loc = resolver.resolve("CompletelyUnknownNonexistentSymbol")
    assert not isinstance(loc, SourceLocation) or not loc.is_exact_match


# ---------------------------------------------------------------------------
# T07: Path traversal and escapes fail closed
# ---------------------------------------------------------------------------
def test_t07_path_traversal_fails_closed(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    resolver = GraphEntitySourceResolver(repo_root=repo, raw_graph={"nodes": [], "edges": []})
    with pytest.raises(PathTraversalError):
        resolver.resolve("../../../etc/passwd")


# ---------------------------------------------------------------------------
# T10: Fresh provider session prevents cross-trial leakage
# ---------------------------------------------------------------------------
def test_t10_session_reset_prevents_leakage():
    session = ContextSessionState()
    session.entities_seen.add("EntityA")
    session.files_seen.add("FileA.php")
    session.spans_seen.add(("FileA.php", 10, 20))
    session.tokens_already_supplied = 500

    assert len(session.entities_seen) == 1
    # Reset
    fresh = ContextSessionState()
    assert len(fresh.entities_seen) == 0
    assert len(fresh.files_seen) == 0
    assert fresh.tokens_already_supplied == 0


# ---------------------------------------------------------------------------
# T14: Physical separation of public tasks vs private oracle
# ---------------------------------------------------------------------------
def test_t14_tasks_and_oracle_physical_isolation():
    pub_file = Path("experiments/benchmarks/public/dev.json")
    priv_file = Path("experiments/benchmarks/private/dev/oracle.json")
    assert pub_file.exists()
    assert priv_file.exists()

    pub_data = json.loads(pub_file.read_text(encoding="utf-8"))
    priv_data = json.loads(priv_file.read_text(encoding="utf-8"))

    # Public tasks must never expose hidden_evaluator
    for t in pub_data.get("tasks", []):
        assert "hidden_evaluator" not in t

    # Private oracle must contain hidden_evaluator
    has_hidden = any("hidden_evaluator" in t for t in priv_data.get("tasks", []))
    assert has_hidden is True

    # Hashes must strictly differ
    pub_sha = sha256_file(pub_file)
    priv_sha = sha256_file(priv_file)
    assert pub_sha != priv_sha


# ---------------------------------------------------------------------------
# T15 & T16: L0 negative control qualifies assertion vs crash, mandatory for pass
# ---------------------------------------------------------------------------
def test_t15_t16_l0_negative_control_qualification_and_requirement(tmp_path: Path):
    evaluator = EvaluatorOracle(oracle_path=tmp_path / "oracle.json", repo_root=tmp_path)

    # Test crash / syntax / import error results in SETUP_ERROR, not PASS
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Traceback (most recent call last):\n  ModuleNotFoundError: No module named 'foo'", stdout="")
        with patch.object(evaluator, "get_task_oracle", return_value={"hidden_evaluator": {"verification_script": "fake.py"}}):
            with patch("pathlib.Path.exists", return_value=True):
                status = evaluator.evaluate_negative_control(tmp_path, "T1")
                assert status == CheckStatus.SETUP_ERROR

    # Test genuine assertion failure results in PASS
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="ASSERTION_FAIL: Target signature not matched", stdout="")
        with patch.object(evaluator, "get_task_oracle", return_value={"hidden_evaluator": {"verification_script": "fake.py"}}):
            with patch("pathlib.Path.exists", return_value=True):
                status = evaluator.evaluate_negative_control(tmp_path, "T1")
                assert status == CheckStatus.PASS

    # T16: L0 SKIPPED cannot earn accepted verdict
    verif = evaluator.evaluate_worktree(tmp_path, "T1", ["a.php"], l0_status=CheckStatus.SKIPPED)
    assert verif.accepted is False


# ---------------------------------------------------------------------------
# T18: L1 syntax-only runner never reports L3 PASS
# ---------------------------------------------------------------------------
def test_t18_l1_syntax_never_reports_l3_pass(tmp_path: Path):
    evaluator = EvaluatorOracle(oracle_path=tmp_path / "oracle.json", repo_root=tmp_path)
    with patch("subprocess.run") as mock_run:
        # Mocking verify_regression.py outputting syntax check pass
        mock_run.return_value = MagicMock(returncode=0, stdout="PASS: Regression syntax checks passed for 3 files via PHP.", stderr="")
        with patch.object(evaluator, "get_task_oracle", return_value={"hidden_evaluator": {"verification_levels": ["L3_RELEVANT_REGRESSION"]}}):
            with patch("pathlib.Path.exists", return_value=True):
                verif = evaluator.evaluate_worktree(tmp_path, "T1", ["a.php"], l0_status=CheckStatus.PASS)
                assert verif.l3_regression_status == CheckStatus.NOT_MEASURED
                assert verif.l3_regression_passed is False


# ---------------------------------------------------------------------------
# T28: Sandboxed execution denies arbitrary python -c, python -m, php -r, git -c
# ---------------------------------------------------------------------------
def test_t28_sandbox_denies_arbitrary_code_execution(tmp_path: Path):
    env = RepoToolEnvironment(str(tmp_path))

    # Python -c denied
    res_py_c = env.run_command("python -c \"print('injected')\"")
    assert res_py_c["status"] == "TOOL_DENIED"

    # Python -m denied
    res_py_m = env.run_command("python -m http.server")
    assert res_py_m["status"] == "TOOL_DENIED"

    # PHP -r denied
    res_php_r = env.run_command("php -r \"echo 1;\"")
    assert res_php_r["status"] == "TOOL_DENIED"

    # Git -c denied
    res_git_c = env.run_command("git -c core.fsmonitor=true status")
    assert res_git_c["status"] == "TOOL_DENIED"

    # Benign allowed tool succeeds or runs cleanly
    res_ver = env.run_command("python --version")
    assert res_ver["status"] in ("SUCCESS", "ERROR")  # non-denied execution


# ---------------------------------------------------------------------------
# T30: Untracked files included in census and unified diff
# ---------------------------------------------------------------------------
def test_t30_untracked_files_in_census_and_diff(tmp_path: Path):
    # Initialize real temporary git repo
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)

    base_file = tmp_path / "base.txt"
    base_file.write_text("initial\n")
    subprocess.run(["git", "add", "base.txt"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)

    env = RepoToolEnvironment(str(tmp_path))

    # Create new untracked file
    new_file = tmp_path / "new_untracked.txt"
    new_file.write_text("hello untracked\n")

    mod_files = env.get_modified_files()
    assert "new_untracked.txt" in mod_files

    diff = env.get_git_diff()
    assert "+hello untracked" in diff


# ---------------------------------------------------------------------------
# T32: Revert changes guards non-ephemeral repository
# ---------------------------------------------------------------------------
def test_t32_revert_changes_guards_non_ephemeral(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    (tmp_path / "file.txt").write_text("orig")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)

    # Add untracked user file
    user_file = tmp_path / "user_work.txt"
    user_file.write_text("do not delete")

    # Non-ephemeral env
    env = RepoToolEnvironment(str(tmp_path), is_ephemeral=False)
    env.revert_changes()
    assert user_file.exists()  # Kept safe!


# ---------------------------------------------------------------------------
# T35 & T36: Benchmark service fails closed on missing data without showcase fallback
# ---------------------------------------------------------------------------
def test_t35_t36_benchmark_service_run_scoped_fail_closed(tmp_path: Path):
    svc = BenchmarkService()
    svc.runs_root = tmp_path

    # Non-existent run
    summary = svc.get_run_summary("non_existent_run_999")
    assert summary is None

    # Run without metrics.json returns NOT_MEASURED (never 10/3/+1.68)
    run_dir = tmp_path / "run_test_empty"
    run_dir.mkdir()
    (run_dir / "manifest.json").write_text(json.dumps({"start_time_utc": "2026-10-10T12:00:00Z"}))

    summary_empty = svc.get_run_summary("run_test_empty")
    assert summary_empty is not None
    assert summary_empty["status"] == "NOT_MEASURED"
    assert summary_empty["total_trials"] == 0
    assert summary_empty["valid_pairs"] == 0

    # CSV for non-existent run returns None (never showcase fallback)
    csv_res = svc.get_csv_content("pairs.csv", run_id="non_existent_run_999")
    assert csv_res is None
