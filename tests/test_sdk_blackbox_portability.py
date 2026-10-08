"""
Black-Box Portability Verification Test (Section 14.4).

Verifies that the packaged PolyFlow SDK wheel installs and runs completely
standalone in an isolated virtual environment outside the PolyFlow workspace,
without access to monorepo PYTHONPATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SAMPLE_POLY = """@contract
feature_id: blackbox-test
owner: qa
timeout_ms: 2000
@end

@schema QueryRequest
query: string
limit: int
@end

@source
path: lib/query.py
language: python
role: service
symbol: ExecuteQuery
@end

@python[main]
def process(payload):
    q = payload.get("query", "status")
    return {"status": "ok", "result": f"Executed: {q}"}
@end
"""


def test_sdk_blackbox_portability():
    # 1. Locate wheel
    monorepo_root = Path(__file__).resolve().parents[1]
    wheel_dir = monorepo_root / "polyflow-sdk" / "dist"
    wheels = list(wheel_dir.glob("*.whl"))
    assert wheels, f"No wheel found in {wheel_dir}. Run 'python -m build --wheel' first."
    wheel_path = wheels[0]
    print(f"Target wheel: {wheel_path}")

    # 2. Create isolated directory outside workspace
    temp_dir = Path(tempfile.mkdtemp(prefix="polyflow_blackbox_"))
    try:
        venv_dir = temp_dir / "venv"
        print(f"Creating isolated venv at: {venv_dir}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        if os.name == "nt":
            venv_python = venv_dir / "Scripts" / "python.exe"
            venv_polyflow = venv_dir / "Scripts" / "polyflow.exe"
        else:
            venv_python = venv_dir / "bin" / "python"
            venv_polyflow = venv_dir / "bin" / "polyflow"

        # 3. Clean environment without PYTHONPATH
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONPATH", None)
        clean_env.pop("RCIR_RUN_DIR", None)
        clean_env.pop("RCIR_RUN_ID", None)

        # 4. Install wheel inside isolated venv
        print(f"Installing wheel into isolated venv...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--no-warn-script-location", str(wheel_path)],
            check=True,
            env=clean_env,
            capture_output=True,
            text=True
        )

        # 5. Create standalone workspace
        work_dir = temp_dir / "workspace"
        work_dir.mkdir()
        sample_file = work_dir / "sample.poly"
        sample_file.write_text(SAMPLE_POLY, encoding="utf-8")

        # 6. Execute polyflow --version
        print("Testing: polyflow --version")
        res = subprocess.run([str(venv_polyflow), "--version"], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        assert res.returncode == 0, f"--version failed: {res.stderr}"
        assert "PolyFlow SDK" in res.stdout
        print(f"  [OK] {res.stdout.strip()}")

        # 7. Execute polyflow doctor
        print("Testing: polyflow doctor")
        res = subprocess.run([str(venv_polyflow), "doctor"], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        assert res.returncode == 0, f"doctor failed: {res.stderr}"
        print("  [OK] Doctor passed")

        # 8. Execute polyflow inspect sample.poly
        print("Testing: polyflow inspect sample.poly")
        res = subprocess.run([str(venv_polyflow), "inspect", "sample.poly"], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        assert res.returncode == 0, f"inspect failed: {res.stderr}"
        assert "Grammar Version:    1.0.0" in res.stdout
        print("  [OK] Inspect passed")

        # 9. Execute polyflow ast sample.poly --json
        print("Testing: polyflow ast sample.poly")
        res = subprocess.run([str(venv_polyflow), "ast", "sample.poly"], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        assert res.returncode == 0, f"ast failed: {res.stderr}"
        assert '"grammar_version": "1.0.0"' in res.stdout
        print("  [OK] AST output passed")

        # 10. Execute polyflow run sample.poly
        print("Testing: polyflow run sample.poly")
        res = subprocess.run([str(venv_polyflow), "run", "sample.poly", "-p", '{"query": "healthcheck"}'], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        assert res.returncode == 0, f"run failed: {res.stderr}"
        print("  [OK] Run passed")

        # 11. Execute polyflow test .
        print("Testing: polyflow test .")
        res = subprocess.run([str(venv_polyflow), "test", "."], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        assert res.returncode == 0, f"test failed: {res.stderr}"
        print("  [OK] Test discovery passed")

        # 12. Execute polyflow analyze on external dummy repo
        dummy_repo = work_dir / "dummy_repo"
        dummy_repo.mkdir()
        (dummy_repo / "server.py").write_text("import json\nclass Server:\n    pass\n", encoding="utf-8")
        print("Testing: polyflow analyze dummy_repo")
        res = subprocess.run([str(venv_polyflow), "analyze", "dummy_repo"], cwd=str(work_dir), env=clean_env, capture_output=True, text=True)
        print(f"  [OK] Analyze finished with code {res.returncode}")

        print("\nALL BLACK-BOX PORTABILITY CHECKS PASSED!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_sdk_blackbox_portability()
