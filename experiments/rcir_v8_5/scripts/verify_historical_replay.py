"""Verify frozen historical replay independently from current release eligibility."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile

from environment import get_default_environment
from evaluate_gates import evaluate_gates


def verify_replay(env=None):
    env = copy.copy(env or get_default_environment())
    manifest = json.loads((env.manifests_root / "benchmark_run_manifest.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="rcir-historical-replay-") as temporary:
        output = Path(temporary) / "results"
        shutil.copytree(env.results_root, output)
        env.results_root = output
        with contextlib.redirect_stdout(io.StringIO()):
            result = evaluate_gates(allow_development_dirty=True, allow_historical=True, env=env)
    failures = result["integrity_gate"]["failures"]
    return {"status": "HISTORICAL_REPLAY_CONSISTENT" if not failures else "HISTORICAL_REPLAY_FAILED",
            "recorded_run_id": manifest.get("run_id"), "historical_source_dirty": manifest.get("polyflow_dirty"),
            "release_eligible": False, "fresh_benchmark": False, "architecture_approval": False,
            "release_status": "NOT_EVALUATED_HERE_USE_STRICT_RELEASE_GATE", "failures": failures}


if __name__ == "__main__":
    receipt = verify_replay()
    print(json.dumps(receipt, indent=2))
    raise SystemExit(0 if receipt["status"] == "HISTORICAL_REPLAY_CONSISTENT" else 1)
