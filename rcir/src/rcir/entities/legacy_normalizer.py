"""
RCIR v8.5 — Legacy Endpoint Normalizer & Collision Prevention (PHASES 21, 22, 24).

Features:
- LegacyEndpointNormalizer: parses legacy, heterogeneous endpoints into canonical URIs
  (file.php, file.php::FQN::method, FQN::method, FQN, route identifiers, config keys).
- Strict "External Means External" enforcement (PHASE 22):
  Repo-local files, classes (OC\\, OCP\\, OCA\\), and methods CANNOT become external://.
- Collision Detection (PHASE 24):
  Methods like __construct without established owners become unresolved://, never php://__construct.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rcir.entities.canonical import (
    CanonicalEntityID,
    CanonicalEntityRegistry,
    EntityKind,
)


class LegacyEndpointNormalizer:
    """Normalizes raw graph and legacy endpoints into unambiguous canonical URIs."""

    EXTERNAL_NAMESPACES = (
        "Psr\\",
        "Symfony\\",
        "Doctrine\\",
        "GuzzleHttp\\",
        "Composer\\",
        "PHPUnit\\",
        "Pimple\\",
        "League\\",
        "Sabre\\",
        "Bifrost\\",
        "Laminas\\",
        "DateTime",
        "Exception",
        "Throwable",
        "stdClass",
        "PDO",
        "ArrayAccess",
        "Countable",
        "Iterator",
        "Traversable",
    )

    INTERNAL_NAMESPACES = (
        "OC\\",
        "OCP\\",
        "OCA\\",
        "OCP",
        "OCA",
        "OC",
    )

    def __init__(self, target_repo_root: Optional[Path] = None):
        self.target_repo_root = Path(target_repo_root).resolve() if target_repo_root else None
        self._internal_file_cache: set[str] = set()

    def set_repo_root(self, target_repo_root: Path):
        self.target_repo_root = Path(target_repo_root).resolve()
        self._internal_file_cache.clear()

    def is_repo_local_file(self, file_path: str) -> bool:
        """Check if file_path belongs to target repository."""
        clean = file_path.replace("\\", "/").lstrip("/")
        if clean in self._internal_file_cache:
            return True
        if self.target_repo_root and (self.target_repo_root / clean).exists():
            self._internal_file_cache.add(clean)
            return True
        # Check standard Nextcloud paths
        if clean.startswith(("apps/", "lib/", "core/", "settings/", "ocs/", "tests/")):
            return True
        return False

    def is_internal_symbol(self, symbol: str) -> bool:
        """Check if namespace/symbol belongs to Nextcloud internal codebase."""
        clean = symbol.replace("/", "\\").lstrip("\\")
        for ns in self.INTERNAL_NAMESPACES:
            if clean.startswith(ns):
                return True
        return False

    def is_external_symbol(self, symbol: str) -> bool:
        """Check if symbol belongs to known external libraries or PHP standard library."""
        clean = symbol.replace("/", "\\").lstrip("\\")
        for ns in self.EXTERNAL_NAMESPACES:
            if clean.startswith(ns):
                return True
        return False

    def normalize_endpoint(
        self,
        raw_endpoint: str,
        registry: Optional[CanonicalEntityRegistry] = None,
        context_file: str = "",
    ) -> str:
        """Normalize raw endpoint string into a canonical URI."""
        if not raw_endpoint:
            return "unresolved://empty"

        ep = raw_endpoint.strip()

        # Handle existing URI schemes
        if "://" in ep:
            parts = ep.split("://")
            scheme = parts[0]
            rest = parts[-1].lstrip("/")

            # PHASE 22: Repair incorrect external:// for repo-local endpoints
            if scheme == "external":
                if self.is_internal_symbol(rest) or self.is_repo_local_file(rest):
                    if rest in ("__construct", "getId", "getName", "run", "init", "setUp") or not rest:
                        return f"unresolved://{rest}"
                    return f"php://{rest}"
                else:
                    return f"external://{rest}"
            elif scheme == "php":
                # PHASE 24: Prevent collision like php://__construct
                if rest in ("__construct", "getId", "getName", "run", "init", "setUp") or not rest:
                    return f"unresolved://{rest}"
                return f"php://{rest}"
            elif scheme in ("unresolved", "ts", "js", "python"):
                return f"{scheme}://{rest}"
            else:
                return ep

        # 1. Format: file.ext::FQN::method or file.ext::FQN
        if "::" in ep and (ep.endswith((".php", ".ts", ".js")) or "/" in ep.split("::")[0]):
            parts = ep.split("::")
            file_p = parts[0].replace("\\", "/").strip("/")
            if len(parts) >= 3:
                owner_fqn = parts[1]
                method = parts[2]
                if method in ("__construct", "init") and not owner_fqn:
                    return f"unresolved://{ep}"
                owner_clean = owner_fqn.lstrip("\\")
                return f"php://{owner_clean}::{method}"
            elif len(parts) == 2:
                owner_fqn = parts[1].lstrip("\\")
                return f"php://{owner_fqn}"

        # 2. Format: Namespace\Class::method
        if "::" in ep:
            owner_part, method = ep.split("::", 1)
            owner_clean = owner_part.lstrip("\\")
            if not owner_clean:
                # Collision prevention (PHASE 24)
                return f"unresolved://{method}"
            if self.is_external_symbol(owner_clean):
                return f"external://{owner_clean}::{method}"
            return f"php://{owner_clean}::{method}"

        # 3. Format: File path
        if ep.endswith((".php", ".ts", ".js", ".json", ".vue")):
            norm_file = ep.replace("\\", "/").strip("/")
            lang = "ts" if norm_file.endswith(".ts") else "js" if norm_file.endswith(".js") else "php"
            return f"{lang}://{norm_file}"

        # 4. Format: FQN class or interface (e.g. OCP\IConfig or Psr\Log\LoggerInterface)
        if "\\" in ep:
            clean_fqn = ep.lstrip("\\")
            if self.is_external_symbol(clean_fqn):
                return f"external://{clean_fqn}"
            return f"php://{clean_fqn}"

        # 5. Format: Route identifier (e.g. route:apps/files/api or Api#getThumbnail)
        if "#" in ep or ep.startswith("route:"):
            return f"php://route/{ep}"

        # 6. Format: Single symbol (e.g. IConfig, ApiController)
        if registry:
            res = registry.resolve(ep, target_file_hint=context_file)
            if res.canonical_id:
                return res.canonical_id

        # 7. Check if external standard symbol
        if self.is_external_symbol(ep):
            return f"external://{ep}"

        # If it looks like an isolated method without class owner, avoid colliding php://method!
        if ep in ("__construct", "init", "run", "execute", "getId", "get", "set"):
            return f"unresolved://{ep}"

        # Default fallback
        if self.is_repo_local_file(ep):
            return f"php://{ep}"

        return f"unresolved://{ep}"
