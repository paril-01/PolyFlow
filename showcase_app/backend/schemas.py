"""
showcase_app/backend/schemas.py — Typed Pydantic models for PolyFlow Backend API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "PolyFlow Evidence & Showcase Server"
    version: str = "1.0.0"
    evidence_status: str = "VALIDATED"
    timestamp: str


class RunSummaryResponse(BaseModel):
    run_id: str
    timestamp: str
    benchmark_type: str
    model: str
    total_trials: int
    valid_pairs: int
    successful_pairs: int
    median_input_token_delta_pct: float
    crash_rate_pct: float
    agent_gate_status: str


class FeatureSummary(BaseModel):
    feature_id: str
    feature_name: str
    domain: str
    native_files_count: int
    poly_file: str
    coverage_ratio: float


class NativeVsPolyResponse(BaseModel):
    feature_id: str
    feature_name: str
    domain: str
    poly_file: str
    poly_content: str
    layers: Dict[str, Any]
    reduction_ratio: str
    evidence_status: str


class InterpreterRunRequest(BaseModel):
    mode: str = Field("normal", description="'normal' or 'failure'")
    feature_id: str = "ERPNEXT-ACCOUNTS-SALES_INVOICE"


class InterpreterCellEvent(BaseModel):
    cell_id: str
    language: str
    event: str
    status: str
    duration_ms: float
    timestamp: str
    output: Optional[Dict[str, Any]] = None


class InterpreterRunResponse(BaseModel):
    run_id: str
    mode: str
    execution_status: str
    latency_ms: float
    cells_executed: int
    cells_failed: int
    cells_fallback: int
    receipt_id: str
    receipt_hash: str
    timeline: List[InterpreterCellEvent]


class ProofItem(BaseModel):
    proof_id: str
    title: str
    run_id: str
    rel_path: str
    source_file: str
    sha256: str
    bytes: int
    mime_type: str
    origin_kind: str
    measurement_method: str
    validity_status: str
    timestamp: str
    safe_url: str


class ProofIndexResponse(BaseModel):
    run_id: str
    total_proofs: int
    proofs: List[ProofItem]


class RCIRQueryRequest(BaseModel):
    query_text: str = "Find accounting ledger entry calculation in ERPNext"
    target_domain: Optional[str] = "accounts"
    token_budget: Optional[int] = 4000


class RCIRCandidate(BaseModel):
    rank: int
    path: str
    score: float
    tier: int
    reason: str


class RCIRQueryResponse(BaseModel):
    query_id: str
    query_text: str
    repo_file_count: int
    retrieved_count: int
    compiled_tokens: int
    candidates: List[RCIRCandidate]


class ERPNextTreeResponse(BaseModel):
    total_doctypes: int
    total_features: int
    total_loc: int
    domains: Dict[str, Any]
    parity_tiers: Dict[str, Any]
