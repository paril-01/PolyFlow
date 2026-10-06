"""
Tests for Stage 3: Ranking Semantics & Discovery Channels (F03, F11).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
import pytest
from dataclasses import dataclass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))

from rcir.retrieval.ranker import RankedCandidate, ScoreBreakdown
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.query.change_spec import ChangeSpecification, ChangeOperation
from experiments.rcir_v8_5.scripts.retrieval_runner import (
    compute_split_metrics,
    discover_multi_channel_candidates,
)
from rcir.graph.canonical_graph import CanonicalGraph


def test_f03_file_deduplication_prevents_ndcg_inflation():
    """
    F03 Verification:
    If twenty candidates are from the same relevant dependency file,
    naive scoring counted each one, yielding P@20 = 1.0 and nDCG@50 > 7.0.
    With file-level deduplication, only the first candidate provides gain,
    so P@20 = 1/20 = 0.05 and nDCG <= 1.0.
    """
    target_file = "apps/files/lib/Service/TargetService.php"
    dep_file = "lib/private/Files/Node/RelevantNode.php"

    # Create 20 distinct candidate entities that all reside in dep_file
    duplicate_cands = [
        RankedCandidate(
            rank=i + 1,
            entity_id=f"php://OC\\Files\\Node\\RelevantNode::method_{i}",
            file_path=dep_file,
            total_score=1.0 - (i * 0.01),
            evidence=EvidenceVector(entity_id=f"php://OC\\Files\\Node\\RelevantNode::method_{i}", file_path=dep_file),
            breakdown=ScoreBreakdown(total_score=1.0 - (i * 0.01)),
        )
        for i in range(20)
    ]

    gt_tasks = {
        "TASK-01": {
            "target_file": target_file,
            "expected_files": [dep_file],
            "critical_files": [dep_file],
            "must_change": [dep_file],
            "must_inspect": [],
        }
    }

    metrics = compute_split_metrics({"TASK-01": duplicate_cands}, gt_tasks)

    # Only 1 distinct file matched out of 20 slots -> 1 / 20 = 0.05
    assert metrics["precision_at_20_excluding_target"] == 0.05
    # Graded nDCG must be exactly 1.0 (since the single ideal item is at rank 1) and never > 1.0
    assert 0.0 <= metrics["graded_ndcg_at_50"] <= 1.0
    assert metrics["graded_ndcg_at_50"] == 1.0


def test_f03_target_exclusion_in_ranking():
    """
    F03 Verification:
    Candidates from the target file itself must be excluded from target-exclusion metrics.
    """
    target_file = "apps/files/lib/Service/TargetService.php"
    dep_file = "lib/private/Files/Storage/Storage.php"

    cands = [
        RankedCandidate(
            rank=i + 1,
            entity_id=f"php://OCA\\Files\\Service\\TargetService::method_{i}",
            file_path=target_file,
            total_score=1.0,
            evidence=EvidenceVector(entity_id=f"php://OCA\\Files\\Service\\TargetService::method_{i}", file_path=target_file),
            breakdown=ScoreBreakdown(total_score=1.0),
        )
        for i in range(10)
    ] + [
        RankedCandidate(
            rank=11,
            entity_id="php://OC\\Files\\Storage\\Storage::get",
            file_path=dep_file,
            total_score=0.5,
            evidence=EvidenceVector(entity_id="php://OC\\Files\\Storage\\Storage::get", file_path=dep_file),
            breakdown=ScoreBreakdown(total_score=0.5),
        )
    ]

    gt_tasks = {
        "TASK-02": {
            "target_file": target_file,
            "expected_files": [dep_file],
            "critical_files": [dep_file],
            "must_change": [],
            "must_inspect": [dep_file],
        }
    }

    metrics = compute_split_metrics({"TASK-02": cands}, gt_tasks)

    # After target exclusion, dep_file is at rank 1 of the excluded list
    assert metrics["dependency_mrr"] == 1.0
    assert metrics["precision_at_20_excluding_target"] == 1.0 / 20.0
    assert 0.0 <= metrics["graded_ndcg_at_50"] <= 1.0


def test_f11_discovery_channels_honest_inference():
    """
    F11 Verification:
    Channels B, C, D, E, F must not claim 'static_exact' without exact compiler proof;
    they must use 'static_inference'. Unrelated targets must not inherit hardcoded
    unrelated tests (ManagerTest, SessionTest).
    """
    cg = CanonicalGraph()
    spec = ChangeSpecification(
        operation=ChangeOperation.SIGNATURE_CHANGE,
        requested_symbol="php://OCA\\CustomApp\\Service\\CustomService::execute",
        canonical_target_ids=["php://OCA\\CustomApp\\Service\\CustomService::execute"],
    )

    res = discover_multi_channel_candidates(spec, cg, cg.registry)

    # Check resolution class on any discovered candidate (excluding the target itself)
    for ent_id, ev in res.candidates.items():
        if ent_id != "php://OCA\\CustomApp\\Service\\CustomService::execute":
            assert ev.resolution_class == "static_inference"

    # ManagerTest and SessionTest must NOT be present for unrelated target
    for ent_id, ev in res.candidates.items():
        assert "ManagerTest" not in ev.file_path
        assert "SessionTest" not in ev.file_path
