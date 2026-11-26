"""Create a scoped local diff and derive progress from raw command receipts."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
PLAN = ROOT / "plans/rcir_proof"
SOURCE_PATHS = [
    ".github/workflows/ci.yml", ".github/workflows/rcir-artifact-integrity.yml",
    "showcase_app/backend/services/evidence_registry.py",
    "showcase_app/backend/api/proofs.py", "showcase_app/backend/api/health.py",
    "showcase_app/backend/schemas.py", "orchestrator/tools.py",
    "tests/test_backend_proof_server.py", "tests/test_evidence_registry.py",
    "tests/test_repo_tools.py", "tests/benchmark_integrity/test_historical_provenance_gate.py",
    "experiments/rcir_v8_5/reports/final_assessment.md",
]

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)

def main():
    import ast
    import yaml
    for name in SOURCE_PATHS:
        if name.endswith(".py"):
            ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)
        elif name.endswith(".yml"):
            workflow = yaml.safe_load((ROOT / name).read_text())
            assert workflow["jobs"]
    print("AST_AND_YAML_PARSE_OK")
    check = git("diff", "--check", "--", *SOURCE_PATHS)
    assert check.returncode == 0, check.stdout.decode(errors="replace")
    print("SCOPED_DIFF_CHECK_OK")
    protected = ["polyflow", "polyflow-sdk", "templates/PHASE_STATE.json",
                 "experiments/rcir_v8_5/results", "experiments/rcir_v8_5/manifests",
                 "experiments/rcir_v8_5/ground_truth", "experiments/rcir_v8_5/edge_ground_truth",
                 "experiments/rcir_v8_5/receiver_ground_truth", "experiments/rcir_v8_5/canonicalization_ground_truth",
                 "experiments/runs/run_20261009_blind_verified"]
    pristine = git("diff", "HEAD", "--exit-code", "--", *protected)
    assert pristine.returncode == 0, pristine.stdout.decode(errors="replace")
    print("PROTECTED_SOURCE_RAW_RESULTS_MANIFESTS_AND_FROZEN_RUN_UNCHANGED")
    patch = git("diff", "--binary", "--", *SOURCE_PATHS).stdout
    added = git("diff", "--no-index", "--", "/dev/null", "tests/test_evidence_registry.py")
    assert added.returncode == 1
    patch += added.stdout
    (RUN / "scoped.patch").write_bytes(patch)
    (RUN / "final-git-status.log").write_bytes(git("status", "--short").stdout)
    receipts = [json.loads(line) for line in (RUN / "commands.jsonl").read_text().splitlines()]
    indexed = {item["name"]: item for item in receipts}
    chosen = ["provenance-baseline", "linux-object-provenance", "proof-final", "linux-proof-smoke-fixed",
              "integrity-after", "historical-gates-isolated", "stages-final", "core-ci-final", "reports-after", "core-after"]
    lines = ["# RCIR implementation progress", "", "PHASE: PF-RP-00 baseline captured; PF-RP-01 local repair implemented; hosted CI/independent acceptance pending.", "",
             "REPO/SHA/BRANCH/DIRTY: paril-01/PolyFlow @ 6a586e16007cb1bed123619b4494067f99eccf2f; work/pf-rp-01-proof-integrity; uncommitted scoped patch plus preserved user changes.", "",
             "AUTHORIZATION: Owner's current request to evaluate then implement locally. [Exact ticket and ownership](./PF-RP-01.json).", "",
             "FILES READ / EVIDENCE TABLE / PLAN / CHANGES / RISKS / PROHIBITED ACTIONS: [complete baseline and closeout](./BASELINE.md).", "",
             "Implemented proof delivery with exact recorded digest, raw/delivery hash policies, all-branch path checks and explicit availability; removed static validated health; isolated mutating historical tests; repaired Windows command argv quoting; corrected the stale derived assessment while archiving its previous bytes; added Windows/Linux CI coverage and target checkout.", "",
             "## Observed execution", "", "These are separate checks, not summed into a benchmark score. Exact executable argv and all failed attempts are in [commands.jsonl](../../experiments/runs/pf_rp_01_20261126T014922/commands.jsonl).", "",
             "| Check | Exit | Actual outcome | Log |", "|---|---:|---|---|"]
    for name in chosen:
        receipt = indexed.get(name)
        if not receipt:
            continue
        log = ROOT / receipt["log"]
        content = log.read_text(encoding="utf-8", errors="replace")
        matches = re.findall(r"[^\n]*\b\d+ passed[^\n]*", content)
        outcome = matches[-1].strip() if matches else receipt["status"]
        lines.append(f"| {name} | {receipt['exit_code']} | {outcome} | [{log.name}](../../{log.relative_to(ROOT).as_posix()}) |")
    lines += ["", "COMMANDS / TESTS:", ""]
    for name in chosen:
        if name in indexed:
            receipt = indexed[name]
            lines += [f"- `{name}`: `{subprocess.list2cmdline(receipt['command'])}`; exit `{receipt['exit_code']}`; log linked above."]
    lines += ["", "The Linux proof check validates all 18 frozen Git-blob proofs plus six negative controls, including real Linux symlinks. Windows proof tests skip two symlink cases because this host denies creation; Linux checks cover both. Linux source-object validation does not certify worktree cleanliness. The initial full Linux validator was deliberately stopped with exit 15 after 305 seconds in an NTFS git-status census; its failed receipt is retained.", "",
              "The report-consistency pass proves agreement with stored inputs. The corrected report says INVALID because that is the saved historical gate input, not because a fresh live benchmark was run. [Previous report bytes](../../experiments/runs/pf_rp_01_20261126T014922/superseded-final_assessment.md) are preserved. Two files overwritten by pre-existing tests were archived as test-generated outputs and restored; final raw-result/manifest Git checks pass.", "",
              "GATE STATUS: PF-RP-01 remains INCOMPLETE pending four hosted workflows and independent review. Existing R2 invalidation test still fails (core-after log). No architecture winner, live task success, token saving, cost reduction or native IDE credit saving is claimed.", "",
              "NOT_RUN: fresh live paired/locked benchmarks; native MCP IDE A/B study; paid provider calls; clean independent package install; React build in this session; full supported Python-version matrix. Provider/generalization smoke scripts that overwrite historical results were not run directly. No GitHub workflow was launched on this uncommitted patch.", "",
              "NEXT ACTION: review [scoped source patch](../../experiments/runs/pf_rp_01_20261126T014922/scoped.patch), then approve publishing the branch and a draft PR for hosted CI without merge. The branch also contains the prior committed provenance fix. [Dependency-ordered backlog](./BACKLOG.json) prepares PF-RP-02; it has not started.", ""]
    (PLAN / "PROGRESS.md").write_text("\n".join(lines), encoding="utf-8")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ledger = PLAN / "PHASE_LEDGER.jsonl"
    if not ledger.exists():
        with ledger.open("a", encoding="utf-8") as output:
            output.write(json.dumps(dict(timestamp=now, phase="PF-RP-00", status="BASELINE_CAPTURED", source_sha="6a586e16007cb1bed123619b4494067f99eccf2f", evidence="BASELINE.md")) + "\n")
    with ledger.open("a", encoding="utf-8") as output:
        output.write(json.dumps(dict(timestamp=now, phase="PF-RP-01", status="LOCAL_REPAIR_IMPLEMENTED_CI_AND_INDEPENDENT_REVIEW_PENDING", source_sha="6a586e16007cb1bed123619b4494067f99eccf2f", patch_sha256=hashlib.sha256(patch).hexdigest(), evidence="PROGRESS.md", later_lifecycle_failure="core-after.log", live_benchmarks="NOT_RUN")) + "\n")
    print("REVIEW_PACKET_WRITTEN", str(PLAN / "PROGRESS.md"))

if __name__ == "__main__":
    main()
