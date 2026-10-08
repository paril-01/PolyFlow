"""
showcase_app/backend/services/feature_service.py — Feature Mapping Service.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class FeatureService:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.mapping_file = self.repo_root / "showcase" / "data" / "polyflow_mapping.json"
        self.closure_file = self.repo_root / "experiments" / "erpnext_validation" / "feature_closure_validation.json"

    def get_features(self) -> List[Dict[str, Any]]:
        features = []
        if self.closure_file.exists():
            data = json.loads(self.closure_file.read_text(encoding="utf-8"))
            for rf in data.get("representative_features", []):
                features.append({
                    "feature_id": rf.get("feature_id", ""),
                    "feature_name": rf.get("feature", ""),
                    "domain": rf.get("domain", ""),
                    "native_files_count": rf.get("extracted_sources_count", 0),
                    "poly_file": rf.get("stack_manifest", {}).get("poly_file", ""),
                    "coverage_ratio": rf.get("layer_coverage", {}).get("overall", 1.0),
                })
        return features

    def get_feature_detail(self, feature_id: str) -> Optional[Dict[str, Any]]:
        for f in self.get_features():
            if f["feature_id"] == feature_id:
                return f
        return None

    def get_native_vs_poly(self, feature_id: str) -> Optional[Dict[str, Any]]:
        if not self.mapping_file.exists():
            return None
        data = json.loads(self.mapping_file.read_text(encoding="utf-8"))
        selected = data.get("selected_feature", {})
        if selected.get("feature_id") == feature_id or "SALES_INVOICE" in feature_id:
            return selected
        features = data.get("features", {})
        return features.get(feature_id)


feature_service = FeatureService()
