"""Preserve test-generated outputs and restore only two initially clean artifacts."""
import hashlib
from pathlib import Path
import subprocess

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
for name in ["gate_evaluation.json", "integrity_evaluation.json"]:
    relative = f"experiments/rcir_v8_5/results/{name}"
    target = ROOT / relative
    generated = target.read_bytes()
    saved = RUN / ("test-generated-" + name)
    if saved.exists():
        raise RuntimeError("Refusing to overwrite captured test output")
    saved.write_bytes(generated)
    blob = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT,
                          capture_output=True, check=True).stdout
    # Initial inventory: both paths were clean, i/lf w/crlf, autocrlf=true.
    restored = blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if name == "gate_evaluation.json":
        assert hashlib.sha256(restored).hexdigest() == "faef3c586e11a3b6d33502a967994fdea91c733535dbe9969de5930895a11b6e"
    target.write_bytes(restored)
    print("RESTORED_INITIAL_CLEAN_ARTIFACT", relative,
          "sha256=" + hashlib.sha256(restored).hexdigest(),
          "test_generated_copy=" + saved.name)
    subprocess.run(["git", "diff", "--exit-code", "--", relative], cwd=ROOT, check=True)
