import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "rcir/src")]
from rcir.context.tokenizer import TiktokenTokenCounter
from rcir.service import ServiceError
from rcir.service.snapshot import digest
from rcir.service.delivery import DeliveryScope, SupplementaryDelivery
from experiments.benchmark_core.product_study import export_base, counterbalanced_schedule, summarize_trials, validate_protocol, LinuxSandbox
from experiments.benchmark_core.retrieval_study import run_study, score_spans


def test_delivery_default_and_protection():
    scope = DeliveryScope("owner", "snapshot", "policy")
    raw = b"Repeated line\n" * 100
    delivery = SupplementaryDelivery(TiktokenTokenCounter())
    assert delivery.present(raw, "log", scope, 1000)["view"].encode() == raw
    delivery.enabled = True
    for kind in ["source", "instructions", "test_result", "security"]:
        assert delivery.present(raw, kind, scope, 1000)["view"].encode() == raw
    assert delivery.present(raw, "log", scope, 1000, protected=True)["lossy"] is False
    view = delivery.present(raw, "log", scope, 1000)
    assert view["lossy"] is True
    assert delivery.restore(view["restore_handle"], scope) == raw
    with pytest.raises(ServiceError):
        delivery.restore(view["restore_handle"], DeliveryScope("other", "snapshot", "policy"))
    with pytest.raises(ServiceError):
        delivery.present(raw, "source", scope, 1)


def test_delivery_expiration_and_lru():
    now = [0]
    scope = DeliveryScope("a", "b", "c")
    delivery = SupplementaryDelivery(TiktokenTokenCounter(), enabled=True, max_entries=1, clock=lambda: now[0], ttl_seconds=1)
    one = delivery.present(b"one\n" * 100, "log", scope, 1000)["restore_handle"]
    two = delivery.present(b"two\n" * 100, "log", scope, 1000)["restore_handle"]
    assert one is not None and two is not None
    with pytest.raises(ServiceError):
        delivery.restore(one, scope)
    now[0] = 2
    with pytest.raises(ServiceError):
        delivery.restore(two, scope)


def make_repo(root):
    root.mkdir()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT).decode().strip()
    git("init")
    git("config", "user.name", "fixture")
    git("config", "user.email", "test@example.invalid")
    git("config", "core.autocrlf", "false")
    (root / "worker.py").write_bytes(b"def target():\n    return 1\n")
    git("add", ".")
    git("commit", "-m", "base")
    return git("rev-parse", "HEAD"), git


def test_export_hides_future_git_history(tmp_path):
    root = tmp_path / "repo"
    base, git = make_repo(root)
    (root / "future_answer.py").write_text("secret_fix = True")
    git("add", ".")
    git("commit", "-m", "future answer")
    output = tmp_path / "trial"
    receipt = export_base(root, base, output)
    assert receipt["git_objects_exposed"] is False
    assert set(p.name for p in output.iterdir()) == {"worker.py"}
    with pytest.raises(ServiceError):
        export_base(root, base, output)


def test_counterbalancing_reproducible():
    args = (["a", "b", "c", "d"], ["A", "B", "C", "D"], 2, 7)
    rows = counterbalanced_schedule(*args)
    assert rows == counterbalanced_schedule(*args)
    assert len({r["namespace"] for r in rows}) == 32
    first = [r["arm"] for r in rows if r["position"] == 0 and r["replicate"] == 0]
    assert sorted(first) == ["A", "B", "C", "D"]


def test_no_zero_success_or_missing_usage_savings():
    rows = [{"task_id": "task", "replicate": 0, "arm": arm, "success": False, "native_input_tokens": None} for arm in ["A", "B"]]
    assert summarize_trials(rows)["secondary_mean_input_reduction"] is None
    for row in rows:
        row["success"] = True
    assert summarize_trials(rows)["efficiency_status"] == "NOT_MEASURED"
    rows[0]["native_input_tokens"], rows[1]["native_input_tokens"] = 100, 80
    assert summarize_trials(rows)["secondary_mean_input_reduction"] == .2
    with pytest.raises(ServiceError):
        summarize_trials(rows + rows)


def test_task_cluster_bootstrap():
    rows = [{"task_id": task, "replicate": repeat, "arm": arm, "success": True, "native_input_tokens": tokens}
            for task in ["one", "two"] for repeat in range(2) for arm, tokens in [("A", 100), ("B", 80)]]
    result = summarize_trials(rows, resamples=100)
    assert result["task_cluster_bootstrap_95_interval"] == [.2, .2]
    assert result["both_success_task_clusters_with_native_usage"] == 2
    assert result["native_ide_credits"] is None


def test_planned_missing_trials_stay_in_itt():
    planned = counterbalanced_schedule(["task"], ["A", "B"], 1, 0)
    result = summarize_trials([{"task_id": "task", "replicate": 0, "arm": "A", "success": True}], expected_schedule=planned)
    assert result["missing_planned_trials"] == 1
    assert result["itt"]["B"] == {"trials": 1, "successes": 0}
    assert result["itt_scope"] == "PREREGISTERED_SCHEDULE"


