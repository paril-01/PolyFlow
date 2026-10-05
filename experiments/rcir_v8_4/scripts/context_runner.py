#!/usr/bin/env python3
"""
RCIR v8.4 — Decoupled Context Runner (PHASE 76).

Architectural Rule:
This process has NO access to ground truth data or paths.
It reads raw retrieval predictions, applies ContextPlanner and ContextCompiler,
enforces strict token budget invariants on exact rendered markdown prompts,
and outputs compiled context packages.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

from rcir.context.compiler import ContextCompiler
from rcir.context.planner import ContextPlanner
from rcir.context.tokenizer import get_default_token_counter
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import RankedCandidate, ScoreBreakdown

DATASETS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "datasets"
RAW_RETRIEVAL_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "raw" / "retrieval"
RAW_CONTEXT_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "raw" / "context"

RAW_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

BUDGETS = [2000, 4000, 8000]


def run_context(split: str) -> dict[str, Any]:
    pred_path = RAW_RETRIEVAL_DIR / f"{split}_predictions.json"
    if not pred_path.exists():
        raise FileNotFoundError(f"Predictions not found: {pred_path}. Run retrieval_runner.py first.")

    pred_data = json.loads(pred_path.read_text(encoding="utf-8"))
    task_preds = pred_data.get("task_predictions", {})

    dataset_path = DATASETS_DIR / f"{split}.json"
    tasks_meta = {t["task_id"]: t for t in json.loads(dataset_path.read_text(encoding="utf-8")).get("tasks", [])}

    print(f"Running decoupled context compilation for split: '{split}' ({len(task_preds)} tasks)...")

    compiler = ContextCompiler(repo_root=REPO_ROOT, tokenizer=get_default_token_counter())

    compiled_results: dict[str, Any] = {
        "split": split,
        "version": "8.4",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task_contexts": {},
    }

    for task_id, p_info in task_preds.items():
        t_meta = tasks_meta.get(task_id, {})
        spec_data = t_meta.get("spec", {})
        op_str = spec_data.get("operation", "behavior_change")
        try:
            op = ChangeOperation(op_str)
        except ValueError:
            op = ChangeOperation.BEHAVIOR_CHANGE

        spec = ChangeSpecification(
            operation=op,
            requested_symbol=spec_data.get("requested_symbol", ""),
            target_file_hint=spec_data.get("target_file_hint"),
            canonical_target_ids=spec_data.get("canonical_target_ids", []),
            description=t_meta.get("description", ""),
        )

        # Reconstruct RankedCandidates from raw predictions
        ranked_cands: list[RankedCandidate] = []
        for c_dict in p_info.get("ranked_candidates", []):
            ev_dict = c_dict.get("evidence", {})
            ev = EvidenceVector(
                entity_id=ev_dict.get("entity_id", c_dict["entity_id"]),
                file_path=ev_dict.get("file_path", c_dict["file_path"]),
                entity_match=ev_dict.get("entity_match", "none"),
                resolution_class=ev_dict.get("resolution_class", "not_analyzed"),
                edge_types=ev_dict.get("edge_types", []),
                hop_distance=ev_dict.get("hop_distance", 1),
                traversal_score=ev_dict.get("traversal_score", 0.5),
                test_relationship=ev_dict.get("test_relationship", "none"),
                boundary_contract=ev_dict.get("boundary_contract", "none"),
            )
            sb = ScoreBreakdown()
            ranked_cands.append(RankedCandidate(
                rank=c_dict["rank"],
                entity_id=c_dict["entity_id"],
                file_path=c_dict["file_path"],
                total_score=c_dict["total_score"],
                evidence=ev,
                breakdown=sb,
            ))

        compiled_results["task_contexts"][task_id] = {
            "task_id": task_id,
            "target_entity": p_info["target_entity"],
            "budgets": {},
        }

        for budget in BUDGETS:
            # Plan and compile context package
            plan = ContextPlanner.create_plan(
                ranked_candidates=ranked_cands,
                token_budget=budget,
                spec=spec,
            )

            compiled = compiler.compile(
                ranked_candidates=ranked_cands,
                token_budget=budget,
                pinned_targets=set(spec.canonical_target_ids),
                plan=plan,
            )

            # Strict Token-Budget Invariant assertion (Phase 50 & 51)
            assert compiled.total_estimated_tokens <= budget, (
                f"BUDGET INVARIANT VIOLATED for {task_id} at {budget}: "
                f"{compiled.total_estimated_tokens} > {budget}"
            )

            included_files = sorted(list({e.source_file for e in compiled.entries if e.source_file}))
            compiled_results["task_contexts"][task_id]["budgets"][str(budget)] = {
                "budget": budget,
                "tokens_consumed": compiled.total_estimated_tokens,
                "entries_count": len(compiled.entries),
                "entities_merged": compiled.entities_merged,
                "included_entities": [e.entity_id for e in compiled.entries],
                "included_files": included_files,
                "prompt_markdown": compiled.render_prompt_markdown(),
            }

    output_path = RAW_CONTEXT_DIR / f"{split}_contexts.json"
    output_path.write_text(json.dumps(compiled_results, indent=2), encoding="utf-8")
    print(f"Saved compiled contexts for {len(task_preds)} tasks to {output_path}")
    return compiled_results


def main():
    parser = argparse.ArgumentParser(description="RCIR v8.4 Decoupled Context Runner")
    parser.add_argument("--split", choices=["dev", "validation", "test", "all"], default="all")
    args = parser.parse_args()

    splits = ["dev", "validation", "test"] if args.split == "all" else [args.split]
    for s in splits:
        run_context(s)

    print("All context compilations successfully completed within strict token budgets.")


if __name__ == "__main__":
    main()
