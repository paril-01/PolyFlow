"""
RCIR v8.1 — Nextcloud Repository Adapter (PHASE 15 & 16).

Encapsulates repository-specific conventions for Nextcloud:
- Module resolution: `apps/<app_name>` -> `apps/<app_name>`, `lib/*` -> `core`
- Boundary contracts: `routes.php`, frontend client services (`Recent.ts`, etc.)
- Test file mapping conventions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rcir.entities.module import ModuleResolver


class NextcloudModuleResolver(ModuleResolver):
    """Nextcloud-specific module resolver honoring apps/ and lib/ structures."""

    def get_module(self, path_or_entity: str) -> str:
        clean = path_or_entity.split("::")[0].replace("\\", "/").strip("/")

        if "apps/" in clean:
            parts = clean.split("apps/")[1].split("/")
            if parts and parts[0]:
                return f"apps/{parts[0]}"
        elif clean.startswith("lib/") or "/lib/" in clean:
            return "core"
        elif clean.startswith("core/"):
            return "core"
        elif clean.startswith("tests/"):
            return "tests"

        return super().get_module(clean)

    def compute_module_distance(self, path1: str, path2: str) -> int:
        m1 = self.get_module(path1)
        m2 = self.get_module(path2)
        if m1 == m2:
            return 0
        if "apps/" in m1 and "apps/" in m2:
            return 1
        return 2


def is_nextcloud_boundary_match(source_or_target: str, query_symbol: str) -> bool:
    """Nextcloud-specific check for frontend-to-backend boundary wiring."""
    s = source_or_target.lower()
    q = query_symbol.lower()
    if "recent.ts" in q or "recent" in q:
        return "recent" in s
    return False
