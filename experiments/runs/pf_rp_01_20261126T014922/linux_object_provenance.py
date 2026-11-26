"""Validate source objects on Linux without rescanning the NTFS working tree."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "experiments/nextcloud_validation/nextcloud-server"
sys.path.insert(0, str(ROOT / "experiments/rcir_v8_5/scripts"))
from environment import BenchmarkEnvironment
from validate_ground_truth_provenance import audit_provenance

assert sys.platform == "linux"
def head(path):
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()

target_sha, source_sha = head(TARGET), head(ROOT)
assert target_sha == "da57df078d0808a7235a0177bd99d23c010b472e"
print("LINUX_SOURCE_OBJECT_CHECK", sys.version, source_sha, target_sha, flush=True)
print("WORKTREE_CLEANLINESS_NOT_EVALUATED: explicit resolved revisions avoid the slow NTFS status census.", flush=True)
env = BenchmarkEnvironment(polyflow_root=ROOT, target_repo_root=TARGET,
                           polyflow_commit=source_sha, target_repo_commit=target_sha)
result = audit_provenance(env=env)
print("LINUX_SOURCE_OBJECT_PROVENANCE_COMPLETE", result.get("validation_status"), flush=True)
