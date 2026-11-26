"""
showcase_app/backend/services/evidence_registry.py — Allow-listed Proof & Evidence Registry.

Provides secure access to frozen and measured benchmark artifacts.
Guards against path traversal, absolute path leakage, and SHA-256 tampering.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class EvidenceRegistry:
    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = (repo_root or REPO_ROOT).resolve()
        self.run_id = "run_20261009_blind_verified"
        self.proof_index_file = self.repo_root / "experiments" / "runs" / self.run_id / "proof_index.json"
        if not self.proof_index_file.exists():
            self.proof_index_file = self.repo_root / "showcase" / "data" / "proof_index.json"
        
        self.proofs_by_id: Dict[str, Dict[str, Any]] = {}
        self.reload_proofs()

    def reload_proofs(self) -> None:
        # Never retain previously loaded evidence after index deletion or corruption.
        self.proofs_by_id = {}
        try:
            data = json.loads(self.proof_index_file.read_text(encoding="utf-8"))
            proofs = data["proofs"]
            if data.get("run_id") != self.run_id or not isinstance(proofs, list):
                return
            loaded = {}
            for proof in proofs:
                if not isinstance(proof, dict):
                    return
                proof_id = proof.get("proof_id")
                if not isinstance(proof_id, str) or not proof_id or proof_id in loaded:
                    return
                loaded[proof_id] = proof
            self.proofs_by_id = loaded
        except (OSError, ValueError, KeyError, TypeError):
            return

    def get_all_proofs(self) -> List[Dict[str, Any]]:
        self.reload_proofs()
        listed = []
        for proof in self.proofs_by_id.values():
            verified = self._read_verified(proof)
            if verified is None:
                listed.append({**proof, "availability_status": "UNAVAILABLE",
                               "availability_reason": "MISSING_OR_INVALID_EVIDENCE",
                               "validity_status": "UNAVAILABLE"})
            else:
                listed.append(verified[2])
        return listed

    def _contained_path(self, base: Path, value: Any) -> Optional[Path]:
        if not isinstance(value, str) or not value or "\x00" in value or ":" in value:
            return None
        normalized = value.replace("\\", "/")
        if (PurePosixPath(normalized).is_absolute()
                or PureWindowsPath(value).anchor
                or any(part in ("", ".", "..") for part in normalized.split("/"))):
            return None
        candidate = base / normalized
        try:
            candidate.resolve().relative_to(base.resolve())
            candidate.resolve().relative_to(self.repo_root)
            # Proofs are ordinary files; symlink aliases are not evidence authority.
            for component in (candidate, *candidate.parents):
                if component == self.repo_root:
                    break
                if component.is_symlink():
                    return None
        except (OSError, ValueError, RuntimeError):
            return None
        return candidate

    def _read_verified(self, proof: Dict[str, Any]) -> Optional[tuple[Path, bytes, Dict[str, Any]]]:
        expected_hash = proof.get("sha256")
        if (not isinstance(expected_hash, str) or len(expected_hash) != 64
                or any(char not in "0123456789abcdef" for char in expected_hash)):
            return None
        primary = self._contained_path(self.repo_root, proof.get("source_file"))
        run_root = self.repo_root / "experiments" / "runs" / self.run_id
        fallback = self._contained_path(run_root, proof.get("rel_path"))
        # Validate BOTH paths, including fallback, before opening either file.
        if primary is None or fallback is None:
            return None
        file_path = primary if primary.is_file() else fallback
        try:
            if not file_path.is_file():
                return None
            content = file_path.read_bytes()
        except OSError:
            return None
        raw_hash = hashlib.sha256(content).hexdigest()
        policy = "RAW_SHA256_V1"
        if raw_hash != expected_hash:
            # The frozen 20261009 index recorded CRLF checkout bytes. Reconstruct
            # exactly those bytes from UTF-8 LF text, never replace its digest or
            # claim a canonicalized file's raw bytes matched the historical hash.
            if b"\x00" in content or b"\r" in content:
                return None
            try:
                content.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                return None
            content = content.replace(b"\n", b"\r\n")
            if hashlib.sha256(content).hexdigest() != expected_hash:
                return None
            policy = "LEGACY_CRLF_RECONSTRUCTION_V1"
        metadata = {**proof, "availability_status": "AVAILABLE",
                    "raw_sha256": raw_hash, "delivery_hash_policy": policy}
        return file_path, content, metadata

    def read_proof(self, proof_id: str) -> Optional[tuple[bytes, Dict[str, Any], str]]:
        """Return the verified bytes themselves so HTTP never reopens the file."""
        self.reload_proofs()
        proof = self.proofs_by_id.get(proof_id)
        verified = self._read_verified(proof) if proof else None
        if verified is None:
            return None
        path, content, metadata = verified
        return content, metadata, path.name

    def resolve_proof_file(self, proof_id: str) -> Optional[tuple[Path, Dict[str, Any]]]:
        """Compatibility lookup; use read_proof for hash-verified delivery bytes.

        For legacy LF checkouts, metadata explicitly distinguishes raw_sha256
        from the recorded digest of the reconstructed CRLF delivery.
        """
        self.reload_proofs()
        proof = self.proofs_by_id.get(proof_id)
        if not proof:
            return None

        verified = self._read_verified(proof)
        if verified is None:
            return None
        return verified[0], verified[2]


evidence_registry = EvidenceRegistry()
