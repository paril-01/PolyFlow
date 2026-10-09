"""
showcase_app/backend/api/proofs.py — Proofs, Benchmarks, and CSV Artifact Endpoints.

Enforces Rule 0: Allow-listed proof registry, SHA-256 integrity, path-traversal guards.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from showcase_app.backend.services.evidence_registry import evidence_registry
from showcase_app.backend.services.benchmark_service import benchmark_service

router = APIRouter()


@router.get("/runs")
def list_runs():
    return benchmark_service.get_runs()


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    summary = benchmark_service.get_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")
    return summary


@router.get("/runs/{run_id}/metrics")
def get_run_metrics(run_id: str):
    summary = benchmark_service.get_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run_id,
        "valid_pairs": summary.get("valid_pairs"),
        "successful_pairs": summary.get("successful_pairs"),
        "median_input_token_delta_pct": summary.get("median_input_token_delta_pct"),
        "agent_gate_status": summary.get("agent_gate_status"),
        "crash_rate_pct": summary.get("crash_rate_pct"),
    }


@router.get("/runs/{run_id}/status")
def get_run_status(run_id: str):
    summary = benchmark_service.get_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")
    return summary


@router.get("/runs/{run_id}/pairs.csv")
def get_run_pairs_csv(run_id: str):
    csv_text = benchmark_service.get_csv_content("paired_token_usage.csv", run_id=run_id)
    if csv_text is None:
        raise HTTPException(status_code=404, detail="paired_token_usage.csv not found")
    return Response(content=csv_text, media_type="text/csv")


@router.get("/runs/{run_id}/retrieval.csv")
def get_run_retrieval_csv(run_id: str):
    csv_text = benchmark_service.get_csv_content("retrieved_files.csv", run_id=run_id)
    if csv_text is None:
        raise HTTPException(status_code=404, detail="retrieved_files.csv not found")
    return Response(content=csv_text, media_type="text/csv")


@router.get("/runs/{run_id}/trials.csv")
def get_run_trials_csv(run_id: str):
    csv_text = benchmark_service.get_csv_content("agent_trials.csv", run_id=run_id)
    if csv_text is None:
        raise HTTPException(status_code=404, detail="agent_trials.csv not found")
    return Response(content=csv_text, media_type="text/csv")


@router.get("/runs/{run_id}/proofs")
def get_run_proofs(run_id: str):
    summary = benchmark_service.get_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")
    proofs = evidence_registry.get_all_proofs()
    return {
        "run_id": run_id,
        "total_proofs": len(proofs),
        "proofs": proofs,
    }


@router.get("/benchmarks/{run_id}/summary")
def get_benchmark_summary(run_id: str):
    summary = benchmark_service.get_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    return summary


@router.get("/benchmarks/{run_id}/pairs.csv")
def get_benchmark_pairs_csv(run_id: str):
    csv_text = benchmark_service.get_csv_content("paired_token_usage.csv")
    if csv_text is None:
        raise HTTPException(status_code=404, detail="paired_token_usage.csv not found")
    return Response(content=csv_text, media_type="text/csv")


@router.get("/benchmarks/{run_id}/ranked-files.csv")
def get_benchmark_ranked_files_csv(run_id: str):
    csv_text = benchmark_service.get_csv_content("retrieved_files.csv")
    if csv_text is None:
        raise HTTPException(status_code=404, detail="retrieved_files.csv not found")
    return Response(content=csv_text, media_type="text/csv")


@router.get("/proofs")
def list_proofs():
    proofs = evidence_registry.get_all_proofs()
    return {
        "run_id": evidence_registry.run_id,
        "total_proofs": len(proofs),
        "proofs": proofs,
    }


@router.get("/proofs/{proof_id}")
def get_proof_content(proof_id: str):
    resolved = evidence_registry.resolve_proof_file(proof_id)
    if not resolved:
        raise HTTPException(status_code=404, detail="Proof not found or integrity check failed")
    
    file_path, proof_meta = resolved
    mime = proof_meta.get("mime_type", "text/plain")
    return FileResponse(path=str(file_path), media_type=mime)


@router.get("/proofs/{proof_id}/download")
def download_proof(proof_id: str):
    resolved = evidence_registry.resolve_proof_file(proof_id)
    if not resolved:
        raise HTTPException(status_code=404, detail="Proof not found or integrity check failed")

    file_path, proof_meta = resolved
    return FileResponse(
        path=str(file_path),
        media_type=proof_meta.get("mime_type", "application/octet-stream"),
        filename=file_path.name,
    )
