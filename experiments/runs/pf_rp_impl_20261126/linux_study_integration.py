"""Actual sandbox/control/evaluator integration using a SYNTHETIC fixture.

Not a curated task, not a model run, not benchmark or release evidence.
"""
import json
from pathlib import Path
import subprocess
import tempfile

from experiments.benchmark_core.product_study import qualify_change, export_base
from experiments.benchmark_core.agent_trial import source_census, complete_patch, evaluate_trial
from rcir.service.snapshot import canonical


root = Path(tempfile.mkdtemp(prefix="rcir-controller-test-"))
repo, oracle = root / "repo", root / "private"
repo.mkdir()
oracle.mkdir()
def git(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.STDOUT).decode().strip()
git("init")
git("config", "user.name", "Synthetic integration")
git("config", "user.email", "test@example.invalid")
(repo / "worker.py").write_text("def compute():\n    return 1\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "synthetic base")
base = git("rev-parse", "HEAD")
(repo / "worker.py").write_text("def compute():\n    return 2\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "synthetic reference")
fix = git("rev-parse", "HEAD")
(oracle / "check.py").write_text("import runpy\nassert runpy.run_path('/work/worker.py')['compute']() == 2\n", encoding="utf-8")
command = ["/usr/bin/python3", "/oracle/check.py"]
controls = qualify_change(repo, base, fix, oracle, command, root / "controls")
assert controls["status"] == "CONTROL_EXECUTION_QUALIFIED"
source = root / "agent"
export_base(repo, base, source)
before = source_census(source)
(source / "worker.py").write_text("def compute():\n    return 2\n", encoding="utf-8")
(source / "untracked.txt").write_text("untracked output\n", encoding="utf-8")
patch, changes = complete_patch(source, before)
(root / "changes.json").write_bytes(canonical(changes))
result = evaluate_trial(repo, base, root / "changes.json", oracle, command, root / "evaluation",
                        qualified_control_receipt=root / "controls/qualification.json")
assert result["status"] == "TESTS_PASSED"
assert len(changes) == 2
print(json.dumps({"scope": "SYNTHETIC_SOFTWARE_INTEGRATION_ONLY", "model_calls": 0,
                  "controls": controls, "evaluation": result, "changed_files": len(changes), "raw_artifact_directory": str(root)}, indent=2))
