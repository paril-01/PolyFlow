"""Read-only source/artifact/tool inventory; printed output is captured by check.py."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, timeout=30)
    return dict(exit_code=result.returncode,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"))


for args in [("rev-parse", "HEAD"), ("branch", "--show-current"),
             ("status", "--short"), ("remote", "-v"),
             ("submodule", "status", "--recursive")]:
    print(json.dumps(dict(command=["git", *args], **git(*args))))
print("SESSION_IDENTITY", json.dumps({"agent": "Codex", "model_id": "UNVERIFIED: not exposed by native receipt", "python": sys.version, "python_executable": sys.executable, "platform": sys.platform}))
for name in ["pytest", "PyYAML", "hypothesis", "dash", "fastapi", "httpx", "psutil", "tiktoken", "pytest-cov"]:
    try:
        print("PACKAGE", name, importlib.metadata.version(name))
    except importlib.metadata.PackageNotFoundError:
        print("PACKAGE", name, "NOT_INSTALLED")
for name in ["git", "code", "node", "npm", "php", "composer", "ollama", "docker", "wsl", "gh"]:
    print("TOOL", name, shutil.which(name) or "NOT_ON_PATH")
for command in [["git", "--version"], ["cmd", "/c", "code", "--version"], ["node", "--version"], ["php", "--version"], ["docker", "version"], ["wsl", "--list", "--quiet"]]:
    try:
        result = subprocess.run(command, capture_output=True, timeout=15)
        print("VERSION", json.dumps(dict(command=command, exit_code=result.returncode, stdout=result.stdout.decode(errors="replace"), stderr=result.stderr.decode(errors="replace"))))
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("VERSION_UNAVAILABLE", command, str(exc))
try:
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=4) as response:
        print("LOCAL_MODEL_INVENTORY", response.read().decode())
except Exception as exc:
    print("LOCAL_MODEL_UNAVAILABLE", str(exc))

index = json.loads((ROOT / "experiments/runs/run_20261009_blind_verified/proof_index.json").read_text())
for proof in index["proofs"]:
    path = proof["source_file"]
    disk = (ROOT / path).read_bytes() if (ROOT / path).is_file() else None
    blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True)
    raw = blob.stdout if blob.returncode == 0 else None
    sha = lambda data: hashlib.sha256(data).hexdigest() if data is not None else None
    crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n") if raw is not None else None
    print("PROOF_HASH", json.dumps(dict(id=proof["proof_id"], path=path, expected=proof.get("sha256"), disk=sha(disk), git_blob=sha(raw), git_blob_crlf=sha(crlf), disk_bytes=len(disk) if disk is not None else None, git_bytes=len(raw) if raw is not None else None)))
for path in ["experiments/rcir_v8_5/results/performance_benchmark.json", "experiments/rcir_v8_5/manifests/benchmark_run_manifest.json", "experiments/rcir_v8_5/results/gate_evaluation.json"]:
    data = json.loads((ROOT / path).read_text())
    print("HISTORICAL_RECEIPT", json.dumps(dict(path=path, sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), run_id=data.get("run_id"), polyflow_commit=data.get("polyflow_commit"), target_repo_commit=data.get("target_repo_commit"), run_validity=data.get("run_validity"))))
