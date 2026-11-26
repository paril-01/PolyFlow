"""Fresh Linux checks using real LF Git blobs; no model or benchmark claims."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from showcase_app.backend.services.evidence_registry import EvidenceRegistry

assert sys.platform == "linux", sys.platform
print("PLATFORM", sys.platform, sys.version)
with tempfile.TemporaryDirectory(prefix="polyflow-proof-linux-") as directory:
    root = Path(directory)
    run = root / "experiments/runs/run_20261009_blind_verified"
    run.mkdir(parents=True)
    registry = EvidenceRegistry(root)
    registry.proof_index_file = run / "proof_index.json"
    index_path = "experiments/runs/run_20261009_blind_verified/proof_index.json"
    index = json.loads(subprocess.run(["git", "show", f"HEAD:{index_path}"], cwd=ROOT,
                                     capture_output=True, check=True).stdout)
    registry.proof_index_file.write_text(json.dumps(index))
    for proof in index["proofs"]:
        blob = subprocess.run(["git", "show", f"HEAD:{proof['source_file']}"], cwd=ROOT,
                              capture_output=True, check=True).stdout
        path = root / proof["source_file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        verified = registry.read_proof(proof["proof_id"])
        assert verified is not None, proof["proof_id"]
        assert hashlib.sha256(verified[0]).hexdigest() == proof["sha256"]
        assert path.read_bytes() == blob
        print("PASS LF_GIT_BLOB", proof["proof_id"], verified[1]["delivery_hash_policy"])
    first = index["proofs"][0]
    path = root / first["source_file"]
    original = path.read_bytes()
    path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    assert registry.read_proof(first["proof_id"]) is None
    print("PASS SAME_LENGTH_TAMPER_REJECTED")
    path.write_bytes(original)
    outside = root / "outside.txt"
    outside.write_bytes(original)
    for field in ["source_file", "rel_path"]:
        modified = {**first, field: "../../../../outside.txt"}
        registry.proof_index_file.write_text(json.dumps(dict(run_id=registry.run_id, proofs=[modified])))
        assert registry.read_proof(first["proof_id"]) is None
        print("PASS TRAVERSAL_REJECTED", field)
    link = run / "link.txt"
    link.symlink_to(outside)
    for field in ["source_file", "rel_path"]:
        value = link.relative_to(root).as_posix() if field == "source_file" else "link.txt"
        modified = {**first, field: value}
        registry.proof_index_file.write_text(json.dumps(dict(run_id=registry.run_id, proofs=[modified])))
        assert registry.read_proof(first["proof_id"]) is None
        print("PASS SYMLINK_REJECTED", field)
    registry.proof_index_file.unlink()
    assert registry.get_all_proofs() == []
    print("PASS DELETED_INDEX_CLEARS_STATE")
print("LINUX_PROOF_SMOKE_COMPLETE: 18 frozen proofs and 6 negative checks")
