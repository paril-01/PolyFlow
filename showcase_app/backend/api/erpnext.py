"""
showcase_app/backend/api/erpnext.py — ERPNext Enterprise Scale & Coverage Endpoints.
"""

from fastapi import APIRouter, HTTPException, Response
from showcase_app.backend.services.erpnext_service import erpnext_service
from showcase_app.backend.services.feature_service import feature_service

router = APIRouter()


@router.get("/erpnext/tree")
def get_erpnext_tree():
    return erpnext_service.get_tree()


@router.get("/erpnext/features/{feature_id}")
def get_erpnext_feature(feature_id: str):
    feat = feature_service.get_feature_detail(feature_id)
    if not feat:
        raise HTTPException(status_code=404, detail="ERPNext feature not found")
    return feat


@router.get("/erpnext/coverage.csv")
def get_coverage_csv():
    csv_text = erpnext_service.get_coverage_csv()
    if not csv_text:
        raise HTTPException(status_code=404, detail="Coverage ledger CSV not found")
    return Response(content=csv_text, media_type="text/csv")
