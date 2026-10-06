"""
RCIR v8.5 — Context Compiler Runner & Saturation Evaluator (PHASES 37-45, 67, 68).

Features:
- Configures ContextCompiler with env.target_repo_root (PHASE 37).
- Rejects file-reference stubs from counting as source context (PHASE 38).
- Records rich Phase 39 metadata (source_file, source_exists, span_resolved, content_hash, representation_type).
- Splits CriticalFileRecall@Budget from CriticalSourceRecall@Budget (PHASE 40).
- Strictly enforces exact rendered prompt token budget <= budget (PHASE 41).
- Context saturation curve across 1k, 2k, 4k, 8k, 16k (PHASE 68).
- Saves raw/context/* and results/context_*.
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

from rcir.context.compiler import ContextCompiler, ContextGranularity
from rcir.context.planner import ContextPlanner
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import RankedCandidate, ScoreBreakdown


def run_context_compilation():
    print("=" * 80)
    print("RCIR v8.5 — Context Compilation & Saturation Curve Runner (PHASES 37-45, 67, 68)")
    print("=" * 80)

    # Instantiate compiler strictly with target_repo_root (PHASE 37)
    compiler = ContextCompiler(repo_root=env.target_repo_root)

    # Load Ground Truth
    gt_data = json.loads((env.ground_truth_root / "ground_truth.json").read_text(encoding="utf-8"))
    gt_tasks = gt_data["tasks"]

    # 1. Compile standard contexts (budget=4000) for DEV, VALIDATION, and TEST
    for split in ("dev", "validation", "test"):
        raw_pred_file = env.raw_root / "retrieval" / f"{split}_predictions.json"
        if not raw_pred_file.exists():
            raise FileNotFoundError(f"Missing retrieval predictions for {split} at {raw_pred_file}")

        pred_data = json.loads(raw_pred_file.read_text(encoding="utf-8"))
        tasks_preds = pred_data["tasks"]
        print(f"Compiling context (budget=4000) for {split.upper()} ({len(tasks_preds)} tasks)...")

        dataset = json.loads((env.dataset_root / f"{split}.json").read_text(encoding="utf-8"))
        ds_tasks = {t["task_id"]: t for t in dataset["tasks"]}

        raw_context_entries: dict[str, Any] = {}
        file_recalls = []
        source_recalls = []
        token_usages = []
        budget_violations = 0
        total_relevant_tokens = 0
        total_delivered_tokens = 0
        total_unresolved_spans = 0
        total_entries = 0

        for tid, t_pred in tasks_preds.items():
            gt_task = gt_tasks.get(tid)
            if not gt_task:
                continue

            target_file = gt_task["target_file"]
            critical_files = set(gt_task["critical_files"])
            expected_files = set(gt_task["expected_files"])

            ds_t = ds_tasks.get(tid, {})
            spec_data = ds_t.get("spec", {})
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
            )

            # Reconstruct RankedCandidates from prediction dump
            ranked_cands = []
            for rc in t_pred["ranked_candidates"]:
                vec = EvidenceVector(
                    entity_id=rc["entity_id"],
                    file_path=rc["file_path"],
                    hop_distance=rc.get("hop_distance", 1),
                    edge_types=rc.get("edge_types", []),
                    resolution_class=rc.get("resolution_class", "static_exact"),
                )
                ranked_cands.append(RankedCandidate(
                    rank=rc["rank"],
                    entity_id=rc["entity_id"],
                    file_path=rc["file_path"],
                    total_score=rc["score"],
                    evidence=vec,
                    breakdown=ScoreBreakdown(),
                ))

            # Create context plan (PHASE 43, 44, 45)
            plan = ContextPlanner.create_plan(
                ranked_candidates=ranked_cands,
                token_budget=4000,
                spec=spec,
            )

            # Compile context
            compiled = compiler.compile(
                ranked_candidates=ranked_cands,
                token_budget=4000,
                pinned_targets=set(spec.canonical_target_ids),
                plan=plan,
            )

            # Strict budget invariant check (PHASE 41)
            if compiled.total_estimated_tokens > 4000:
                budget_violations += 1

            token_usages.append(compiled.total_estimated_tokens)

            # Calculate CriticalFileRecall vs CriticalSourceRecall (PHASE 40)
            files_delivered = {e.source_file for e in compiled.entries if e.source_file}
            file_rec = len(critical_files.intersection(files_delivered)) / max(1, len(critical_files))
            file_recalls.append(file_rec)

            source_delivered = set()
            for e in compiled.entries:
                total_entries += 1
                if e.representation_type == "UNRESOLVED":
                    total_unresolved_spans += 1
                elif e.representation_type in ("SOURCE_SPAN", "STRUCTURAL_SUMMARY"):
                    source_delivered.add(e.source_file)
                    if e.source_file in expected_files:
                        total_relevant_tokens += e.estimated_tokens
                total_delivered_tokens += e.estimated_tokens

            source_rec = len(critical_files.intersection(source_delivered)) / max(1, len(critical_files))
            source_recalls.append(source_rec)

            raw_context_entries[tid] = {
                "task_id": tid,
                "total_tokens": compiled.total_estimated_tokens,
                "token_budget": compiled.token_budget,
                "entries_count": len(compiled.entries),
                "critical_file_recall": round(file_rec, 4),
                "critical_source_recall": round(source_rec, 4),
                "entries": [e.to_dict() for e in compiled.entries],
                "rendered_prompt_markdown": compiled.render_prompt_markdown(),
            }

        mean_file_recall = sum(file_recalls) / max(1, len(file_recalls))
        mean_source_recall = sum(source_recalls) / max(1, len(source_recalls))
        mean_tokens = sum(token_usages) / max(1, len(token_usages))
        unresolved_rate = total_unresolved_spans / max(1, total_entries)
        relevant_token_ratio = total_relevant_tokens / max(1, total_delivered_tokens)

        # Write raw dump
        raw_ctx_payload = {
            "run_id": env.run_id,
            "split": split,
            "token_budget": 4000,
            "total_tasks": len(raw_context_entries),
            "tasks": raw_context_entries,
        }
        raw_file = env.raw_root / "context" / f"{split}_contexts.json"
        raw_file.write_text(json.dumps(raw_ctx_payload, indent=2), encoding="utf-8")
        print(f"Saved raw contexts to {raw_file}")

        # Write results/context_{split}.json
        res_payload = {
            "run_id": env.run_id,
            "split": split,
            "token_budget": 4000,
            "critical_file_recall_at_4k": round(mean_file_recall, 4),
            "critical_source_recall_at_4k": round(mean_source_recall, 4),
            "mean_delivered_tokens": round(mean_tokens, 1),
            "token_budget_violations": budget_violations,
            "unresolved_span_rate": round(unresolved_rate, 4),
            "relevant_token_ratio": round(relevant_token_ratio, 4),
            "strict_budget_invariant_satisfied": (budget_violations == 0),
            "meets_4k_source_target": (mean_source_recall >= 0.60),
        }
        res_file = env.results_root / f"context_{split}.json"
        res_file.write_text(json.dumps(res_payload, indent=2), encoding="utf-8")
        print(f"[{split.upper()}] Critical File Recall: {mean_file_recall*100:.1f}%, Critical Source Recall: {mean_source_recall*100:.1f}%, Mean Tokens: {mean_tokens:.0f}, Budget Violations: {budget_violations}")

    # 2. CONTEXT SATURATION CURVE (PHASE 68) ON TEST SPLIT
    print("\n--- Evaluating Context Saturation Curve on TEST Split (PHASE 68) ---")
    budgets = [1000, 2000, 4000, 8000, 16000]
    curve_results = {}

    test_preds = json.loads((env.raw_root / "retrieval" / "test_predictions.json").read_text(encoding="utf-8"))["tasks"]
    test_ds = json.loads((env.dataset_root / "test.json").read_text(encoding="utf-8"))["tasks"]
    test_ds_map = {t["task_id"]: t for t in test_ds}

    for b in budgets:
        b_file_recalls = []
        b_source_recalls = []
        b_tokens = []
        b_violations = 0

        for tid, t_pred in test_preds.items():
            gt_task = gt_tasks.get(tid)
            if not gt_task:
                continue

            critical_files = set(gt_task["critical_files"])
            spec_data = test_ds_map[tid]["spec"]
            spec = ChangeSpecification(
                operation=ChangeOperation(spec_data.get("operation", "behavior_change")),
                requested_symbol=spec_data.get("requested_symbol", ""),
                target_file_hint=spec_data.get("target_file_hint"),
                canonical_target_ids=spec_data.get("canonical_target_ids", []),
            )

            ranked_cands = []
            for rc in t_pred["ranked_candidates"]:
                vec = EvidenceVector(
                    entity_id=rc["entity_id"],
                    file_path=rc["file_path"],
                    hop_distance=rc.get("hop_distance", 1),
                    edge_types=rc.get("edge_types", []),
                    resolution_class=rc.get("resolution_class", "static_exact"),
                )
                ranked_cands.append(RankedCandidate(
                    rank=rc["rank"],
                    entity_id=rc["entity_id"],
                    file_path=rc["file_path"],
                    total_score=rc["score"],
                    evidence=vec,
                    breakdown=ScoreBreakdown(),
                ))

            plan = ContextPlanner.create_plan(
                ranked_candidates=ranked_cands,
                token_budget=b,
                spec=spec,
            )

            compiled = compiler.compile(
                ranked_candidates=ranked_cands,
                token_budget=b,
                pinned_targets=set(spec.canonical_target_ids),
                plan=plan,
            )

            if compiled.total_estimated_tokens > b:
                b_violations += 1
            b_tokens.append(compiled.total_estimated_tokens)

            files_del = {e.source_file for e in compiled.entries if e.source_file}
            b_file_recalls.append(len(critical_files.intersection(files_del)) / max(1, len(critical_files)))

            src_del = {e.source_file for e in compiled.entries if e.representation_type in ("SOURCE_SPAN", "STRUCTURAL_SUMMARY")}
            b_source_recalls.append(len(critical_files.intersection(src_del)) / max(1, len(critical_files)))

        mean_f_rec = sum(b_file_recalls) / max(1, len(b_file_recalls))
        mean_s_rec = sum(b_source_recalls) / max(1, len(b_source_recalls))
        mean_tok = sum(b_tokens) / max(1, len(b_tokens))

        curve_results[str(b)] = {
            "budget": b,
            "critical_file_recall": round(mean_f_rec, 4),
            "critical_source_recall": round(mean_s_rec, 4),
            "mean_tokens_delivered": round(mean_tok, 1),
            "budget_violations": b_violations,
        }
        print(f"  Budget {b:>5} tokens -> Critical Source Recall: {mean_s_rec*100:.1f}%, Mean Tokens: {mean_tok:.0f}, Violations: {b_violations}")

    saturation_payload = {
        "run_id": env.run_id,
        "split": "test",
        "saturation_curve": curve_results,
    }
    curve_file = env.results_root / "context_budget_curve_test.json"
    curve_file.write_text(json.dumps(saturation_payload, indent=2), encoding="utf-8")
    print(f"Saved context saturation curve to {curve_file}")
    print("Context runner execution COMPLETE.")


if __name__ == "__main__":
    run_context_compilation()
