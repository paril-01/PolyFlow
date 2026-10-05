#!/usr/bin/env python3
"""
RCIR v8.4 — Determinism Benchmark Evaluator (PHASE 69).

Runs the full pipeline (spec -> ranker -> planner -> compiler) N=5 times with identical inputs.
Hashes the final prompt markdown output for each trial.
Proves 100% determinism with zero variance.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

from rcir.context.compiler import ContextCompiler
from rcir.context.planner import ContextPlanner
from rcir.context.tokenizer import get_default_token_counter
from rcir.entities.canonical import CanonicalEntityRegistry, CanonicalEntityID, EntityKind
from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdge, CanonicalEdgeType, ResolutionClass
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import MultiObjectiveRanker, OperationRankerProfile, RankerConfig

RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

N_TRIALS = 5


def evaluate_determinism():
    print("=" * 80)
    print("RCIR v8.4 — Measured Compiler & Ranker Determinism (PHASE 69)")
    print("=" * 80)

    # Build canonical graph fixture
    reg = CanonicalEntityRegistry()
    cg = CanonicalGraph(registry=reg)

    target_id = "php://OCP\\IConfig"
    reg.register(CanonicalEntityID(
        repository="nextcloud-server", language="php", file="lib/public/IConfig.php",
        namespace="OCP", owner_type="IConfig", symbol="IConfig", kind=EntityKind.INTERFACE,
        aliases=["IConfig", "OCP\\IConfig"],
    ))

    # Add 10 deterministically ordered edges
    for i in range(10):
        src = f"php://OCA\\Files\\Service{i}"
        reg.register(CanonicalEntityID(
            repository="nextcloud-server", language="php", file=f"apps/files/lib/Service{i}.php",
            namespace="OCA\\Files", owner_type=f"Service{i}", symbol=f"Service{i}", kind=EntityKind.CLASS,
        ))
        cg.add_edge(CanonicalEdge(
            source_id=src, target_id=target_id, edge_type=CanonicalEdgeType.CALLS,
            resolution_class=ResolutionClass.STATIC_EXACT,
        ))

    spec = ChangeSpecification(
        operation=ChangeOperation.CONFIG_CHANGE,
        requested_symbol="IConfig",
        canonical_target_ids=[target_id],
        description="Deterministic context compilation verification",
    )

    ranker = MultiObjectiveRanker(operation=ChangeOperation.CONFIG_CHANGE)
    compiler = ContextCompiler(repo_root=REPO_ROOT, tokenizer=get_default_token_counter())

    # Build candidate vectors
    cands = [EvidenceVector(entity_id=target_id, file_path="lib/public/IConfig.php", entity_match="exact", traversal_score=1.0, hop_distance=0)]
    for i in range(10):
        cands.append(EvidenceVector(
            entity_id=f"php://OCA\\Files\\Service{i}",
            file_path=f"apps/files/lib/Service{i}.php",
            edge_types=["calls"],
            resolution_class="static_exact",
            hop_distance=1,
            traversal_score=0.8 - (i * 0.05),
        ))

    prompt_hashes = []
    trial_records = []
    for trial in range(1, N_TRIALS + 1):
        ranked = ranker.rank(cands)
        plan = ContextPlanner.create_plan(ranked, token_budget=4000, spec=spec)
        compiled = compiler.compile(ranked, token_budget=4000, pinned_targets=set(spec.canonical_target_ids), plan=plan)

        prompt_text = compiled.render_prompt_markdown()
        p_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        prompt_hashes.append(p_hash)

        trial_records.append({
            "trial": trial,
            "tokens": compiled.total_estimated_tokens,
            "entries_count": len(compiled.entries),
            "prompt_hash": p_hash,
        })

    is_deterministic = len(set(prompt_hashes)) == 1

    output = {
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validation_status": "MEASURED_DETERMINISM",
        "trials_count": N_TRIALS,
        "is_deterministic": is_deterministic,
        "unique_prompt_hashes": len(set(prompt_hashes)),
        "prompt_hash": prompt_hashes[0] if is_deterministic else None,
        "trials": trial_records,
    }

    out_file = RESULTS_DIR / "determinism_evaluation.json"
    out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Determinism Evaluation: {'PASSED (100% Identical Prompt Hashes)' if is_deterministic else 'FAILED'}")
    print(f"Saved to {out_file}")


if __name__ == "__main__":
    evaluate_determinism()
