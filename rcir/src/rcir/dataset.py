"""
RCIR v8.3 — Dataset Loader & Split Enforcer (PHASES 36, 37, 38, 39, 40).

Enforces strict separation between DEV, VALIDATION, and TEST sets:
- DEV: Feature development, ranker weight tuning, operation profile tuning
- VALIDATION: Ranker configuration selection, context planner selection
- TEST: Frozen formal evaluation executed once; inaccessible during ranker selection
- Automated leakage guard: Raises PermissionError if TEST split is requested in DEV/SELECTION modes
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from rcir.query.change_spec import ChangeOperation, ChangeSpecification, RequestedScope


class DatasetSplit(str, Enum):
    DEV = "dev"
    VALIDATION = "validation"
    TEST = "test"


class DatasetMode(str, Enum):
    DEVELOPMENT = "development"
    RANKER_SELECTION = "ranker_selection"
    FORMAL_TEST = "formal_test"


@dataclass
class BenchmarkTask:
    task_id: str
    title: str
    category: str
    spec: ChangeSpecification
    query: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "category": self.category,
            "spec": self.spec.to_dict(),
            "query": self.query,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkTask:
        spec_data = data.get("spec", {})
        if not spec_data:
            # Build spec from legacy task fields
            op_map = {
                "controller_route": ChangeOperation.ROUTE_CHANGE,
                "interface_method": ChangeOperation.SIGNATURE_CHANGE,
                "event_contract": ChangeOperation.EVENT_CHANGE,
                "dependency_injection": ChangeOperation.CONFIG_CHANGE,
                "cross_stack": ChangeOperation.ROUTE_CHANGE,
            }
            cat = data.get("category", "interface_method")
            spec = ChangeSpecification(
                operation=op_map.get(cat, ChangeOperation.BEHAVIOR_CHANGE),
                requested_symbol=data.get("target_symbol", ""),
                target_file_hint=data.get("target_file", ""),
                description=data.get("description", ""),
            )
        else:
            spec = ChangeSpecification.from_dict(spec_data)

        return cls(
            task_id=data["task_id"],
            title=data.get("title", ""),
            category=data.get("category", "interface_method"),
            spec=spec,
            query=data.get("query", ""),
            description=data.get("description", ""),
        )


class DatasetLoader:
    """Manages loading of partitioned benchmark tasks with strict leakage barriers."""

    def __init__(
        self,
        datasets_dir: Path | str,
        mode: DatasetMode = DatasetMode.DEVELOPMENT,
    ):
        self.datasets_dir = Path(datasets_dir)
        self.mode = mode

    def load_split(self, split: DatasetSplit) -> list[BenchmarkTask]:
        """Load tasks for a specific split; guards against TEST set access in dev/selection."""
        if split == DatasetSplit.TEST and self.mode in (DatasetMode.DEVELOPMENT, DatasetMode.RANKER_SELECTION):
            raise PermissionError(
                f"[LEAKAGE GUARD] Access to TEST split is prohibited during {self.mode.value} phase!"
            )

        split_file = self.datasets_dir / f"{split.value}.json"
        if not split_file.exists():
            raise FileNotFoundError(f"Dataset split file not found: {split_file}")

        with open(split_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tasks_raw = data.get("tasks", [])
        return [BenchmarkTask.from_dict(t) for t in tasks_raw]
