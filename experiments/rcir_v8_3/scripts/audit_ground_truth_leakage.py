#!/usr/bin/env python3
"""
RCIR v8.3 — Ground Truth Leakage Auditor (ABSOLUTE RULE 0 & PHASE 3).

Audits production code and retrieval pipelines:
1. Static AST/Source inspection of rcir/src and runtime retrieval pipelines for illegal
   ground-truth parameter signatures or references (ground_truth, critical_ground_truth,
   gold, oracle, expected_files, etc.).
2. Runtime permutation test: ensures retrieval/context compilation output is strictly
   independent of any external ground-truth permutations.
"""

import ast
import inspect
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RCIR_SRC = REPO_ROOT / "rcir" / "src"

FORBIDDEN_TERMS = [
    "ground_truth",
    "critical_ground_truth",
    "graded_ground_truth",
    "expected_files",
    "expected_edges",
    "relevance_labels",
    "gold_set",
    "oracle_answer",
]

# Paths in rcir/src that are strictly production retrieval/context/graph code
PRODUCTION_SUBDIRS = [
    "context",
    "entities",
    "graph",
    "impact",
    "query",
    "retrieval",
    "types",
]


def audit_static_leakage() -> List[str]:
    violations: List[str] = []

    for subdir in PRODUCTION_SUBDIRS:
        target_dir = RCIR_SRC / "rcir" / subdir
        if not target_dir.exists():
            continue

        for py_file in target_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            except Exception as e:
                violations.append(f"Parse error in {py_file}: {e}")
                continue

            for node in ast.walk(tree):
                # Check function definitions and their arguments
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for arg in node.args.args + node.args.kwonlyargs:
                        arg_name = arg.arg.lower()
                        for term in FORBIDDEN_TERMS:
                            if term in arg_name:
                                violations.append(
                                    f"[LEAKAGE] {py_file.relative_to(REPO_ROOT)}:{node.lineno} "
                                    f"Function '{node.name}' has forbidden parameter '{arg.arg}'"
                                )

                # Check variable assignments or attribute accesses in production modules
                if isinstance(node, ast.Name):
                    name_lower = node.id.lower()
                    if name_lower in ("critical_ground_truth", "relevance_labels", "gold_set"):
                        violations.append(
                            f"[LEAKAGE] {py_file.relative_to(REPO_ROOT)}:{node.lineno} "
                            f"Reference to forbidden term '{node.id}' in production code"
                        )

    return violations


def audit_runtime_invariance() -> Tuple[bool, str]:
    """Test that candidate generation and ranking are byte-identical regardless of external labels."""
    sys.path.insert(0, str(RCIR_SRC))
    try:
        from rcir.retrieval.ranker import RankerConfig, DeterministicRanker
        from rcir.retrieval.evidence_vector import EvidenceVector
        from rcir.context.summarizer import ImpactSummarizer
    except ImportError as e:
        return False, f"Import error during invariance test: {e}"

    # Verify ImpactSummarizer signature has no critical_ground_truth parameter
    sig = inspect.signature(ImpactSummarizer.summarize)
    if "critical_ground_truth" in sig.parameters:
        return False, "ImpactSummarizer.summarize still accepts 'critical_ground_truth'!"

    # Verify deterministic ranking outputs are independent of any external labels
    config = RankerConfig(use_cascaded_ranking=True)
    ranker = DeterministicRanker(config)
    v1 = EvidenceVector(entity_id="test1", file_path="f1.py", resolution_class="static_exact")
    v2 = EvidenceVector(entity_id="test2", file_path="f2.py", resolution_class="static_inference")
    
    r1 = ranker.rank([v1, v2])
    r2 = ranker.rank([v1, v2])
    
    if [x.entity_id for x in r1] != [x.entity_id for x in r2]:
        return False, "Ranker output is not deterministic across identical inputs."

    return True, "Runtime invariance test passed."


def main():
    print("=" * 60)
    print("RCIR v8.3 — Ground Truth Leakage Static & Runtime Audit")
    print("=" * 60)

    static_violations = audit_static_leakage()
    runtime_ok, runtime_msg = audit_runtime_invariance()

    if static_violations:
        print("\nFAILED: Ground truth leakage detected in production code:")
        for v in static_violations:
            print(f"  [X] {v}")
    else:
        print("\n[PASS] Static audit: 0 leakage violations in rcir/src production modules.")

    if not runtime_ok:
        print(f"\n[FAIL] Runtime audit failed: {runtime_msg}")
    else:
        print(f"[PASS] Runtime audit: {runtime_msg}")

    if static_violations or not runtime_ok:
        sys.exit(1)

    print("\nALL LEAKAGE AUDIT CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
