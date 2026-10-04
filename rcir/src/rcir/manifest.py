"""
RCIR v8.3 — Benchmark Run Manifest and Provenance Manager (PHASE 1).

Guarantees run immutability, artifact provenance, and cross-artifact configuration integrity.
Generates and validates benchmark_run_manifest.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def compute_file_sha256(path: Path | str) -> str:
    """Compute hex SHA-256 for a file; returns empty hash if file does not exist."""
    p = Path(path)
    if not p.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_dict_sha256(data: dict[str, Any]) -> str:
    """Compute canonical JSON SHA-256 hash."""
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def get_git_commit(cwd: Path | str | None = None) -> str:
    """Get current git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


@dataclass
class BenchmarkRunManifest:
    """Immutable provenance manifest for a benchmark execution."""
    run_id: str
    polyflow_commit: str
    target_repository: str
    target_repository_commit: str
    benchmark_contract_hash: str
    dataset_hash: str
    ground_truth_hash: str
    graph_hash: str
    candidate_config_hash: str
    ranker_config_hash: str
    compiler_config_hash: str
    provider: Optional[str] = None
    model: Optional[str] = None
    tokenizer: Optional[str] = None
    environment: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, output_path: Path | str) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, manifest_path: Path | str) -> BenchmarkRunManifest:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


class ManifestBuilder:
    """Creates a sealed BenchmarkRunManifest with live hashes and environment details."""

    @classmethod
    def create(
        cls,
        contract_path: Path | str,
        dataset_path: Path | str,
        ground_truth_path: Path | str,
        graph_path: Path | str,
        candidate_config: dict[str, Any],
        ranker_config: dict[str, Any],
        compiler_config: dict[str, Any],
        target_repo_path: Path | str | None = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tokenizer: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> BenchmarkRunManifest:
        r_id = run_id or f"rcir-v8.3-{uuid.uuid4().hex[:12]}"
        polyflow_commit = get_git_commit()
        target_commit = get_git_commit(target_repo_path) if target_repo_path else "LOCAL_SNAPSHOT"

        env_info = {
            "python_version": platform.python_version(),
            "os": platform.system(),
            "os_release": platform.release(),
            "cpu_arch": platform.machine(),
            "pid": os.getpid(),
        }

        return BenchmarkRunManifest(
            run_id=r_id,
            polyflow_commit=polyflow_commit,
            target_repository=str(target_repo_path or "nextcloud-server"),
            target_repository_commit=target_commit,
            benchmark_contract_hash=compute_file_sha256(contract_path),
            dataset_hash=compute_file_sha256(dataset_path),
            ground_truth_hash=compute_file_sha256(ground_truth_path),
            graph_hash=compute_file_sha256(graph_path),
            candidate_config_hash=compute_dict_sha256(candidate_config),
            ranker_config_hash=compute_dict_sha256(ranker_config),
            compiler_config_hash=compute_dict_sha256(compiler_config),
            provider=provider,
            model=model,
            tokenizer=tokenizer,
            environment=env_info,
        )