def test_protocol_refuses_missing_independent_curator():
    with pytest.raises(ServiceError):
        validate_protocol({"tasks": []}, {}, {})
    with pytest.raises(ServiceError, match="curator"):
        validate_protocol({"tasks": [{"task_id": "task"}]}, {}, {})


def test_no_host_sandbox_fallback(tmp_path, monkeypatch):
    import experiments.benchmark_core.product_study as study
    monkeypatch.setattr(study.shutil, "which", lambda _: None)
    with pytest.raises(ServiceError, match="host execution refused"):
        LinuxSandbox(tmp_path)


def test_exact_path_and_complete_span_scoring():
    gold = [{"path": "real/file.py", "start_line": 4, "end_line": 8}]
    assert score_spans([{"file_path": "other/file.py", "start_line": 1, "end_line": 20}], gold)["critical_span_recall"] == 0
    assert score_spans([{"file_path": "real/file.py", "start_line": 4, "end_line": 6}], gold)["critical_span_recall"] == 0


def test_retrieval_runner_real_source_and_no_hint_leak(tmp_path):
    root = tmp_path / "repo"
    commit, git = make_repo(root)
    public = tmp_path / "public.json"
    gold = tmp_path / "gold.json"
    public.write_text(json.dumps({"tasks": [{"task_id": "dev-example", "query": "target"}]}))
    gold.write_text(json.dumps({"dev-example": [{"path": "worker.py", "start_line": 1, "end_line": 2,
                                                 "file_sha256": digest((root / "worker.py").read_bytes())}]}))
    result = run_study(root, commit, public, gold, tmp_path / "run", arms=["R0", "R2"])
    assert len(result["records"]) == 8
    assert result["winner"] is None
    assert all(r["delivery"]["query"] == "target" for r in result["records"])
    assert all(r["critical_span_recall"] == 1 for r in result["records"])
    with pytest.raises(ServiceError):
        run_study(root, commit, public, gold, tmp_path / "run")
    with pytest.raises(ServiceError, match="canonical graph"):
        run_study(root, commit, public, gold, tmp_path / "missing-graph", arms=["R1"])
    public.write_text('{"tasks":[]}')
    with pytest.raises(ServiceError):
        run_study(root, commit, public, gold, tmp_path / "empty")


def test_canonical_entries_and_hybrid_no_fallback(tmp_path):
    root = tmp_path / "repo"
    commit, _ = make_repo(root)
    public, gold, graph = [tmp_path / name for name in ["public.json", "gold.json", "graph.json"]]
    public.write_text(json.dumps({"tasks": [{"task_id": "dev", "query": "target"}]}))
    gold.write_text(json.dumps({"dev": [{"path": "worker.py", "start_line": 1, "end_line": 2,
                                         "file_sha256": digest((root / "worker.py").read_bytes())}]}))
    data = {"metadata": {"target_commit": commit}, "nodes": {"python://worker:target": {"file": "worker.py", "line": 1, "end_line": 2}}, "edges": []}
    graph.write_text(json.dumps(data))
    receipt = run_study(root, commit, public, gold, tmp_path / "canonical", arms=["R0", "R1", "R2", "R3"], graph=graph)
    assert all(row["critical_span_recall"] == 1 for row in receipt["records"])
    data["metadata"]["target_commit"] = "0" * 40
    graph.write_text(json.dumps(data))
    with pytest.raises(ServiceError, match="identity"):
        run_study(root, commit, public, gold, tmp_path / "wrong-graph", arms=["R1"], graph=graph)


def test_patch_capture_is_independent_of_agent_git(tmp_path):
    from experiments.benchmark_core.agent_trial import source_census, complete_patch, LocalOllama
    root = tmp_path / "trial"
    root.mkdir()
    (root / "before.py").write_bytes(b"old\n")
    (root / "delete.py").write_bytes(b"delete\n")
    baseline = source_census(root)
    (root / "before.py").write_bytes(b"new\n")
    (root / "delete.py").unlink()
    (root / "untracked.bin").write_bytes(b"\x00binary")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("untrusted Git config must never execute on host")
    patch, changes = complete_patch(root, baseline)
    assert {c["path"] for c in changes} == {"before.py", "delete.py", "untracked.bin"}
    assert b"-old" in patch and b"+new" in patch
    import base64
    binary = next(c for c in changes if c["path"] == "untracked.bin")
    assert base64.b64decode(binary["after_base64"]) == b"\x00binary"
    for endpoint in ["https://api.example.com", "http://evil.test", "http://user:password@localhost", "http://127.0.0.1?redirect=evil"]:
        with pytest.raises(ServiceError):
            LocalOllama(endpoint, "model")
