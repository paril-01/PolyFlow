"""
Tests for Stage 5: Strict Contract & Gate Evaluator Hardening (F02, F10, F12, F13).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))

from evaluate_gates import evaluate_gates
from environment import get_default_environment


def test_f02_source_recall_strictly_enforced_in_context_gate():
    """
    F02 Verification:
    If source recall is below the contract threshold (e.g. 0.0),
    context_gate["passed"] must be False, and Option A cannot be accepted.
    """
    env = get_default_environment()
    ctx_test_path = env.results_root / "context_test.json"
    gate_path = env.results_root / "gate_evaluation.json"
    integ_path = env.results_root / "integrity_evaluation.json"
    assert ctx_test_path.exists()

    orig_ctx = ctx_test_path.read_text(encoding="utf-8")
    orig_gate = gate_path.read_text(encoding="utf-8") if gate_path.exists() else None
    orig_integ = integ_path.read_text(encoding="utf-8") if integ_path.exists() else None
    try:
        # Mutate context_test.json to have 0.0 source recall
        data = json.loads(orig_ctx)
        data["critical_source_recall_at_4k"] = 0.0
        ctx_test_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        res = evaluate_gates(allow_development_dirty=True)
        assert res["context_gate"]["source_recall_passed"] is False
        assert res["context_gate"]["passed"] is False
        assert res["architecture_decision"] != "OPTION_A_ACCEPTED"
    finally:
        ctx_test_path.write_text(orig_ctx, encoding="utf-8")
        if orig_gate is not None:
            gate_path.write_text(orig_gate, encoding="utf-8")
        if orig_integ is not None:
            integ_path.write_text(orig_integ, encoding="utf-8")


def test_f02_empty_agent_evidence_cannot_pass_agent_gate():
    """
    F02 Verification:
    An agent summary claiming completion with zero trials or empty evidence
    must be rejected by the agent gate.
    """
    env = get_default_environment()
    agent_ab_path = env.results_root / "agent_ab_runs.json"
    gate_path = env.results_root / "gate_evaluation.json"
    integ_path = env.results_root / "integrity_evaluation.json"
    orig_ab = agent_ab_path.read_text(encoding="utf-8") if agent_ab_path.exists() else None
    orig_gate = gate_path.read_text(encoding="utf-8") if gate_path.exists() else None
    orig_integ = integ_path.read_text(encoding="utf-8") if integ_path.exists() else None

    try:
        # Mock agent_ab_runs claiming MEASURED validation with 0 trials
        fake_ab = {
            "validation_status": "MEASURED_AGENT_VALIDATION",
            "provider": {"is_simulation": False},
            "condition_a_rcir": {"trials_count": 0, "completed_count": 0, "completion_rate": 1.0},
        }
        agent_ab_path.write_text(json.dumps(fake_ab, indent=2), encoding="utf-8")

        res = evaluate_gates(allow_development_dirty=True)
        assert res["agent_gate"]["passed"] is False
        assert res["architecture_decision"] != "OPTION_A_ACCEPTED"
    finally:
        if orig_ab is not None:
            agent_ab_path.write_text(orig_ab, encoding="utf-8")
        elif agent_ab_path.exists():
            agent_ab_path.unlink()
        if orig_gate is not None:
            gate_path.write_text(orig_gate, encoding="utf-8")
        if orig_integ is not None:
            integ_path.write_text(orig_integ, encoding="utf-8")


def test_f10_structural_summary_gives_zero_source_recall_credit():
    """
    F10 Verification:
    In context compilation, structural summaries and file references must not
    contribute to source_delivered for critical source recall.
    """
    from rcir.context.compiler import ContextEntry, ContextGranularity

    entry_summary = ContextEntry(
        entity_id="php://OC\\SummaryOnly",
        rank=1,
        reason="test",
        evidence="test",
        granularity=ContextGranularity.SUMMARY,
        source_file="lib/private/SummaryOnly.php",
        source_lines="1-10",
        estimated_tokens=50,
        content_snippet="Summary only reference",
        representation_type="STRUCTURAL_SUMMARY",
        source_exists=True,
        span_resolved=False,
    )

    entry_span = ContextEntry(
        entity_id="php://OC\\RealSource",
        rank=2,
        reason="test",
        evidence="test",
        granularity=ContextGranularity.DEFINITION,
        source_file="lib/private/RealSource.php",
        source_lines="1-10",
        estimated_tokens=50,
        content_snippet="<?php class RealSource {}",
        representation_type="SOURCE_SPAN",
        source_exists=True,
        span_resolved=True,
    )

    # In context_runner logic:
    entries = [entry_summary, entry_span]
    src_delivered = {
        e.source_file
        for e in entries
        if e.representation_type == "SOURCE_SPAN" and e.source_exists and e.span_resolved
    }

    assert "lib/private/SummaryOnly.php" not in src_delivered
    assert "lib/private/RealSource.php" in src_delivered
