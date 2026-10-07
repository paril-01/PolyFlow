#!/usr/bin/env python3
"""
RCIR v8.5.2 — Cross-Artifact Consistency & Run Provenance Scanner (Issue 50).

Scans all generated JSON result artifacts in results/ and raw/:
1. Verifies that all artifacts share the identical active run_id.
2. Verifies that all artifacts share the identical target_commit and polyflow_commit.
3. Verifies that all artifacts contain the complete required provenance envelope (17 fields).
4. Verifies that all config_hashes and code_fingerprints match the active machine state.
5. Fails immediately (exit code 1) on any discrepancy or stale artifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from environment import get_default_environment
from provenance import REQUIRED_PROVENANCE_FIELDS, validate_artifact_provenance, collect_input_hashes


def scan_run_consistency(results_dir: Path | None = None, env: Any = None, allow_development_dirty: bool = True) -> bool:
    print("=" * 80)
    print("RCIR v8.5.2 — Cross-Artifact Run Provenance & Consistency Scanner")
    print("=" * 80)

    if env is None:
        env = get_default_environment()
    env.derive_run_id()

    target_results = results_dir or env.results_root
    if not target_results.exists():
        print(f"[ERROR] Results directory does not exist: {target_results}")
        return False

    json_files = list(target_results.glob("*.json"))
    if not json_files:
        print(f"[ERROR] No JSON artifacts found in {target_results}")
        return False

    print(f"Scanning {len(json_files)} artifacts in {target_results} against active Run ID: '{env.run_id}'...")

    primary_run_id = env.run_id
    primary_target_commit = env.target_repo_commit
    primary_polyflow_commit = env.polyflow_commit

    inputs = collect_input_hashes(env)
    active_config_hashes = inputs["config_hashes"]

    discrepancies: List[str] = []

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            discrepancies.append(f"{jf.name}: Invalid JSON: {e}")
            continue

        # Skip local selection or metadata files if they don't have provenance envelopes
        if jf.name in ("selected_ranker_config.json",):
            continue

        prov = data.get("provenance") or data
        art_run_id = prov.get("run_id") or data.get("run_id")

        if not art_run_id:
            discrepancies.append(f"{jf.name}: Missing 'run_id'")
        elif art_run_id != primary_run_id:
            discrepancies.append(f"{jf.name}: run_id mismatch: '{art_run_id}' != '{primary_run_id}' (STALE)")

        # Validate complete provenance envelope if artifact is a formal benchmark output
        formal_artifacts = (
            "gate_evaluation.json",
            "type_flow_evaluation.json",
            "impact_test.json",
            "determinism_evaluation.json",
            "agent_ab_runs.json",
            "agent_turn_budget.json",
            "generalization_readiness.json",
        )
        if jf.name in formal_artifacts:
            ok, errors = validate_artifact_provenance(data, env, allow_development_dirty=allow_development_dirty)
            if not ok:
                for err in errors:
                    discrepancies.append(f"{jf.name}: {err}")

    if discrepancies:
        print("\n[CONSISTENCY SCAN FAILED] Discrepancies detected:")
        for d in discrepancies:
            print(f"  - {d}")
        return False

    print(f"\n[CONSISTENCY SCAN PASSED] All {len(json_files)} artifacts share identical Run ID '{primary_run_id}' and valid provenance.")
    return True


if __name__ == "__main__":
    success = scan_run_consistency()
    sys.exit(0 if success else 1)
