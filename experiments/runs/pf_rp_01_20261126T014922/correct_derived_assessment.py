"""Supersede a stale derived report while preserving original bytes and inputs."""
import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
SCRIPTS = ROOT / "experiments/rcir_v8_5/scripts"
sys.path.insert(0, str(SCRIPTS))
from generate_reports import generate_all_reports

report = ROOT / "experiments/rcir_v8_5/reports/final_assessment.md"
archive = RUN / "superseded-final_assessment.md"
if archive.exists():
    raise RuntimeError("Refusing to overwrite superseded report")
original = report.read_bytes()
archive.write_bytes(original)
results = ROOT / "experiments/rcir_v8_5/results"
protected = {path: path.read_bytes() for path in results.glob("*.json")}
generated = RUN / "derived-reports"
generate_all_reports(out_dir=generated)
replacement = (generated / report.name).read_bytes()
assert b"`INVALID`" in replacement
assert b"`OPTION_B_ACCEPTED`" not in replacement
for path, data in protected.items():
    assert path.read_bytes() == data, path
report.write_bytes(replacement)
print(json.dumps({"action": "SUPERSEDE_STALE_DERIVED_REPORT", "old_sha256": hashlib.sha256(original).hexdigest(), "new_sha256": hashlib.sha256(replacement).hexdigest(), "old_bytes_preserved_at": str(archive.relative_to(ROOT)), "source_gate_status": "HISTORICAL_REPORTED_INVALID", "fresh_benchmark_run": False, "raw_results_unchanged": True}))
