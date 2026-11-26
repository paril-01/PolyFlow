"""Synthetic adversarial fixtures for proof integrity, not benchmark evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from showcase_app.backend.services.evidence_registry import EvidenceRegistry


@pytest.fixture
def registry(tmp_path):
    run = tmp_path / "experiments/runs/run_20261009_blind_verified"
    run.mkdir(parents=True)
    registry = EvidenceRegistry(tmp_path)
    registry.proof_index_file = run / "proof_index.json"
    return registry


def publish(registry, content=b"proof\n", expected=None, **updates):
    path = registry.proof_index_file.parent / "proof.txt"
    path.write_bytes(content)
    proof = dict(proof_id="sample", source_file=path.relative_to(registry.repo_root).as_posix(),
                 rel_path="proof.txt", sha256=expected or hashlib.sha256(content).hexdigest(),
                 mime_type="text/plain", validity_status="VALIDATED")
    proof.update(updates)
    registry.proof_index_file.write_text(json.dumps(dict(run_id=registry.run_id, proofs=[proof])), encoding="utf-8")
    return path, proof


@pytest.mark.parametrize("content", [b"proof\n", b"proof\r\n", "π 雪\n".encode(), b"\x00\xff\n\r\n"])
def test_raw_bytes_and_digest_are_preserved(registry, content):
    publish(registry, content)
    served, metadata, name = registry.read_proof("sample")
    assert served == content
    assert hashlib.sha256(served).hexdigest() == metadata["sha256"]
    assert metadata["delivery_hash_policy"] == "RAW_SHA256_V1"
    assert name == "proof.txt"


def test_legacy_lf_checkout_serves_exact_recorded_crlf_bytes(registry):
    disk = "π 雪\nline two\n".encode()
    historical = disk.replace(b"\n", b"\r\n")
    path, _ = publish(registry, disk, expected=hashlib.sha256(historical).hexdigest())
    served, metadata, _ = registry.read_proof("sample")
    assert served == historical
    assert metadata["delivery_hash_policy"] == "LEGACY_CRLF_RECONSTRUCTION_V1"
    assert metadata["raw_sha256"] == hashlib.sha256(disk).hexdigest()
    assert path.read_bytes() == disk  # No rewrite of source evidence.


def test_crlf_checkout_serves_exact_recorded_lf_bytes(registry):
    historical = "π 雪\nline two\n".encode()
    disk = historical.replace(b"\n", b"\r\n")
    path, _ = publish(registry, disk, expected=hashlib.sha256(historical).hexdigest())
    served, metadata, _ = registry.read_proof("sample")
    assert served == historical
    assert metadata["delivery_hash_policy"] == "LEGACY_LF_RECONSTRUCTION_V1"
    assert path.read_bytes() == disk


@pytest.mark.parametrize("content", [b"\x00proof\n", b"\xffproof\n", b"mixed\r\nlines\n"])
def test_non_utf8_binary_and_mixed_endings_are_not_reconstructed(registry, content):
    publish(registry, content, expected=hashlib.sha256(content.replace(b"\n", b"\r\n")).hexdigest())
    assert registry.read_proof("sample") is None


def test_same_length_tampering_is_unavailable(registry):
    path, _ = publish(registry, b"original\n")
    path.write_bytes(b"tampered\n")
    assert registry.read_proof("sample") is None
    listed = registry.get_all_proofs()[0]
    assert listed["availability_status"] == "UNAVAILABLE"
    assert listed["validity_status"] == "UNAVAILABLE"


@pytest.mark.parametrize("digest", [None, "", "not-a-hash", "0" * 64])
def test_missing_invalid_or_wrong_hash_never_served(registry, digest):
    publish(registry, sha256=digest)
    assert registry.read_proof("sample") is None


@pytest.mark.parametrize("field", ["source_file", "rel_path"])
@pytest.mark.parametrize("unsafe", ["../outside.txt", "nested/../../outside.txt", "/etc/passwd", "C:/secret.txt", "C:secret.txt", "\\\\host\\share\\file", "\\secret.txt", "file.txt:stream", "", "a\x00b"])
def test_both_primary_and_fallback_paths_are_validated(registry, field, unsafe):
    publish(registry, **{field: unsafe})
    assert registry.read_proof("sample") is None


def test_fallback_can_only_read_within_run(registry):
    _, proof = publish(registry, source_file="missing/proof.txt")
    assert registry.read_proof("sample")[0] == b"proof\n"
    assert registry.resolve_proof_file("sample")[1]["sha256"] == proof["sha256"]


def test_missing_file_and_unknown_id_are_unavailable(registry):
    path, _ = publish(registry)
    path.unlink()
    assert registry.read_proof("sample") is None
    assert registry.read_proof("unknown") is None
    assert registry.resolve_proof_file("../../secret") is None
    assert registry.get_all_proofs()[0]["availability_status"] == "UNAVAILABLE"


@pytest.mark.parametrize("replacement", [None, "invalid-json", '{}', '{"proofs": [null]}'])
def test_index_reload_clears_stale_records(registry, replacement):
    publish(registry)
    assert registry.read_proof("sample")
    if replacement is None:
        registry.proof_index_file.unlink()
    else:
        registry.proof_index_file.write_text(replacement)
    assert registry.read_proof("sample") is None
    assert registry.get_all_proofs() == []


def test_duplicate_ids_fail_closed(registry):
    _, proof = publish(registry)
    registry.proof_index_file.write_text(json.dumps(dict(run_id=registry.run_id, proofs=[proof, proof])))
    assert registry.get_all_proofs() == []


@pytest.mark.parametrize("field", ["source_file", "rel_path"])
def test_symlink_escape_is_rejected(registry, tmp_path, field):
    path, _ = publish(registry)
    outside = tmp_path.parent / (tmp_path.name + "-outside.txt")
    outside.write_bytes(path.read_bytes())
    link = registry.proof_index_file.parent / "link.txt"
    try:
        try:
            link.symlink_to(outside)
        except OSError as exc:
            pytest.skip(f"Symlinks unavailable on this host: {exc}")
        value = link.relative_to(registry.repo_root).as_posix() if field == "source_file" else "link.txt"
        publish(registry, **{field: value})
        assert registry.read_proof("sample") is None
    finally:
        outside.unlink(missing_ok=True)


def test_download_uses_verified_bytes_after_disk_changes(registry, monkeypatch):
    from fastapi.testclient import TestClient
    from showcase_app.backend.app import app
    from showcase_app.backend.api import proofs

    path, _ = publish(registry)
    original_reader = registry.read_proof

    def read_then_change(proof_id):
        result = original_reader(proof_id)
        path.write_bytes(b"tampered after verification")
        return result

    monkeypatch.setattr(registry, "read_proof", read_then_change)
    monkeypatch.setattr(proofs, "evidence_registry", registry)
    response = TestClient(app).get("/api/proofs/sample/download")
    assert response.status_code == 200
    assert response.content == b"proof\n"


def test_health_never_validates_missing_evidence(registry, monkeypatch):
    from fastapi.testclient import TestClient
    from showcase_app.backend.app import app
    from showcase_app.backend.api import proofs

    monkeypatch.setattr(proofs, "evidence_registry", registry)
    assert TestClient(app).get("/api/health").json()["evidence_status"] == "NOT_EVALUATED_BY_HEALTH"


def test_every_frozen_proof_from_lf_git_blobs(registry):
    """Reproduce LF checkout bytes on Windows without modifying frozen evidence."""
    root = Path(__file__).resolve().parents[1]
    index_path = "experiments/runs/run_20261009_blind_verified/proof_index.json"
    index = json.loads(subprocess.run(["git", "show", f"HEAD:{index_path}"], cwd=root,
                                     capture_output=True, check=True).stdout)
    registry.proof_index_file.write_text(json.dumps(index))
    for proof in index["proofs"]:
        blob = subprocess.run(["git", "show", f"HEAD:{proof['source_file']}"],
                              cwd=root, capture_output=True, check=True).stdout
        target = registry.repo_root / proof["source_file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        result = registry.read_proof(proof["proof_id"])
        assert result is not None, proof["proof_id"]
        content, metadata, _ = result
        assert hashlib.sha256(content).hexdigest() == proof["sha256"]
        assert metadata["sha256"] == proof["sha256"]
        assert target.read_bytes() == blob
