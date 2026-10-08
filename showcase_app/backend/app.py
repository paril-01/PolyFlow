"""
showcase_app/backend/app.py — PolyFlow Evidence-First Backend Server.

FastAPI application delivering:
1. /api/health
2. /api/runs, /api/runs/{run_id}/status
3. /api/features, /api/features/{feature_id}, /api/features/{feature_id}/native-vs-poly
4. /api/interpreter/runs (POST), /api/interpreter/runs/{run_id}, /api/interpreter/runs/{run_id}/events (SSE)
5. /api/rcir/queries (POST), /api/rcir/queries/{query_id}, /api/rcir/pipeline
6. /api/benchmarks/{run_id}/summary, /api/benchmarks/{run_id}/pairs.csv, /api/benchmarks/{run_id}/ranked-files.csv
7. /api/proofs, /api/proofs/{proof_id}, /api/proofs/{proof_id}/download
8. /api/erpnext/tree, /api/erpnext/features/{feature_id}, /api/erpnext/coverage.csv
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from showcase_app.backend.api.health import router as health_router
from showcase_app.backend.api.features import router as features_router
from showcase_app.backend.api.interpreter import router as interpreter_router
from showcase_app.backend.api.rcir import router as rcir_router
from showcase_app.backend.api.proofs import router as proofs_router
from showcase_app.backend.api.erpnext import router as erpnext_router

app = FastAPI(
    title="PolyFlow Evidence & Showcase API",
    description="Evidence-first REST and SSE backend for PolyFlow, RCIR, and ERPNext validation.",
    version="1.0.0",
)

# CORS configuration (Localhost only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(features_router, prefix="/api", tags=["Features"])
app.include_router(interpreter_router, prefix="/api", tags=["Interpreter"])
app.include_router(rcir_router, prefix="/api", tags=["RCIR"])
app.include_router(proofs_router, prefix="/api", tags=["Proofs"])
app.include_router(erpnext_router, prefix="/api", tags=["ERPNext"])

# Mount static frontend
frontend_dir = REPO_ROOT / "showcase_app" / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("showcase_app.backend.app:app", host="127.0.0.1", port=8000, reload=True)
