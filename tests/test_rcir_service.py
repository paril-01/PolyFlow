"""Adversarial source identity, byte spans, delivery budgets and lifecycle checks."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rcir" / "src"))
from rcir.service import RepositoryService, ServiceError
from rcir.service.snapshot import canonical, digest, safe_path
from rcir.service.proof import seal_run, verify_run
from rcir.context.tokenizer import ApproximateCharTokenCounter


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT).decode().strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "RCIR test")
    git(tmp_path, "config", "core.autocrlf", "false")
    (tmp_path / "a.py").write_bytes('import b\r\nclass Alpha:\r\n    def calculate(self):\r\n        return "café"\r\n'.encode())
    (tmp_path / "b.py").write_text("import c\ndef beta():\n    return 2\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("import a\ndef gamma():\n    return 3\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "fixture")
    return tmp_path


def test_source_bytes_and_budget(repo):
    service = RepositoryService(repo)
    for budget in [500, 1000, 2000, 4000, 8000]:
        result = service.retrieve("calculate", budget)
        assert service.counter.count(canonical(result).decode()) == result["tokens_consumed"] <= budget
        for item in result["evidence_items"]:
            raw = (repo / item["file_path"]).read_bytes()
            span = raw[item["start_byte"]:item["end_byte"]]
            assert span == item["snippet"].encode()
            assert digest(span) == item["span_sha256"]
            assert digest(raw) == item["file_sha256"]
    item = service.retrieve("calculate", required_symbols=["Alpha.calculate"])["evidence_items"][0]
    assert item["symbol_name"] == "Alpha.calculate"
    expanded = service.expand(item["evidence_id"])
    assert expanded["evidence"] == item
    assert service.counter.count(canonical(expanded).decode()) == expanded["tokens_consumed"]


@pytest.mark.parametrize("budget", [0, -1, True, "4000", 1, 1_000_001])
def test_invalid_and_tiny_budgets(repo, budget):
    with pytest.raises(ServiceError) as error:
        RepositoryService(repo).retrieve("calculate", budget)
    assert error.value.status == "BUDGET_INSUFFICIENT"


def test_pinned_budget_and_missing_symbol(repo):
    service = RepositoryService(repo)
    with pytest.raises(ServiceError, match="Pinned"):
        service.retrieve("calculate", 100, required_symbols=["Alpha.calculate"])
    with pytest.raises(ServiceError) as error:
        service.retrieve("calculate", required_symbols=["missing"])
    assert error.value.status == "UNRESOLVED"


def test_ambiguous_symbol(repo):
    (repo / "duplicate.py").write_text("def beta():\n    return 8\n", encoding="utf-8")
    service = RepositoryService(repo, allow_overlay=True)
    with pytest.raises(ServiceError) as error:
        service.retrieve("beta", required_symbols=["beta"])
    assert error.value.status == "AMBIGUOUS"


def test_stale_refresh_and_restart(repo):
    service = RepositoryService(repo, allow_overlay=True)
    handle = service.retrieve("calculate")["evidence_items"][0]["evidence_id"]
    old_id = service.snapshot.id
    (repo / "a.py").write_text("def renamed():\n    return 4\n", encoding="utf-8")
    with pytest.raises(ServiceError) as error:
        service.expand(handle)
    assert error.value.status == "STALE"
    service.refresh()
    assert service.snapshot.id != old_id
    with pytest.raises(ServiceError):
        service.expand(handle)
    assert RepositoryService(repo, allow_overlay=True).snapshot.id == service.snapshot.id
    assert not any(s["symbol_name"] == "Alpha.calculate" for s in service.retrieve("calculate")["evidence_items"])
    (repo / "a.py").rename(repo / "renamed.py")
    with pytest.raises(ServiceError):
        service.retrieve("renamed")
    service.refresh()
    assert "renamed.py" in service.snapshot.files


def test_reverse_import_closure_and_cycle(repo):
    service = RepositoryService(repo)
    assert service.impact("c.py")["affected_files"] == ["a.py", "b.py"]
    assert service.impact("a.py")["affected_files"] == ["b.py", "c.py"]
    assert "PARTIAL" in service.impact("a.py")["completeness"]


@pytest.mark.parametrize("path", ["../escape.py", "C:/secret.py", "/root.py", "a/../../escape", "a.py:stream", "\\\\server\\file", "a//b", "a\x00.py"])
def test_path_scope(repo, path):
    with pytest.raises(ServiceError):
        safe_path(repo, path)


def test_exclusions_and_dirty_opt_in(repo):
    (repo / ".env.json").write_text('{"secret":"hidden"}')
    (repo / "oracle.json").write_text('{"answer":"hidden"}')
    (repo / "private").mkdir()
    (repo / "private" / "answer.py").write_text("secret = 1")
    with pytest.raises(ServiceError, match="Dirty"):
        RepositoryService(repo)
    service = RepositoryService(repo, allow_overlay=True)
    assert set(service.snapshot.files) == {"a.py", "b.py", "c.py"}


def test_symlink_exclusion(repo, tmp_path):
    outside = repo.parent / "outside.py"
    outside.write_text("secret = 1")
    try:
        (repo / "link.py").symlink_to(outside)
    except OSError:
        pytest.skip("OS did not grant symlink creation")
    service = RepositoryService(repo, allow_overlay=True)
    assert "link.py" not in service.snapshot.files
    with pytest.raises(ServiceError):
        safe_path(repo, "link.py")


def test_exact_tokenizer_required(repo):
    with pytest.raises(ServiceError, match="exact tokenizer"):
        RepositoryService(repo, counter=ApproximateCharTokenCounter())


def test_source_only_never_runs_host_git(repo, monkeypatch):
    from rcir.service.snapshot import Snapshot
    def prohibited(*args, **kwargs):
        raise AssertionError("Host Git must not inspect agent-controlled metadata")
    monkeypatch.setattr(Snapshot, "_git", prohibited)
    service = RepositoryService(repo, allow_unversioned=True, source_only=True)
    assert service.snapshot.commit is None
    assert service.retrieve("calculate")["evidence_items"]
    assert ".git/config" not in service.snapshot.files


def test_concurrent_consistency(repo):
    service = RepositoryService(repo)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: service.retrieve("calculate"), range(8)))
    assert all(r == results[0] for r in results)


def test_handle_eviction(repo):
    service = RepositoryService(repo, cache_entries=1)
    item = service.retrieve("calculate")["evidence_items"][0]
    service.retrieve("gamma")
    with pytest.raises(ServiceError) as error:
        service.expand(item["evidence_id"])
    assert error.value.status == "UNRESOLVED"


def test_proof_inventory_and_mutation(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "integrity.json").write_text("nested artifact")
    assert seal_run(tmp_path)["files"] == 1
    assert verify_run(tmp_path)["signature"] is False
    with pytest.raises(ServiceError):
        seal_run(tmp_path)
    (tmp_path / "nested" / "integrity.json").write_text("mutated")
    with pytest.raises(ServiceError):
        verify_run(tmp_path)


def test_proof_extra_file(tmp_path):
    (tmp_path / "receipt.json").write_text("{}")
    seal_run(tmp_path)
    (tmp_path / "extra").write_text("unexpected")
    with pytest.raises(ServiceError):
        verify_run(tmp_path)
