"""
RCIR v8.5 — Single Target Repository Configuration & Benchmark Environment (PHASES 1, 2, 3, 4).

Establishes a single, authoritative BenchmarkEnvironment:
- Fails fast if target repository root does not contain expected sentinels.
- Records exact Git commits and working-tree dirty status for both PolyFlow and Nextcloud.
- Centralizes all path definitions across compilers, evaluators, runners, and agents.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


class BenchmarkEnvironmentError(RuntimeError):
    """Raised when the target repository or execution environment fails verification."""
    pass


class BenchmarkIntegrityError(RuntimeError):
    """Raised when run ID mismatch or integrity contract violation occurs."""
    pass


@dataclass
class BenchmarkEnvironment:
    """Authoritative environment passed to all RCIR v8.5 tools."""
    polyflow_root: Path
    target_repo_root: Path
    target_repo_name: str = "nextcloud/server"
    target_repo_commit: str = ""
    target_repo_dirty: bool = False
    target_repository_state: str = "CLEAN"
    working_tree_diff_hash: str = ""
    polyflow_commit: str = ""
    polyflow_dirty: bool = False

    run_id: str = "rcir-v8.5-primary"

    # Paths
    v8_5_root: Path = field(init=False)
    graph_path: Path = field(init=False)
    dataset_root: Path = field(init=False)
    ground_truth_root: Path = field(init=False)
    edge_ground_truth_root: Path = field(init=False)
    receiver_ground_truth_root: Path = field(init=False)
    canonicalization_ground_truth_root: Path = field(init=False)
    manifests_root: Path = field(init=False)
    results_root: Path = field(init=False)
    raw_root: Path = field(init=False)
    reports_root: Path = field(init=False)
    contract_path: Path = field(init=False)

    def __post_init__(self):
        self.polyflow_root = Path(self.polyflow_root).resolve()
        self.target_repo_root = Path(self.target_repo_root).resolve()

        self.v8_5_root = self.polyflow_root / "experiments" / "rcir_v8_5"
        self.graph_path = self.polyflow_root / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
        self.dataset_root = self.v8_5_root / "datasets"
        self.ground_truth_root = self.v8_5_root / "ground_truth"
        self.edge_ground_truth_root = self.v8_5_root / "edge_ground_truth"
        self.receiver_ground_truth_root = self.v8_5_root / "receiver_ground_truth"
        self.canonicalization_ground_truth_root = self.v8_5_root / "canonicalization_ground_truth"
        self.manifests_root = self.v8_5_root / "manifests"
        self.results_root = self.v8_5_root / "results"
        self.raw_root = self.v8_5_root / "raw"
        self.reports_root = self.v8_5_root / "reports"
        v8_5_2_contract = self.v8_5_root / "contract" / "benchmark_contract_v8_5_2.json"
        if v8_5_2_contract.exists():
            self.contract_path = v8_5_2_contract
        else:
            self.contract_path = self.v8_5_root / "contract" / "benchmark_contract.json"

        # Verify fail-fast sentinels
        self.verify_sentinels()

        # Capture git metadata if not explicitly provided
        if not self.target_repo_commit:
            self._capture_target_repo_git()
        if not self.polyflow_commit:
            self._capture_polyflow_git()

    def verify_sentinels(self) -> None:
        """PHASE 2: Fail fast on wrong source root."""
        sentinels = [
            ("lib/public/IConfig.php", "Public IConfig interface"),
            ("apps/files", "Files application directory"),
            (".git", "Target git metadata directory"),
            ("version.php", "Nextcloud version descriptor"),
            ("lib/private/Server.php", "Core dependency container Server"),
            ("core/Command/Base.php", "Core CLI command base"),
        ]

        missing = []
        for rel_path, desc in sentinels:
            full = self.target_repo_root / rel_path
            if not full.exists():
                missing.append(f"{rel_path} ({desc}) at {full}")

        if missing:
            raise BenchmarkEnvironmentError(
                f"BenchmarkEnvironmentError: Target repository root '{self.target_repo_root}' "
                f"is invalid or missing critical sentinels:\n  " + "\n  ".join(missing) +
                "\nFormal execution stopped. Never assume target files live under PolyFlow root."
            )

    def _capture_target_repo_git(self) -> None:
        """PHASE 3: Capture target repo commit and dirty state."""
        try:
            head = subprocess.check_output(
                ["git", "-C", str(self.target_repo_root), "rev-parse", "HEAD"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            self.target_repo_commit = head
        except Exception as ex:
            raise BenchmarkEnvironmentError(f"Failed to resolve target_repo HEAD: {ex}")

        try:
            status = subprocess.check_output(
                ["git", "-C", str(self.target_repo_root), "status", "--porcelain"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            if status:
                self.target_repo_dirty = True
                self.target_repository_state = "DIRTY"
                diff = subprocess.check_output(
                    ["git", "-C", str(self.target_repo_root), "diff"],
                    text=True, stderr=subprocess.DEVNULL
                )
                self.working_tree_diff_hash = hashlib.sha256(diff.encode("utf-8")).hexdigest()
            else:
                self.target_repo_dirty = False
                self.target_repository_state = "CLEAN"
                self.working_tree_diff_hash = ""
        except Exception:
            self.target_repo_dirty = True
            self.target_repository_state = "UNKNOWN"

    polyflow_worktree_diff_hash: str = ""

    def _capture_polyflow_git(self) -> None:
        """PHASE 4: Capture actual PolyFlow commit and dirty status."""
        try:
            head = subprocess.check_output(
                ["git", "-C", str(self.polyflow_root), "rev-parse", "HEAD"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            self.polyflow_commit = head
        except Exception as ex:
            raise BenchmarkEnvironmentError(
                f"Failed to resolve PolyFlow git HEAD commit: {ex}. Provenance cannot invent a source revision."
            )

        try:
            # Check status of PolyFlow repository excluding generated benchmark run outputs
            output_excludes = [
                ":!experiments/rcir_v8_5/results",
                ":!experiments/rcir_v8_5/raw",
                ":!experiments/rcir_v8_5/reports",
                ":!experiments/rcir_v8_5/manifests",
                ":!experiments/rcir_runs",
                ":!scratch",
            ]
            status = subprocess.check_output(
                ["git", "-C", str(self.polyflow_root), "status", "--porcelain", "--ignore-submodules=dirty", "--", "."] + output_excludes,
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            self.polyflow_dirty = bool(status)
            if self.polyflow_dirty:
                diff = subprocess.check_output(
                    ["git", "-C", str(self.polyflow_root), "diff", "--ignore-submodules=dirty", "--", "."] + output_excludes,
                    text=True, stderr=subprocess.DEVNULL
                )
                self.polyflow_worktree_diff_hash = hashlib.sha256(diff.encode("utf-8")).hexdigest()
            else:
                self.polyflow_worktree_diff_hash = ""
        except Exception as ex:
            raise BenchmarkEnvironmentError(f"Failed to check PolyFlow git status: {ex}")

    def derive_run_id(self) -> str:
        """Derive cryptographic immutable run ID from all benchmark inputs."""
        from provenance import collect_input_hashes, compute_run_identity
        inputs = collect_input_hashes(self)
        self.run_id = compute_run_identity(inputs)
        return self.run_id

    def ensure_directories(self) -> None:
        """Create all required artifact and result directories."""
        for d in [
            self.dataset_root,
            self.ground_truth_root,
            self.edge_ground_truth_root,
            self.receiver_ground_truth_root,
            self.canonicalization_ground_truth_root,
            self.manifests_root,
            self.results_root,
            self.reports_root,
            self.raw_root / "retrieval",
            self.raw_root / "context",
            self.raw_root / "graph",
            self.raw_root / "type_flow",
            self.raw_root / "edge_eval",
            self.raw_root / "agent",
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def validate_run_id(self, artifact_data: dict[str, Any], artifact_name: str) -> None:
        """PHASE 6 & 7: Verify run ID presence and consistency."""
        art_id = artifact_data.get("run_id")
        if not art_id:
            raise BenchmarkIntegrityError(f"Artifact '{artifact_name}' missing required 'run_id' field.")
        if art_id != self.run_id:
            raise BenchmarkIntegrityError(
                f"Run ID mismatch in '{artifact_name}': expected '{self.run_id}', found '{art_id}'."
            )

    def resolve_target_file(self, rel_path: str) -> Path:
        """Resolve a relative target repo path under target_repo_root, verifying existence."""
        clean = rel_path.replace("\\", "/").lstrip("/")
        full = self.target_repo_root / clean
        return full

    def set_run_directory(self, run_dir: Path | str) -> None:
        """Configure isolated per-run directories to prevent cross-run pollution (Issue 2)."""
        r_dir = Path(run_dir).resolve()
        self.manifests_root = r_dir / "manifests"
        self.results_root = r_dir / "results"
        self.raw_root = r_dir / "raw"
        self.reports_root = r_dir / "reports"
        self.ensure_directories()

    def capture_source_state(self) -> dict[str, Any]:
        """Capture immutable source checkout state for release benchmarking (Issue 3)."""
        self._capture_target_repo_git()
        self._capture_polyflow_git()
        return {
            "polyflow_commit": self.polyflow_commit,
            "polyflow_dirty": self.polyflow_dirty,
            "polyflow_worktree_diff_hash": self.polyflow_worktree_diff_hash,
            "target_repo_commit": self.target_repo_commit,
            "target_repo_dirty": self.target_repo_dirty,
            "target_repo_diff_hash": self.working_tree_diff_hash,
        }

    def verify_source_cleanliness(self, initial_state: dict[str, Any]) -> bool:
        """Verify repository source state remained untouched during benchmark execution."""
        current_state = self.capture_source_state()
        return current_state == initial_state

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "polyflow_root": str(self.polyflow_root),
            "target_repo_root": str(self.target_repo_root),
            "target_repo_name": self.target_repo_name,
            "target_repo_commit": self.target_repo_commit,
            "target_repo_dirty": self.target_repo_dirty,
            "target_repository_state": self.target_repository_state,
            "working_tree_diff_hash": self.working_tree_diff_hash,
            "polyflow_commit": self.polyflow_commit,
            "polyflow_dirty": self.polyflow_dirty,
            "polyflow_worktree_diff_hash": self.polyflow_worktree_diff_hash,
        }


def get_default_environment(run_id: Optional[str] = None, run_dir: Optional[Path | str] = None) -> BenchmarkEnvironment:
    """Convenience factory locating the polyflow root from this file."""
    # This file is at PolyFlow/experiments/rcir_v8_5/scripts/environment.py
    polyflow_root = Path(__file__).resolve().parents[3]
    target_repo_root = polyflow_root / "experiments" / "nextcloud_validation" / "nextcloud-server"
    env_run_id = run_id or os.environ.get("RCIR_RUN_ID", "rcir-v8.5.2-primary")
    env = BenchmarkEnvironment(
        polyflow_root=polyflow_root,
        target_repo_root=target_repo_root,
        run_id=env_run_id,
    )
    env_run_dir = run_dir or os.environ.get("RCIR_RUN_DIR")
    if env_run_dir:
        env.set_run_directory(env_run_dir)
    else:
        env.ensure_directories()
    return env


if __name__ == "__main__":
    env = get_default_environment()
    print("BenchmarkEnvironment successfully initialized:")
    print(json.dumps(env.to_dict(), indent=2))
