"""Hash-bound run artifacts. A digest is integrity, not a signature or success proof."""
from pathlib import Path
import json
import re

from .snapshot import ServiceError, canonical, digest, safe_path


def seal_run(run):
    root = Path(run).resolve()
    target = root / "integrity.json"
    if target.exists():
        raise ServiceError("INVALID_SCOPE", "Refusing to overwrite sealed run")
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ServiceError("INVALID_SCOPE", "Symlink in run artifacts")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            safe_path(root, relative)
            files[relative] = digest(path.read_bytes())
    target.write_bytes(canonical({"schema": "rcir.run_integrity.v1", "method": "SHA256_NOT_SIGNATURE", "files": files}))
    return verify_run(root)


def verify_run(run):
    root = Path(run).resolve()
    if (root / "integrity.json").is_symlink():
        raise ServiceError("INVALID_SCOPE", "Run inventory may not be a symlink")
    manifest = json.loads((root / "integrity.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "rcir.run_integrity.v1" or not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise ServiceError("INVALID_SCOPE", "Missing run integrity inventory")
    if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in manifest["files"].values()):
        raise ServiceError("INVALID_SCOPE", "Run inventory requires exact SHA-256 values")
    if any(p.is_symlink() for p in root.rglob("*")):
        raise ServiceError("INVALID_SCOPE", "Symlink in run artifacts")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != root / "integrity.json"}
    if actual != set(manifest["files"]):
        raise ServiceError("STALE", "Run artifact inventory changed")
    for path, expected in manifest["files"].items():
        file = safe_path(root, path)
        if digest(file.read_bytes()) != expected:
            raise ServiceError("STALE", "Run artifact hash mismatch")
    return {"status": "INTEGRITY_VERIFIED", "files": len(actual), "signature": False,
            "benchmark_success": "NOT_DETERMINED_BY_HASHES"}
