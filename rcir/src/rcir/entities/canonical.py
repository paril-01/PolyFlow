"""
RCIR v8.3 — Canonical Entity Identity & Alias Registry (PHASES 4, 5, 6, 7, 8).

Implements a language-independent canonical identity layer:
- Structured EntityID with repository, language, file, namespace, owner_type, symbol, kind, signature, source_span
- Standardized URI format (e.g. php://OCP\\Files\\Node::getId, ts://apps/files/src/services/Recent::getRecentSearch)
- CanonicalEntityRegistry with AliasIndex for exact, unique_alias, ambiguous, and unresolved resolution
- Disambiguation hint separation (file hint is NOT an entity itself)
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EntityKind(str, Enum):
    CLASS = "class"
    INTERFACE = "interface"
    TRAIT = "trait"
    METHOD = "method"
    FUNCTION = "function"
    PROPERTY = "property"
    CONSTANT = "constant"
    ROUTE = "route"
    EVENT = "event"
    CONFIG = "config"
    MODULE = "module"
    FILE = "file"


class AliasResolution(str, Enum):
    EXACT = "exact"
    UNIQUE_ALIAS = "unique_alias"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


@dataclass
class SourceSpan:
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_col": self.start_col,
            "end_col": self.end_col,
        }


@dataclass
class CanonicalEntityID:
    """Standardized, language-independent canonical identity."""
    repository: str
    language: str
    file: str
    namespace: str
    owner_type: str
    symbol: str
    kind: EntityKind
    signature: str = ""
    source_span: Optional[SourceSpan] = None
    aliases: list[str] = field(default_factory=list)

    @property
    def uri(self) -> str:
        """Standardized canonical URI string representation."""
        # e.g. php://OCP\Files\Node::getId or ts://apps/files/Recent::getRecentSearch
        ns_prefix = f"{self.namespace}\\" if self.namespace and not self.namespace.endswith("\\") else self.namespace
        if self.language == "php":
            if self.owner_type and self.symbol:
                return f"php://{ns_prefix}{self.owner_type}::{self.symbol}"
            elif self.owner_type:
                return f"php://{ns_prefix}{self.owner_type}"
            else:
                return f"php://{ns_prefix}{self.symbol}"
        elif self.language in ("ts", "js"):
            owner = f"{self.owner_type}::" if self.owner_type else ""
            return f"{self.language}://{self.file}::{owner}{self.symbol}"
        elif self.language == "python":
            mod = self.file.replace("/", ".").replace(".py", "")
            owner = f":{self.owner_type}." if self.owner_type else ":"
            return f"python://{mod}{owner}{self.symbol}"
        else:
            owner = f"::{self.owner_type}" if self.owner_type else ""
            return f"{self.language}://{self.file}{owner}::{self.symbol}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "repository": self.repository,
            "language": self.language,
            "file": self.file,
            "namespace": self.namespace,
            "owner_type": self.owner_type,
            "symbol": self.symbol,
            "kind": self.kind.value if isinstance(self.kind, EntityKind) else str(self.kind),
            "signature": self.signature,
            "source_span": self.source_span.to_dict() if self.source_span else None,
            "aliases": list(self.aliases),
        }


@dataclass
class ResolutionResult:
    """Result of an alias or symbol resolution."""
    canonical_id: Optional[str]
    resolution: AliasResolution
    evidence: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "resolution": self.resolution.value,
            "evidence": list(self.evidence),
            "alternatives": list(self.alternatives),
        }


class CanonicalEntityRegistry:
    """Registry maintaining all canonical entities and multi-form lookup index."""

    def __init__(self, repository_name: str = "nextcloud-server"):
        self.repository_name = repository_name
        self.entities: dict[str, CanonicalEntityID] = {}
        # alias -> set of canonical URIs
        self.alias_to_uris: dict[str, set[str]] = {}
        # file_path -> set of canonical URIs
        self.file_to_uris: dict[str, set[str]] = {}
        self.tail_to_uris: dict[str, set[str]] = {}
        self.uri_to_aliases: dict[str, set[str]] = {}
        self._cache: dict[tuple[str, str | None], ResolutionResult] = {}

    def register(self, entity: CanonicalEntityID) -> str:
        """Register an entity and index all its natural and specified aliases."""
        uri = entity.uri
        self.entities[uri] = entity
        self._cache.clear()

        norm_file = entity.file.replace("\\", "/").strip("/")
        self.file_to_uris.setdefault(norm_file, set()).add(uri)

        # Generate standard aliases
        aliases = set(entity.aliases)
        aliases.add(uri)
        if entity.symbol:
            aliases.add(entity.symbol)
            self.tail_to_uris.setdefault(entity.symbol, set()).add(uri)
            self.tail_to_uris.setdefault(f"::{entity.symbol}", set()).add(uri)
            self.tail_to_uris.setdefault(f"\\{entity.symbol}", set()).add(uri)
            if entity.namespace:
                aliases.add(f"{entity.namespace}\\{entity.symbol}")
        if entity.owner_type and entity.symbol:
            aliases.add(f"{entity.owner_type}::{entity.symbol}")
            if entity.namespace:
                aliases.add(f"{entity.namespace}\\{entity.owner_type}::{entity.symbol}")
        if entity.owner_type:
            aliases.add(entity.owner_type)
            if entity.namespace:
                aliases.add(f"{entity.namespace}\\{entity.owner_type}")

        # File-qualified aliases
        if norm_file:
            aliases.add(norm_file)
            if entity.symbol:
                aliases.add(f"{norm_file}::{entity.symbol}")
            if entity.owner_type and entity.symbol:
                aliases.add(f"{norm_file}::{entity.owner_type}::{entity.symbol}")
            elif entity.owner_type:
                aliases.add(f"{norm_file}::{entity.owner_type}")

        alias_set = self.uri_to_aliases.setdefault(uri, set())
        for alias in aliases:
            self.alias_to_uris.setdefault(alias, set()).add(uri)
            self.alias_to_uris.setdefault(alias.lower(), set()).add(uri)
            alias_set.add(alias)
            alias_set.add(alias.lower())
            # Also normalize forward/backward slashes
            alt_slash = alias.replace("/", "\\") if "/" in alias else alias.replace("\\", "/")
            self.alias_to_uris.setdefault(alt_slash, set()).add(uri)
            self.alias_to_uris.setdefault(alt_slash.lower(), set()).add(uri)
            alias_set.add(alt_slash)
            alias_set.add(alt_slash.lower())

        return uri

    def get_aliases_for_uri(self, uri: str) -> set[str]:
        """Return all recorded aliases for a given canonical URI."""
        return self.uri_to_aliases.get(uri, set())

    def resolve(
        self,
        symbol_or_alias: str,
        target_file_hint: str | None = None,
    ) -> ResolutionResult:
        """Resolve a requested symbol or alias with optional file disambiguation hint."""
        if not symbol_or_alias:
            return ResolutionResult(canonical_id=None, resolution=AliasResolution.UNRESOLVED)

        cache_key = (symbol_or_alias, target_file_hint)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Direct canonical URI match
        if symbol_or_alias in self.entities:
            res = ResolutionResult(
                canonical_id=symbol_or_alias,
                resolution=AliasResolution.EXACT,
                evidence=["direct_uri_match"],
            )
            self._cache[cache_key] = res
            return res

        sym_norm = re.sub(r'\\+', r'\\', symbol_or_alias.strip())
        matches = (
            self.alias_to_uris.get(symbol_or_alias)
            or self.alias_to_uris.get(sym_norm)
            or self.alias_to_uris.get(sym_norm.replace("\\", "/"))
            or self.alias_to_uris.get(sym_norm.replace("/", "\\"))
            or self.alias_to_uris.get(symbol_or_alias.lower())
            or self.alias_to_uris.get(sym_norm.lower())
        )

        if not matches:
            matches = self.tail_to_uris.get(symbol_or_alias) or self.tail_to_uris.get(sym_norm)

        if not matches:
            res = ResolutionResult(
                canonical_id=None,
                resolution=AliasResolution.UNRESOLVED,
                evidence=["no_alias_registered"],
            )
            self._cache[cache_key] = res
            return res

        # If file hint provided, disambiguate candidates
        if target_file_hint and len(matches) > 1:
            norm_hint = target_file_hint.replace("\\", "/").strip("/")
            file_filtered = {
                uri for uri in matches
                if self.entities[uri].file.replace("\\", "/").strip("/") == norm_hint
            }
            if file_filtered:
                matches = file_filtered

        if len(matches) == 1:
            chosen = next(iter(matches))
            ent = self.entities[chosen]
            # Exact if symbol and owner match or unique alias
            is_exact = (symbol_or_alias == ent.uri or symbol_or_alias == f"{ent.owner_type}::{ent.symbol}")
            res_type = AliasResolution.EXACT if is_exact else AliasResolution.UNIQUE_ALIAS
            res = ResolutionResult(
                canonical_id=chosen,
                resolution=res_type,
                evidence=[f"matched_{len(matches)}_alias_entries"],
            )
            self._cache[cache_key] = res
            return res

        # Multiple conflicting candidates
        res = ResolutionResult(
            canonical_id=None,
            resolution=AliasResolution.AMBIGUOUS,
            evidence=["multiple_candidates_found"],
            alternatives=sorted(list(matches)),
        )
        self._cache[cache_key] = res
        return res

    def get_entities_in_file(self, file_path: str) -> list[CanonicalEntityID]:
        norm = file_path.replace("\\", "/").strip("/")
        uris = self.file_to_uris.get(norm, set())
        return [self.entities[u] for u in uris]
