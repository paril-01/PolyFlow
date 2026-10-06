"""
RCIR v8.5 — Canonicalization Benchmark Evaluator (PHASES 25, 26).

Evaluates the real CanonicalEntityRegistry loaded with the full 48k+ Nextcloud graph
against an independent, verified canonicalization corpus:
- Tests FQN, short aliases, file-qualified aliases, routes, external types, and unresolved symbols.
- Resolves against the REAL loaded graph registry, NOT an artificial unit fixture!
- Generates results/canonicalization_evaluation.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from environment import get_default_environment

env = get_default_environment()
sys.path.insert(0, str(env.polyflow_root / "rcir" / "src"))

from rcir.entities.canonical import AliasResolution
from rcir.graph.canonical_graph import CanonicalGraph


def evaluate_canonicalization():
    print("=" * 80)
    print("RCIR v8.5 — Canonicalization Evaluation on Real Graph (PHASES 25, 26)")
    print("=" * 80)

    corpus_path = env.canonicalization_ground_truth_root / "canonicalization_corpus.json"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Missing canonicalization corpus at {corpus_path}")

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))["records"]
    print(f"Loaded {len(corpus)} verified canonicalization test records.")

    print(f"Loading full CanonicalGraph from {env.graph_path}...")
    raw_graph = json.loads(env.graph_path.read_text(encoding="utf-8"))
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)
    registry = cg.registry
    normalizer = cg.normalizer
    print(f"Registry ready with {len(registry.entities)} indexed entities.")

    correct_exact = 0
    correct_unique_alias = 0
    wrong_resolution = 0
    ambiguous = 0
    unresolved = 0

    eval_records = []

    for item in corpus:
        raw_ref = item["raw_reference"]
        ctx_file = item.get("context_file", "")
        expected_id = item["expected_canonical_id"]

        # Resolve using normalizer + registry
        normalized = normalizer.normalize_endpoint(raw_ref, registry, context_file=ctx_file)
        res = registry.resolve(raw_ref, target_file_hint=ctx_file)

        predicted = res.canonical_id or normalized

        is_match = (predicted == expected_id)
        if is_match:
            if res.resolution == AliasResolution.EXACT or normalized == expected_id:
                correct_exact += 1
                status = "CORRECT_EXACT"
            else:
                correct_unique_alias += 1
                status = "CORRECT_UNIQUE_ALIAS"
        else:
            if res.resolution == AliasResolution.AMBIGUOUS:
                ambiguous += 1
                status = "AMBIGUOUS"
            elif res.resolution == AliasResolution.UNRESOLVED and expected_id.startswith("unresolved://"):
                correct_exact += 1
                status = "CORRECT_UNRESOLVED"
            elif res.resolution == AliasResolution.UNRESOLVED:
                unresolved += 1
                status = "UNRESOLVED"
            else:
                wrong_resolution += 1
                status = "WRONG_RESOLUTION"

        eval_records.append({
            "raw_reference": raw_ref,
            "context_file": ctx_file,
            "expected_canonical_id": expected_id,
            "predicted_id": predicted,
            "resolution_status": status,
            "is_correct": is_match,
        })
        print(f"  [{status}] '{raw_ref}' -> '{predicted}' (expected: '{expected_id}')")

    total = len(corpus)
    accuracy = (correct_exact + correct_unique_alias) / max(1, total)
    wrong_rate = wrong_resolution / max(1, total)

    result_payload = {
        "run_id": env.run_id,
        "target_commit": env.target_repo_commit,
        "total_test_records": total,
        "correct_exact": correct_exact,
        "correct_unique_alias": correct_unique_alias,
        "wrong_resolution": wrong_resolution,
        "ambiguous": ambiguous,
        "unresolved": unresolved,
        "accuracy": round(accuracy, 4),
        "wrong_resolution_rate": round(wrong_rate, 4),
        "meets_contract_target": wrong_rate <= 0.01,
        "eval_records": eval_records,
    }

    res_file = env.results_root / "canonicalization_evaluation.json"
    res_file.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(f"Saved canonicalization evaluation result to {res_file}")
    print(f"Accuracy: {accuracy*100:.1f}%, Wrong Resolution Rate: {wrong_rate*100:.2f}%")


if __name__ == "__main__":
    evaluate_canonicalization()
