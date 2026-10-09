"""
experiments/benchmark_core/task_loader.py — Public Task Manifest Loader.

Exposes only public task specifications to the agent:
- task_id
- title
- instructions
- domain / tier

Strictly withholds the private oracle (hidden files, gold diffs, evaluator scripts).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_public_tasks(task_manifest_path: Path) -> List[Dict[str, Any]]:
    """Loads and sanitizes tasks for the agent prompt, stripping any private oracle fields."""
    if not task_manifest_path.exists():
        raise FileNotFoundError(f"Task manifest not found: {task_manifest_path}")

    raw_data = json.loads(task_manifest_path.read_text(encoding="utf-8"))
    tasks_list = raw_data.get("tasks", []) if isinstance(raw_data, dict) else raw_data

    sanitized = []
    for t in tasks_list:
        sanitized.append({
            "task_id": t["task_id"],
            "title": t["title"],
            "instructions": t["instructions"],
            "tier": t.get("tier", "Core Server"),
            "domain": t.get("domain", "nextcloud"),
            "turn_budget": t.get("turn_budget", 12),
        })

    return sanitized
