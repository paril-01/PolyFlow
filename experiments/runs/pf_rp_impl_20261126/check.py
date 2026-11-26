"""Local audit command logger. No provider calls or benchmark generation."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]


def main():
    name, *command = sys.argv[1:]
    if not command or not name.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("Usage: check.py unique-name command [args...]")
    log = RUN / f"{name}.log"
    if log.exists():
        raise SystemExit(f"Refusing to overwrite {log}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # Tests that launch bare `python` must use this same selected interpreter.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = os.pathsep.join([
        str(ROOT), str(ROOT / "rcir/src"),
        str(ROOT / "experiments/rcir_v8_5/scripts"),
        str(ROOT / "experiments/rcir_v8_5"),
    ])
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    before = time.perf_counter()
    print(f"RUNNING {name}: {subprocess.list2cmdline(command)}", flush=True)
    try:
        with log.open("xb") as output:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=600)
        code = result.returncode
        status = "PASSED" if code == 0 else "FAILED"
    except subprocess.TimeoutExpired:
        code, status = None, "TIMEOUT"
    except OSError as exc:
        with log.open("ab") as output:
            output.write(str(exc).encode("utf-8"))
        code, status = None, "INVALID_SETUP"
    receipt = dict(name=name, command=command, cwd=str(ROOT), started_at=start,
                   duration_seconds=time.perf_counter() - before,
                   exit_code=code, status=status, log=str(log.relative_to(ROOT)),
                   evidence_type="OBSERVED_EXECUTION")
    with (RUN / "commands.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(receipt) + "\n")
    print(json.dumps(receipt), flush=True)
    print(log.read_text(encoding="utf-8", errors="replace")[-7000:], flush=True)
    raise SystemExit(code if code is not None else 124)


if __name__ == "__main__":
    main()
