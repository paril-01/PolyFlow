"""
Ground truth schema and precision/recall computation for RCIR evaluation.

Implements §1 of the v7 plan: formal, per-edge-class precision and recall
measured against an independently-established ground truth.

The ground truth is a set of edges that actually exist for a given change,
established by manual verification or synthetic injection — NOT by asking
RCIR itself (that would be circular).

Metrics computed:
- Precision per edge class: of edges RCIR reports, how many are real?
- Recall per edge class: of edges that actually exist, how many did RCIR find?
- Unresolved rate: ground-truth edges RCIR explicitly flags as unresolvable
  (a known gap, different from a silent miss)
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal


# Edge classes per v7 §1
EdgeClass = Literal["static_exact", "static_inference", "dynamic_unresolved", "unsupported"]


@dataclass
class GroundTruthEdge:
    """A single edge in the ground truth set.

    Represents a dependency that actually exists for a given change,
    established independently of RCIR.
    """
    source: str        # qualified path of the source node
    target: str        # qualified path of the target node
    edge_class: EdgeClass  # how RCIR *should* classify this edge
    description: str = ""  # human-readable explanation of why this edge exists

    def to_dict(self) -> dict:
        d = {"source": self.source, "target": self.target, "edge_class": self.edge_class}
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "GroundTruthEdge":
        return cls(
            source=d["source"],
            target=d["target"],
            edge_class=d["edge_class"],
            description=d.get("description", ""),
        )


@dataclass
class DiscoveredEdge:
    """An edge that RCIR actually discovered during analysis."""
    source: str
    target: str
    edge_class: EdgeClass
    confidence: float
    reason: str = ""
    edge_type: str = "calls"

    def to_dict(self) -> dict:
        d = {
            "source": self.source, "target": self.target,
            "edge_class": self.edge_class, "confidence": self.confidence,
            "edge_type": self.edge_type,
        }
        if self.reason:
            d["reason"] = self.reason
        return d


@dataclass
class EdgeClassMetrics:
    """Precision/recall for a single edge class."""
    edge_class: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0  # silent misses — ground truth edges RCIR didn't find at all
    unresolved: int = 0       # ground truth edges RCIR flagged as unresolvable (a known gap)

    @property
    def precision(self) -> float | None:
        """Of edges RCIR reports in this class, fraction that are real."""
        total_reported = self.true_positives + self.false_positives
        if total_reported == 0:
            return None
        return self.true_positives / total_reported

    @property
    def recall(self) -> float | None:
        """Of ground truth edges in this class, fraction RCIR found."""
        total_ground_truth = self.true_positives + self.false_negatives + self.unresolved
        if total_ground_truth == 0:
            return None
        return self.true_positives / total_ground_truth

    @property
    def unresolved_rate(self) -> float | None:
        """Fraction of ground truth edges explicitly flagged as unresolvable."""
        total_ground_truth = self.true_positives + self.false_negatives + self.unresolved
        if total_ground_truth == 0:
            return None
        return self.unresolved / total_ground_truth

    def to_dict(self) -> dict:
        return {
            "edge_class": self.edge_class,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "unresolved": self.unresolved,
            "precision": self.precision,
            "recall": self.recall,
            "unresolved_rate": self.unresolved_rate,
        }


@dataclass
class PrecisionRecallReport:
    """Full precision/recall report across all edge classes.

    This is the concrete measurement of v7 §1's three separated properties:
    soundness (precision), recall, and auditability (unresolved rate + reasons).
    """
    total_graph_edges: int = 0
    candidates_evaluated: int = 0
    ground_truth_edges: int = 0
    per_class: dict[str, EdgeClassMetrics] = field(default_factory=dict)
    # Edges RCIR found that don't match any ground truth edge
    false_positive_details: list[dict] = field(default_factory=list)
    # Ground truth edges RCIR missed entirely (silent misses)
    false_negative_details: list[dict] = field(default_factory=list)
    # Ground truth edges RCIR flagged as unresolvable
    unresolved_details: list[dict] = field(default_factory=list)

    @property
    def overall_precision(self) -> float | None:
        total_tp = sum(m.true_positives for m in self.per_class.values())
        total_fp = sum(m.false_positives for m in self.per_class.values())
        total = total_tp + total_fp
        if total == 0:
            return None
        return total_tp / total

    @property
    def overall_recall(self) -> float | None:
        total_tp = sum(m.true_positives for m in self.per_class.values())
        total_fn = sum(m.false_negatives for m in self.per_class.values())
        total_unresolved = sum(m.unresolved for m in self.per_class.values())
        total = total_tp + total_fn + total_unresolved
        if total == 0:
            return None
        return total_tp / total

    @property
    def overall_unresolved_rate(self) -> float | None:
        total_tp = sum(m.true_positives for m in self.per_class.values())
        total_fn = sum(m.false_negatives for m in self.per_class.values())
        total_unresolved = sum(m.unresolved for m in self.per_class.values())
        total = total_tp + total_fn + total_unresolved
        if total == 0:
            return None
        return total_unresolved / total

    def to_dict(self) -> dict:
        return {
            "overall": {
                "precision": self.overall_precision,
                "recall": self.overall_recall,
                "unresolved_rate": self.overall_unresolved_rate,
                "total_graph_edges": self.total_graph_edges,
                "candidates_evaluated": self.candidates_evaluated,
                "ground_truth_edges": self.ground_truth_edges,
            },
            "per_class": {k: v.to_dict() for k, v in self.per_class.items()},
            "false_positive_details": self.false_positive_details,
            "false_negative_details": self.false_negative_details,
            "unresolved_details": self.unresolved_details,
        }


def _edge_key(source: str, target: str) -> tuple[str, str]:
    """Normalize an edge to a comparable key."""
    return (source, target)


def is_cross_service_candidate(edge: DiscoveredEdge) -> bool:
    """Determine if a discovered edge is a candidate for cross-service evaluation.

    Includes:
    - Proto RPC and message definitions (.proto file as source or target)
    - Cross-language / gRPC calls (reason has 'cross-language' or 'grpc')
    - HTTP route handlers and calls (target has EXTERNAL_HTTP, UNRESOLVED_HTTP, or reason has 'http')
    - Service implementations (edge_type is 'implements' or reason has 'implementation')
    - Calls targeting gRPC services or methods (target has Service. or Servicer.)

    Excludes:
    - Ordinary intra-file plumbing (import os, sys, json, logging, time, etc.)
    - Generated protobuf bindings & internal libraries (google.protobuf, opentelemetry, grpc_health, jinja2)
    - Standard library inheritance
    """
    src = edge.source
    tgt = edge.target
    reason_lower = edge.reason.lower()

    # Exclude library/framework imports & internal plumbing
    if tgt.startswith((
        "google.protobuf", "opentelemetry", "grpc.", "grpc_health",
        "jinja2", "logging", "logger", "os", "sys", "time", "random",
    )):
        return False
    if src.endswith(("_pb2.py", "_pb2_grpc.py")):
        return False

    # 1. Proto definitions (.proto file as source or target)
    if src.endswith(".proto") or ".proto::" in src or tgt.endswith(".proto") or ".proto::" in tgt:
        return True

    # 2. Cross-language / RPC calls
    if "cross-language" in reason_lower or "grpc" in reason_lower:
        return True

    # 3. HTTP routes and client calls
    if "http" in reason_lower or "external_http" in tgt.lower() or "unresolved_http" in tgt.lower():
        return True

    # 4. Service implementations
    if edge.edge_type == "implements" or "implementation" in reason_lower:
        return True

    # 5. Calls to Service or Service.Method
    target_clean = tgt.split("::")[-1]
    if any(s in target_clean for s in ["Service.", "Servicer."]):
        return True

    return False


def compute_precision_recall(
    discovered: list[DiscoveredEdge],
    ground_truth: list[GroundTruthEdge],
    candidate_filter: Callable[[DiscoveredEdge], bool] | None = None,
) -> PrecisionRecallReport:
    """Compute per-edge-class precision and recall.

    Matching logic:
    - An edge is a "match" if its (source, target) pair matches a ground truth edge.
    - True positive: discovered edge matches a ground truth edge.
    - False positive: discovered edge has no matching ground truth edge.
    - False negative: ground truth edge has no matching discovered edge (silent miss).
    - Unresolved: ground truth edge was discovered but classified as
      dynamic_unresolved or unsupported (RCIR knows it can't resolve it —
      this is an explicitly-reported gap, different from a silent miss).

    The candidate_filter allows scoping evaluation to like-with-like candidates
    (e.g., cross-service/contract edges) so intra-file plumbing edges (like import os)
    are not falsely counted as false positives against a cross-service ground truth.
    """
    total_graph_edges = len(discovered)
    if candidate_filter is not None:
        discovered = [e for e in discovered if candidate_filter(e)]
    candidates_evaluated = len(discovered)

    # Index ground truth by (source, target)
    gt_by_key: dict[tuple[str, str], GroundTruthEdge] = {}
    for gt_edge in ground_truth:
        key = _edge_key(gt_edge.source, gt_edge.target)
        gt_by_key[key] = gt_edge

    # Index discovered by (source, target)
    disc_by_key: dict[tuple[str, str], DiscoveredEdge] = {}
    for disc_edge in discovered:
        key = _edge_key(disc_edge.source, disc_edge.target)
        disc_by_key[key] = disc_edge

    # Initialize per-class metrics for all classes we encounter
    all_classes = set()
    for gt in ground_truth:
        all_classes.add(gt.edge_class)
    for d in discovered:
        all_classes.add(d.edge_class)

    report = PrecisionRecallReport(
        total_graph_edges=total_graph_edges,
        candidates_evaluated=candidates_evaluated,
        ground_truth_edges=len(ground_truth),
    )
    for cls in sorted(all_classes):
        report.per_class[cls] = EdgeClassMetrics(edge_class=cls)

    matched_gt_keys: set[tuple[str, str]] = set()

    # Check each discovered edge against ground truth
    for key, disc in disc_by_key.items():
        gt = gt_by_key.get(key)
        if gt is not None:
            # This discovered edge matches a ground truth edge
            matched_gt_keys.add(key)

            if disc.edge_class in ("dynamic_unresolved", "unsupported"):
                cls_name = gt.edge_class
                if cls_name not in report.per_class:
                    report.per_class[cls_name] = EdgeClassMetrics(edge_class=cls_name)
                report.per_class[cls_name].unresolved += 1
                report.unresolved_details.append({
                    "source": disc.source,
                    "target": disc.target,
                    "discovered_class": disc.edge_class,
                    "expected_class": gt.edge_class,
                    "reason": disc.reason,
                })
            else:
                cls_name = gt.edge_class
                if cls_name not in report.per_class:
                    report.per_class[cls_name] = EdgeClassMetrics(edge_class=cls_name)
                report.per_class[cls_name].true_positives += 1
        else:
            # Discovered edge with no ground truth match — false positive
            cls_name = disc.edge_class
            if cls_name not in report.per_class:
                report.per_class[cls_name] = EdgeClassMetrics(edge_class=cls_name)
            report.per_class[cls_name].false_positives += 1
            report.false_positive_details.append({
                "source": disc.source,
                "target": disc.target,
                "edge_class": disc.edge_class,
                "reason": disc.reason,
            })

    # Check ground truth edges not matched — false negatives (silent misses)
    for key, gt in gt_by_key.items():
        if key not in matched_gt_keys:
            cls_name = gt.edge_class
            if cls_name not in report.per_class:
                report.per_class[cls_name] = EdgeClassMetrics(edge_class=cls_name)
            report.per_class[cls_name].false_negatives += 1
            report.false_negative_details.append({
                "source": gt.source,
                "target": gt.target,
                "edge_class": gt.edge_class,
                "description": gt.description,
            })

    return report


def load_ground_truth(path: str | Path) -> list[GroundTruthEdge]:
    """Load ground truth edges from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [GroundTruthEdge.from_dict(e) for e in data["edges"]]


def save_ground_truth(
    edges: list[GroundTruthEdge],
    path: str | Path,
    metadata: dict | None = None,
) -> None:
    """Save ground truth edges to a JSON file."""
    data: dict[str, Any] = {}
    if metadata:
        data["metadata"] = metadata
    data["edges"] = [e.to_dict() for e in edges]
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def compute_task_precision_recall(
    retrieved_items: list[str],
    ground_truth_items: list[str],
) -> dict[str, float]:
    """Compute precision, recall, and F1 strictly within the scope of a task/change.

    Args:
        retrieved_items: Node or edge paths retrieved for this task.
        ground_truth_items: Target node or edge paths defined in the task ground truth.

    Returns:
        dict with 'precision', 'recall', 'f1', 'true_positives', 'false_positives', 'false_negatives'
    """
    retrieved_set = set(retrieved_items)
    gt_set = set(ground_truth_items)

    tp = len(retrieved_set & gt_set)
    fp = len(retrieved_set - gt_set)
    fn = len(gt_set - retrieved_set)

    precision = tp / len(retrieved_set) if retrieved_set else 1.0
    recall = tp / len(gt_set) if gt_set else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }

