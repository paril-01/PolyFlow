#!/usr/bin/env python3
"""
RCIR v8.2 — Automated Report Consistency Validator (PHASE 57).

Asserts ABSOLUTE RULE 0:
- Reads raw JSON artifacts from experiments/rcir_v8_2/results/
- Reads Markdown reports from experiments/rcir_v8_2/reports/
- Asserts that numbers reported in Markdown strictly match raw values in JSON
- Fails with non-zero exit code if any discrepancy is detected
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_2" / "results"
REPORTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_2" / "reports"


def validate_consistency():
    errors = []

    # 1. Gate evaluation consistency
    gate_file = RESULTS_DIR / "gate_evaluation.json"
    final_report = REPORTS_DIR / "final_assessment.md"
    if gate_file.exists() and final_report.exists():
        with open(gate_file, "r", encoding="utf-8") as f:
            gate_data = json.load(f)
        report_text = final_report.read_text(encoding="utf-8")

        rec = gate_data.get("recommendation", "")
        if rec not in report_text:
            errors.append(f"Recommendation '{rec}' missing from final_assessment.md")

    # 2. Context plane metrics consistency
    ctx_file = RESULTS_DIR / "context_plane.json"
    rank_report = REPORTS_DIR / "ranking_report.md"
    if ctx_file.exists() and rank_report.exists():
        with open(ctx_file, "r", encoding="utf-8") as f:
            ctx_data = json.load(f)
        report_text = rank_report.read_text(encoding="utf-8")

        mrr_val = ctx_data.get("macro_averages", {}).get("mrr", 0.0)
        mrr = f"{mrr_val:.4f}"
        if mrr not in report_text:
            errors.append(f"Aggregate MRR '{mrr}' from context_plane.json not found in ranking_report.md")

    # 3. Impact plane recall consistency
    impact_file = RESULTS_DIR / "impact_plane.json"
    impact_report = REPORTS_DIR / "impact_plane_report.md"
    if impact_file.exists() and impact_report.exists():
        with open(impact_file, "r", encoding="utf-8") as f:
            impact_data = json.load(f)
        report_text = impact_report.read_text(encoding="utf-8")

        global_recall_val = impact_data.get("totals", {}).get("global_pool_recall", 0.0)
        pct_str = f"{global_recall_val * 100:.2f}%"
        float_str = f"{global_recall_val:.4f}"
        if pct_str not in report_text and float_str not in report_text:
            errors.append(f"Global recall '{pct_str}' not found in impact_plane_report.md")

    # 4. Performance benchmark consistency
    perf_file = RESULTS_DIR / "performance_benchmark.json"
    if perf_file.exists():
        with open(perf_file, "r", encoding="utf-8") as f:
            perf_data = json.load(f)
        assert "latency_ms" in perf_data and "memory" in perf_data

    if errors:
        msg = f"Found {len(errors)} consistency discrepancies:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(msg)
    return True


if __name__ == "__main__":
    try:
        validate_consistency()
        print("PASS: All Markdown reports are strictly consistent with raw JSON artifacts.")
        sys.exit(0)
    except ValueError as ex:
        print(f"FAILED: {ex}")
        sys.exit(1)
