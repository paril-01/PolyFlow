"""
RCIR v8.5 — Ground-Truth Provenance Auditor (PHASES 8, 9, 13, 14, 88).

Audits all ground truth files before retrieval evaluation using Git-committed
content as the authoritative source (PF-RC-CI-001):
- Uses read_repo_file_at_commit() for commit-bound object reading.
- Cryptographically verifies raw Git object hashes and CRLF checkout hashes.
- Validates commits, target files, target symbols, expected files, edge files,
  receiver call sites, and canonicalization corpus contexts.
- Detects genuine file tampering, commit mismatches, and path traversal.
- Side-effect free by default to prevent dirtying tracked historical results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Add parent script dir to path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from environment import BenchmarkEnvironment, BenchmarkIntegrityError, get_default_environment
from git_reader import (
    CommitNotFoundError,
    FileNotFoundAtCommitError,
    PathSecurityError,
    read_repo_file_at_commit,
    validate_safe_relative_path,
    verify_commit_exists,
    verify_content_hash,
)


def audit_provenance(
    env: Optional[BenchmarkEnvironment] = None,
    output_path: Optional[Path | str] = None,
    write_results: bool = False,
) -> Dict[str, Any]:
    print("=" * 80)
    print("RCIR v8.5 — Commit-Bound Ground-Truth Provenance Audit (PF-RC-CI-001)")
    print("=" * 80)

    if env is None:
        env = get_default_environment()

    target_root = env.target_repo_root
    target_commit = env.target_repo_commit

    gt_path = env.ground_truth_root / "ground_truth.json"
    edge_gt_path = env.edge_ground_truth_root / "ground_truth_edges.json"
    receiver_gt_path = env.receiver_ground_truth_root / "receiver_ground_truth.json"
    canon_gt_path = env.canonicalization_ground_truth_root / "canonicalization_corpus.json"

    errors: List[Dict[str, Any]] = []
    audited_tasks: List[Dict[str, Any]] = []
    audited_commits: Set[str] = set()
    worktree_drift_warnings: List[str] = []

    # 1. Verify Ground Truth tasks
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing ground truth file at {gt_path}")

    gt_data = json.loads(gt_path.read_text(encoding="utf-8"))
    tasks = gt_data.get("tasks", {})
    print(f"Auditing {len(tasks)} ground truth tasks against Git object store...")

    for tid, task in tasks.items():
        comm = task.get("upstream_commit", "")
        if not comm:
            errors.append({"task_id": tid, "error_class": "MISSING_COMMIT", "message": f"{tid}: Missing upstream_commit"})
            continue

        if not verify_commit_exists(target_root, comm):
            errors.append({
                "task_id": tid,
                "error_class": "COMMIT_NOT_FOUND",
                "message": f"{tid}: Commit {comm} does NOT exist in target repository git object store!",
            })
            continue
        audited_commits.add(comm)

        # Check target file
        tf = task.get("target_file", "")
        rec_hash = task.get("target_file_hash", "")
        sym = task.get("target_symbol", "")

        try:
            tf_blob = read_repo_file_at_commit(target_root, comm, tf)
            is_match, match_mode, canon_h, crlf_h = verify_content_hash(tf_blob, rec_hash)
            if not is_match:
                errors.append({
                    "task_id": tid,
                    "error_class": "HASH_MISMATCH",
                    "file": tf,
                    "recorded_hash": rec_hash,
                    "canonical_hash": canon_h,
                    "crlf_hash": crlf_h,
                    "message": f"{tid}: Target file {tf} hash mismatch (rec={rec_hash}, canon={canon_h}, crlf={crlf_h})",
                })

            tf_text = tf_blob.decode("utf-8", errors="replace")
            if sym and sym not in tf_text:
                errors.append({
                    "task_id": tid,
                    "error_class": "SYMBOL_NOT_FOUND",
                    "file": tf,
                    "symbol": sym,
                    "message": f"{tid}: Target symbol {sym} not found in committed content of {tf}",
                })

            # Check worktree drift diagnostic
            disk_path = target_root / tf
            if disk_path.exists():
                disk_bytes = disk_path.read_bytes()
                disk_hash = hashlib.sha256(disk_bytes).hexdigest()
                if disk_hash not in (canon_h, crlf_h):
                    worktree_drift_warnings.append(f"{tid}: Working tree drift on disk for {tf} (disk={disk_hash})")
            else:
                worktree_drift_warnings.append(f"{tid}: File {tf} missing in working tree on disk")

        except (CommitNotFoundError, FileNotFoundAtCommitError, PathSecurityError) as ex:
            errors.append({
                "task_id": tid,
                "error_class": type(ex).__name__,
                "file": tf,
                "message": f"{tid}: Target file error for {tf}: {ex}",
            })

        # Verify expected files and content hashes
        exp_files = task.get("expected_files", [])
        hash_map = task.get("file_content_hashes", {})
        for ef in exp_files:
            expected_hash = hash_map.get(ef)
            try:
                ef_blob = read_repo_file_at_commit(target_root, comm, ef)
                if expected_hash:
                    is_match_ef, mode_ef, ef_canon_h, ef_crlf_h = verify_content_hash(ef_blob, expected_hash)
                    if not is_match_ef:
                        errors.append({
                            "task_id": tid,
                            "error_class": "HASH_MISMATCH",
                            "file": ef,
                            "recorded_hash": expected_hash,
                            "canonical_hash": ef_canon_h,
                            "crlf_hash": ef_crlf_h,
                            "message": f"{tid}: Content hash mismatch for expected file {ef}",
                        })
            except (CommitNotFoundError, FileNotFoundAtCommitError, PathSecurityError) as ex:
                errors.append({
                    "task_id": tid,
                    "error_class": type(ex).__name__,
                    "file": ef,
                    "message": f"{tid}: Expected file error for {ef}: {ex}",
                })

        audited_tasks.append({
            "task_id": tid,
            "commit": comm,
            "target_file": tf,
            "target_symbol": sym,
            "status": "VALID" if not any(e.get("task_id") == tid for e in errors) else "INVALID",
        })

    # 2. Verify Edge Ground Truth
    if edge_gt_path.exists():
        edge_data = json.loads(edge_gt_path.read_text(encoding="utf-8"))
        edges = edge_data.get("edges", [])
        edge_commit = edge_data.get("target_commit", target_commit)
        print(f"Auditing {len(edges)} edge ground truth tuples at commit {edge_commit}...")
        for eg in edges:
            sf = eg.get("source_file", "")
            rec_s_hash = eg.get("source_file_hash")
            edge_id = eg.get("edge_id")
            try:
                sf_blob = read_repo_file_at_commit(target_root, edge_commit, sf)
                if rec_s_hash:
                    is_match_s, _, sf_canon_h, sf_crlf_h = verify_content_hash(sf_blob, rec_s_hash)
                    if not is_match_s:
                        errors.append({
                            "edge_id": edge_id,
                            "error_class": "HASH_MISMATCH",
                            "file": sf,
                            "message": f"Edge {edge_id}: Source file {sf} hash mismatch",
                        })
            except (CommitNotFoundError, FileNotFoundAtCommitError, PathSecurityError) as ex:
                errors.append({
                    "edge_id": edge_id,
                    "error_class": type(ex).__name__,
                    "file": sf,
                    "message": f"Edge {edge_id}: Source file error for {sf}: {ex}",
                })

    # 3. Verify Receiver Ground Truth
    if receiver_gt_path.exists():
        rec_data = json.loads(receiver_gt_path.read_text(encoding="utf-8"))
        call_sites = rec_data.get("call_sites", [])
        rec_commit = rec_data.get("target_commit", target_commit)
        print(f"Auditing {len(call_sites)} receiver ground truth call sites at commit {rec_commit}...")
        for cs in call_sites:
            f = cs.get("file", "")
            call_id = cs.get("call_id")
            line_no = cs.get("line", 0)
            called_meth = cs.get("called_method", "")
            recv_expr = cs.get("receiver_expression", "")
            rec_hash = cs.get("source_content_hash", "")
            fingerprint = cs.get("source_fingerprint", "")
            try:
                cs_blob = read_repo_file_at_commit(target_root, rec_commit, f)
                if rec_hash:
                    is_match_cs, _, cs_canon_h, cs_crlf_h = verify_content_hash(cs_blob, rec_hash)
                    if not is_match_cs:
                        errors.append({
                            "call_id": call_id,
                            "error_class": "HASH_MISMATCH",
                            "file": f,
                            "message": f"CallSite {call_id}: Source file hash mismatch for {f}",
                        })

                lines = cs_blob.decode("utf-8", errors="replace").splitlines()
                if line_no < 1 or line_no > len(lines):
                    errors.append({
                        "call_id": call_id,
                        "error_class": "CALLSITE_LINE_OUT_OF_BOUNDS",
                        "file": f,
                        "line": line_no,
                        "total_lines": len(lines),
                        "message": f"CallSite {call_id}: Line {line_no} out of bounds (1..{len(lines)}) in {f}",
                    })
                else:
                    line_txt = lines[line_no - 1]
                    if called_meth not in line_txt or recv_expr not in line_txt:
                        errors.append({
                            "call_id": call_id,
                            "error_class": "CALLSITE_CALL_MISMATCH",
                            "file": f,
                            "line": line_no,
                            "message": f"CallSite {call_id}: Call mismatch at line {line_no}: {line_txt}",
                        })
            except (CommitNotFoundError, FileNotFoundAtCommitError, PathSecurityError) as ex:
                errors.append({
                    "call_id": call_id,
                    "error_class": type(ex).__name__,
                    "file": f,
                    "message": f"CallSite {call_id}: File error for {f}: {ex}",
                })

    # 4. Verify Canonicalization Ground Truth
    if canon_gt_path.exists():
        canon_data = json.loads(canon_gt_path.read_text(encoding="utf-8"))
        records = canon_data.get("records", [])
        canon_commit = canon_data.get("target_commit", target_commit)
        print(f"Auditing {len(records)} canonicalization corpus records at commit {canon_commit}...")
        for rec in records:
            cf = rec.get("context_file", "")
            if not cf:
                continue
            try:
                read_repo_file_at_commit(target_root, canon_commit, cf)
            except (CommitNotFoundError, FileNotFoundAtCommitError, PathSecurityError) as ex:
                errors.append({
                    "category": rec.get("category"),
                    "error_class": type(ex).__name__,
                    "file": cf,
                    "message": f"Canonicalization record error for {cf}: {ex}",
                })

    # Build result payload
    provenance_status = "PASSED" if not errors else "FAILED"
    env.derive_run_id()
    from provenance import build_provenance_envelope
    envelope = build_provenance_envelope(env)
    result_payload = {
        **envelope,
        "provenance_status": provenance_status,
        "target_commit": target_commit,
        "audited_commits": list(audited_commits),
        "total_tasks_audited": len(audited_tasks),
        "total_errors": len(errors),
        "errors": [e.get("message", str(e)) for e in errors],
        "error_details": errors,
        "worktree_drift_warnings": worktree_drift_warnings,
        "tasks": audited_tasks,
    }

    # Decide output file path
    target_out_file = None
    if output_path:
        target_out_file = Path(output_path).resolve()
    elif write_results or os.environ.get("RCIR_RUN_DIR"):
        target_out_file = env.results_root / "ground_truth_provenance.json"

    if target_out_file:
        target_out_file.parent.mkdir(parents=True, exist_ok=True)
        temp_out = target_out_file.with_suffix(".tmp")
        temp_out.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
        temp_out.replace(target_out_file)
        print(f"Ground truth provenance result written to {target_out_file}")
    else:
        print("Side-effect free execution: results not written to tracked results/ directory.")

    if errors:
        print(f"FAILED: Found {len(errors)} provenance errors:")
        for e in errors[:10]:
            print(f"  - {e.get('message', str(e))}")
        raise BenchmarkIntegrityError(f"Ground truth provenance failed with {len(errors)} errors.")
    else:
        print(f"SUCCESS: All {len(audited_tasks)} tasks, commits, files, and hashes 100% verified!")
        if worktree_drift_warnings:
            print(f"  (Note: {len(worktree_drift_warnings)} working-tree drift warnings logged)")

    return result_payload


def main():
    parser = argparse.ArgumentParser(description="Audit RCIR Ground-Truth Provenance against Git object store")
    parser.add_argument("--output", "-o", help="Explicit path to write output JSON report", default=None)
    parser.add_argument("--write-results", action="store_true", help="Write to env.results_root / ground_truth_provenance.json")
    args = parser.parse_args()

    audit_provenance(output_path=args.output, write_results=args.write_results)


if __name__ == "__main__":
    main()
