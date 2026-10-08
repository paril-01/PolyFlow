"""
showcase_app/backend/api/rcir.py — RCIR Context Retrieval & Pipeline Endpoints.
"""

from typing import Any, Dict
from fastapi import APIRouter
from showcase_app.backend.schemas import RCIRQueryRequest, RCIRQueryResponse
from showcase_app.backend.services.rcir_service import rcir_service

router = APIRouter()

QUERY_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/rcir/pipeline")
def get_rcir_pipeline():
    return rcir_service.get_pipeline_data()


@router.post("/rcir/queries", response_model=RCIRQueryResponse)
def run_rcir_query(req: RCIRQueryRequest):
    res = rcir_service.query(
        query_text=req.query_text,
        target_domain=req.target_domain or "accounts",
        token_budget=req.token_budget or 4000,
    )
    QUERY_CACHE[res["query_id"]] = res
    return res


@router.get("/rcir/queries/{query_id}", response_model=RCIRQueryResponse)
def get_rcir_query(query_id: str):
    if query_id in QUERY_CACHE:
        return QUERY_CACHE[query_id]
    # Default query response
    return rcir_service.query("Default accounting ledger query")
