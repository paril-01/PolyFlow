"""Build/install a wheel outside the checkout, then exercise the installed CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def run(argv, cwd, env):
    print(json.dumps({"argv": [str(a) for a in argv], "cwd": str(cwd)}), flush=True)
    process = subprocess.Popen([str(a) for a in argv], cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = []
    for line in process.stdout:
        print(line, end="", flush=True)
        output.append(line)
    if process.wait():
        raise subprocess.CalledProcessError(process.returncode, argv)
    return "".join(output)


with tempfile.TemporaryDirectory(prefix="rcir-wheel-") as temporary:
    work = Path(temporary)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    run([sys.executable, "-m", "build", "--wheel", "--outdir", work / "wheels", ROOT / "rcir"], work, env)
    wheel = next((work / "wheels").glob("*.whl"))
    run([sys.executable, "-m", "venv", work / "venv"], work, env)
    python = work / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run([python, "-m", "pip", "install", wheel, "tiktoken==0.14.0", "mcp==2.3.0"], work, env)
    run([python, "-m", "pip", "check"], work, env)
    run([python, "-m", "rcir.service.cli", "--help"], work, env)
    repo = work / "source"
    repo.mkdir()
    run(["git", "init"], repo, env)
    run(["git", "config", "user.name", "RCIR smoke"], repo, env)
    run(["git", "config", "user.email", "test@example.invalid"], repo, env)
    (repo / "source.py").write_text("def sample_symbol():\n    return 1\n", encoding="utf-8")
    run(["git", "add", "."], repo, env)
    run(["git", "commit", "-m", "install smoke"], repo, env)
    receipt = json.loads(run([python, "-m", "rcir.service.cli", "query", "--repo", repo, "--query", "sample_symbol", "--budget", "1000"], work, env))
    assert receipt["evidence_items"][0]["symbol_name"] == "sample_symbol"
    assert receipt["tokens_consumed"] <= 1000
    run([python, "-m", "pip", "freeze"], work, env)
    print("CLEAN_WHEEL_INSTALL_AND_QUERY_VERIFIED", flush=True)
