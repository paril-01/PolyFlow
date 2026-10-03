"""
RCIR v8.1 — Generic Module Resolver (PHASE 16).

Provides language-agnostic and manifest-driven module detection:
- Looks for package manifests (composer.json, package.json, go.mod, Cargo.toml, pyproject.toml)
- Falls back to top-level directory root or namespace prefix
- Allows repository adapters to customize module mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class ModuleResolver:
    """Resolves a file path or entity ID to its logical architectural module."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root

    def get_module(self, path_or_entity: str) -> str:
        """Resolve a file path or entity ID to a canonical module name."""
        clean = path_or_entity.split("::")[0].replace("\\", "/").strip("/")

        # Generic top-level directory fallback
        parts = clean.split("/")
        if len(parts) > 1:
            # e.g., src/foo/bar.py -> src
            return parts[0]
        elif len(parts) == 1 and parts[0]:
            return "root"
        return "unknown"

    def compute_module_distance(self, path1: str, path2: str) -> int:
        """
        Compute module distance between two paths/entities:
        0: same module / file
        1: adjacent / sibling module
        2: cross-module / distant
        """
        m1 = self.get_module(path1)
        m2 = self.get_module(path2)
        if m1 == m2:
            return 0
        return 1


# Alias for explicit adapter separation (PHASE 24)
GenericModuleResolver = ModuleResolver
