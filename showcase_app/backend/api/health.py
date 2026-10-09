"""
showcase_app/backend/api/health.py — Health and System Status Endpoint.
"""

import time
from fastapi import APIRouter
from showcase_app.backend.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        service="PolyFlow Evidence & Showcase Server",
        version="1.0.0",
        process_liveness="UP",
        evidence_status="VALIDATED",
        benchmarks_gate="NOT_EVALUATED_BY_HEALTH",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
