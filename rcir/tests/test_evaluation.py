"""
Tests for the precision/recall evaluation framework.

Tests the core metric computation logic against hand-built edge sets,
NOT against any real repo — that comes in Phase 3 (Online Boutique).
"""

import json
import pytest
from pathlib import Path

from rcir.evaluation.ground_truth import (
    GroundTruthEdge,
    DiscoveredEdge,
    EdgeClassMetrics,
    PrecisionRecallReport,
    compute_precision_recall,
    load_ground_truth,
    save_ground_truth,
)


class TestEdgeClassMetrics:
    """Unit tests for the metrics computation on a single edge class."""

    def test_perfect_precision_and_recall(self):
        m = EdgeClassMetrics(edge_class="static_exact", true_positives=10)
        assert m.precision == 1.0
        assert m.recall == 1.0
        assert m.unresolved_rate == 0.0

    def test_some_false_positives(self):
        m = EdgeClassMetrics(edge_class="static_exact", true_positives=8, false_positives=2)
        assert m.precision == 0.8
        assert m.recall == 1.0  # recall denominator doesn't include FP

    def test_some_false_negatives(self):
        m = EdgeClassMetrics(edge_class="static_exact", true_positives=7, false_negatives=3)
        assert m.precision == 1.0  # precision denominator doesn't include FN
        assert m.recall == 0.7

    def test_some_unresolved(self):
        m = EdgeClassMetrics(
            edge_class="static_exact",
            true_positives=7,
            false_negatives=1,
            unresolved=2,
        )
        # Recall denominator: TP + FN + unresolved = 10
        assert m.recall == 0.7
        assert m.unresolved_rate == 0.2

    def test_empty_metrics(self):
        m = EdgeClassMetrics(edge_class="static_exact")
        assert m.precision is None
        assert m.recall is None
        assert m.unresolved_rate is None

    def test_zero_tp_with_fp_is_zero_precision(self):
        m = EdgeClassMetrics(edge_class="static_exact", false_positives=5)
        assert m.precision == 0.0


