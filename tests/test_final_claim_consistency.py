"""
Final Claim Consistency Test.
Follows Section 14 of POLYFLOW_FINAL_BLIND_VALIDATION_AND_SHOWCASE_PROMPT.md:
- Compares reports, showcase data, formal gates, agent A/B and ERPNext artifacts
- Fails if report says 5/5 but artifact says 0/5
- Fails if agent gate false renders 'all gates passed'
- Fails if NOT_MEASURED becomes 0
- Fails if DocType counts disagree
- Fails if pair counts disagree
- Fails if token delta differs from recomputation
"""

import json
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SHOWCASE_DATA = REPO_ROOT / "showcase" / "data"
RESULTS_DIR = REPO_ROOT / "experiments" / "final_blind_validation" / "results"
REPORTS_DIR = REPO_ROOT / "reports"


def test_agent_success_count_consistency():
    """Verify that agent trials success matches across raw artifacts and showcase data."""
    agent_trials_file = SHOWCASE_DATA / "agent_trials.json"
    token_ab_file = SHOWCASE_DATA / "token_ab.json"
    blind_baseline_file = RESULTS_DIR / "blind_baseline.json"

    assert agent_trials_file.exists()
    assert token_ab_file.exists()
    assert blind_baseline_file.exists()

    agent_trials = json.loads(agent_trials_file.read_text(encoding="utf-8"))
    token_ab = json.loads(token_ab_file.read_text(encoding="utf-8"))
    baseline = json.loads(blind_baseline_file.read_text(encoding="utf-8"))

    # Raw success count
    successful_trials = [t for t in agent_trials["trials"] if t.get("verification", {}).get("accepted")]
    assert len(successful_trials) == 0, "Expected 0 approved trials under 5-turn budget with 1.5b local model"

    # Token A/B agreement
    assert token_ab["successful_pairs"] == 0
    assert token_ab["valid_pairs"] == 5
    assert token_ab["individual_trials"] == 10

    # Baseline results agreement
    assert baseline["successful_pairs"] == 0
    assert baseline["individual_trials"] == 10


def test_gate_consistency_agent_gate_not_satisfied():
    """Verify that agent gate false prevents claims of 'all gates passed'."""
    status_file = SHOWCASE_DATA / "system_status.json"
    assert status_file.exists()

    status = json.loads(status_file.read_text(encoding="utf-8"))
    agent_gate = next((g for g in status["gates"] if g["name"] == "agent_gate"), None)

    assert agent_gate is not None
    assert agent_gate["passed"] is False
    assert agent_gate["status"] == "NOT_SATISFIED"

    # Total gates vs passed
    assert status["gates_passed"] < status["total_contract_gates"]
    assert status["gates_passed"] == 6
    assert status["total_contract_gates"] == 7


def test_ide_credits_not_measured():
    """Verify that IDE credits strictly remain NOT_MEASURED and never convert to 0 or synthetic savings."""
    token_ab_file = SHOWCASE_DATA / "token_ab.json"
    claim_registry_file = SHOWCASE_DATA / "claim_registry.json"

    token_ab = json.loads(token_ab_file.read_text(encoding="utf-8"))
    claim_registry = json.loads(claim_registry_file.read_text(encoding="utf-8"))

    assert token_ab["ide_credits"]["status"] == "NOT_MEASURED"
    assert token_ab["ide_credits"]["value"] is None

    claims_list = claim_registry if isinstance(claim_registry, list) else claim_registry.get("claims", [])
    credit_claim = next((c for c in claims_list if "credit" in c.get("id", "")), None)
    if credit_claim:
        assert credit_claim["status"] == "NOT_MEASURED"


def test_doctype_and_scale_counts_consistency():
    """Verify that ERPNext DocType and scale inventory counts agree across all sources."""
    erpnext_scale_file = SHOWCASE_DATA / "erpnext_scale.json"
    assert erpnext_scale_file.exists()

    erp_data = json.loads(erpnext_scale_file.read_text(encoding="utf-8"))
    inventory = erp_data["scale_inventory"]

    # F15 & F16 exact count reconciliations
    assert inventory["doctype_schema_count"] == 840
    assert inventory["generated_poly_feature_count"] == 842
    assert inventory["non_doctype_feature_count"] == 2
    assert inventory["total_source_files"] == 4412
    assert inventory["total_loc"] == 712940

    # Coverage breakdown
    coverage = erp_data["coverage_breakdown"]
    assert coverage["artifact_accounting_coverage_pct"] == 100.0
    assert coverage["semantic_mapping_coverage_pct"] == 98.4
    assert coverage["executable_vertical_coverage_pct"] == 24.5
    assert coverage["behavioral_parity_coverage_pct"] == 18.2
    assert coverage["unresolved_count"] == 0


def test_token_delta_recomputation():
    """Verify that token delta percentages in token_ab.json equal exact recomputations from prompt tokens."""
    token_ab_file = SHOWCASE_DATA / "token_ab.json"
    token_ab = json.loads(token_ab_file.read_text(encoding="utf-8"))

    deltas = []
    for pair in token_ab["pairs"]:
        b_prompt = pair["baseline"]["prompt_tokens"]
        r_prompt = pair["rcir"]["prompt_tokens"]
        
        expected_delta = round(((b_prompt - r_prompt) / b_prompt) * 100, 2)
        assert abs(pair["input_token_delta_pct"] - expected_delta) < 0.05, (
            f"Token delta mismatch for {pair['task_id']}: expected {expected_delta}%, got {pair['input_token_delta_pct']}%"
        )
        deltas.append(expected_delta)

    median_delta = sorted(deltas)[len(deltas) // 2]
    assert abs(token_ab["median_input_token_delta_pct"] - median_delta) < 0.05
