"""
showcase_app/backend/api/features.py — Feature Mapping and Traceability Endpoints.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from showcase_app.backend.services.feature_service import feature_service

router = APIRouter()


@router.get("/features", response_model=List[Dict[str, Any]])
def list_features():
    return feature_service.get_features()


@router.get("/features/{feature_id}")
def get_feature(feature_id: str):
    feat = feature_service.get_feature_detail(feature_id)
    if not feat:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feat


@router.get("/features/{feature_id}/native-vs-poly")
def get_native_vs_poly(feature_id: str):
    data = feature_service.get_native_vs_poly(feature_id)
    if not data:
        raise HTTPException(status_code=404, detail="Native-vs-Poly mapping not found for feature")
    return data