class TestComputePrecisionRecall:
    """Tests for the core precision/recall computation function."""

    def test_perfect_match(self):
        """All discovered edges match ground truth exactly."""
        gt = [
            GroundTruthEdge("A", "B", "static_exact"),
            GroundTruthEdge("C", "D", "static_exact"),
        ]
        discovered = [
            DiscoveredEdge("A", "B", "static_exact", 1.0),
            DiscoveredEdge("C", "D", "static_exact", 1.0),
        ]
        report = compute_precision_recall(discovered, gt)
        assert report.overall_precision == 1.0
        assert report.overall_recall == 1.0
        assert len(report.false_positive_details) == 0
        assert len(report.false_negative_details) == 0

    def test_false_positives(self):
        """Discovered edges that don't exist in ground truth."""
        gt = [GroundTruthEdge("A", "B", "static_exact")]
        discovered = [
            DiscoveredEdge("A", "B", "static_exact", 1.0),
            DiscoveredEdge("X", "Y", "static_inference", 0.7),  # not in GT
        ]
        report = compute_precision_recall(discovered, gt)
        assert report.overall_precision == 0.5  # 1 TP / (1 TP + 1 FP)
        assert report.overall_recall == 1.0  # found the 1 GT edge
        assert len(report.false_positive_details) == 1
        assert report.false_positive_details[0]["source"] == "X"

    def test_false_negatives(self):
        """Ground truth edges RCIR missed entirely (silent misses)."""
        gt = [
            GroundTruthEdge("A", "B", "static_exact"),
            GroundTruthEdge("C", "D", "static_exact", "missed call site"),
        ]
        discovered = [
            DiscoveredEdge("A", "B", "static_exact", 1.0),
        ]
        report = compute_precision_recall(discovered, gt)
        assert report.overall_precision == 1.0
        assert report.overall_recall == 0.5  # found 1 of 2
        assert len(report.false_negative_details) == 1
        assert report.false_negative_details[0]["source"] == "C"

    def test_unresolved_edges(self):
        """Ground truth edges RCIR found but flagged as unresolvable.

        This is the v7 §1 auditability distinction: RCIR says "I see this
        edge exists but I can't statically resolve it" — this is an
        explicitly-reported gap, different from a silent miss.
        """
        gt = [
            GroundTruthEdge("A", "B", "static_exact"),
            GroundTruthEdge("C", "D", "static_exact"),
        ]
        discovered = [
            DiscoveredEdge("A", "B", "static_exact", 1.0),
            # RCIR found C->D but flagged it as dynamic_unresolved
            DiscoveredEdge("C", "D", "dynamic_unresolved", 0.3, "getattr dispatch"),
        ]
        report = compute_precision_recall(discovered, gt)

        # The unresolved edge is NOT a true positive (RCIR didn't resolve it)
        # but it's also NOT a silent miss (RCIR reported it as a known gap)
        se = report.per_class["static_exact"]
        assert se.true_positives == 1
        assert se.unresolved == 1
        assert se.false_negatives == 0
        assert se.recall == 0.5  # only 1 of 2 actually resolved
        assert se.unresolved_rate == 0.5

        assert len(report.unresolved_details) == 1
        assert report.unresolved_details[0]["reason"] == "getattr dispatch"

    def test_empty_discovered_set(self):
        """RCIR found nothing — all ground truth edges are false negatives."""
        gt = [
            GroundTruthEdge("A", "B", "static_exact"),
            GroundTruthEdge("C", "D", "static_inference"),
        ]
        report = compute_precision_recall([], gt)
        assert report.overall_precision is None  # no edges reported
        assert report.overall_recall == 0.0
        assert len(report.false_negative_details) == 2

    def test_empty_ground_truth(self):
        """No ground truth edges — everything RCIR finds is a false positive."""
        discovered = [
            DiscoveredEdge("A", "B", "static_exact", 1.0),
        ]
        report = compute_precision_recall(discovered, [])
        assert report.overall_precision == 0.0  # all FP
        assert report.overall_recall is None  # no ground truth

    def test_both_empty(self):
        """No edges at all."""
        report = compute_precision_recall([], [])
        assert report.overall_precision is None
        assert report.overall_recall is None

    def test_multi_class_breakdown(self):
        """Precision/recall computed separately per edge class."""
        gt = [
            GroundTruthEdge("A", "B", "static_exact"),
            GroundTruthEdge("C", "D", "static_inference"),
            GroundTruthEdge("E", "F", "static_inference"),
        ]
        discovered = [
            DiscoveredEdge("A", "B", "static_exact", 1.0),
            DiscoveredEdge("C", "D", "static_inference", 0.7),
            # E->F missed
        ]
        report = compute_precision_recall(discovered, gt)

        exact = report.per_class["static_exact"]
        assert exact.precision == 1.0
        assert exact.recall == 1.0

        inferred = report.per_class["static_inference"]
        assert inferred.precision == 1.0
        assert inferred.recall == 0.5  # found 1 of 2

    def test_report_serialization(self):
        """Report can be serialized to dict and contains expected keys."""
        gt = [GroundTruthEdge("A", "B", "static_exact")]
        discovered = [DiscoveredEdge("A", "B", "static_exact", 1.0)]
        report = compute_precision_recall(discovered, gt)
        d = report.to_dict()
        assert "overall" in d
        assert "per_class" in d
        assert "precision" in d["overall"]
        assert "recall" in d["overall"]


class TestGroundTruthIO:
    """Test loading and saving ground truth edge sets."""

    def test_round_trip(self, tmp_path):
        edges = [
            GroundTruthEdge("A", "B", "static_exact", "real import"),
            GroundTruthEdge("C", "D", "static_inference"),
        ]
        path = tmp_path / "gt.json"
        save_ground_truth(edges, path, metadata={"repo": "test", "version": "1.0"})
        loaded = load_ground_truth(path)

        assert len(loaded) == 2
        assert loaded[0].source == "A"
        assert loaded[0].target == "B"
        assert loaded[0].edge_class == "static_exact"
        assert loaded[0].description == "real import"
        assert loaded[1].description == ""

    def test_saved_file_is_valid_json(self, tmp_path):
        edges = [GroundTruthEdge("X", "Y", "dynamic_unresolved")]
        path = tmp_path / "gt.json"
        save_ground_truth(edges, path)
        data = json.loads(path.read_text())
        assert "edges" in data
        assert len(data["edges"]) == 1
