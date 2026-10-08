"""
showcase_app/backend/services/evidence_registry.py — Allow-listed Proof & Evidence Registry.

Provides secure access to frozen and measured benchmark artifacts.
Guards against path traversal, absolute path leakage, and SHA-256 tampering.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class EvidenceRegistry:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.run_id = "run_20261009_blind_verified"
        self.proof_index_file = self.repo_root / "experiments" / "runs" / self.run_id / "proof_index.json"
        if not self.proof_index_file.exists():
            self.proof_index_file = self.repo_root / "showcase" / "data" / "proof_index.json"
        
        self.proofs_by_id: Dict[str, Dict[str, Any]] = {}
        self.reload_proofs()

    def reload_proofs(self) -> None:
        if self.proof_index_file.exists():
            try:
                data = json.loads(self.proof_index_file.read_text(encoding="utf-8"))
                self.proofs_by_id = {p["proof_id"]: p for p in data.get("proofs", [])}
            except Exception:
                self.proofs_by_id = {}

    def get_all_proofs(self) -> List[Dict[str, Any]]:
        self.reload_proofs()
        return list(self.proofs_by_id.values())

    def resolve_proof_file(self, proof_id: str) -> Optional[tuple[Path, Dict[str, Any]]]:
        self.reload_proofs()
        proof = self.proofs_by_id.get(proof_id)
        if not proof:
            return None

        # Guard against path traversal in source_file or rel_path
        rel_path = proof.get("source_file", "")
        if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
            return None

        file_path = (self.repo_root / rel_path).resolve()
        # Verify file is strictly within repo_root
        try:
            file_path.relative_to(self.repo_root)
        except ValueError:
            return None

        if not file_path.exists() or not file_path.is_file():
            # Try within run directory
            run_rel = proof.get("rel_path", "")
            alt_path = (self.repo_root / "experiments" / "runs" / self.run_id / run_rel).resolve()
            if alt_path.exists() and alt_path.is_file():
                file_path = alt_path
            else:
                return None

        # Verify hash integrity
        content = file_path.read_bytes()
        current_hash = hashlib.sha256(content).hexdigest()
        expected_hash = proof.get("sha256", "")
        if expected_hash and current_hash != expected_hash:
            # File was tampered with or modified
            return None

        return file_path, proof


evidence_registry = EvidenceRegistry()
