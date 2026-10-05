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
    ENUM = "enum"
    METHOD = "method"
    FUNCTION = "function"
    PROPERTY = "property"
    CONSTANT = "constant"
    ROUTE = "route"
    EVENT = "event"
    CONFIG = "config"
    MODULE = "module"
    FILE = "file"
    EXTERNAL = "external"
    UNRESOLVED = "unresolved"


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
        if self.kind == EntityKind.UNRESOLVED or self.language == "unresolved":
            return f"unresolved://{self.symbol}"
        if self.kind == EntityKind.EXTERNAL or self.language == "external":
            return f"external://{self.symbol}"

        ns_prefix = f"{self.namespace}\\" if self.namespace and not self.namespace.endswith("\\") else self.namespace
        if self.language == "php":
            if self.kind in (EntityKind.CLASS, EntityKind.INTERFACE, EntityKind.TRAIT, EntityKind.ENUM):
                type_name = self.owner_type or self.symbol
                return f"php://{ns_prefix}{type_name}"
            elif self.kind == EntityKind.METHOD:
                owner = self.owner_type or (self.file.split("/")[-1].split(".")[0] if self.file else "Unknown")
                return f"php://{ns_prefix}{owner}::{self.symbol}"
            elif self.kind == EntityKind.PROPERTY:
                owner = self.owner_type or (self.file.split("/")[-1].split(".")[0] if self.file else "Unknown")
                prop = self.symbol if self.symbol.startswith("$") else f"${self.symbol}"
                return f"php://{ns_prefix}{owner}::{prop}"
            elif self.kind == EntityKind.FUNCTION:
                return f"php://{ns_prefix}{self.symbol}()"
            elif self.kind == EntityKind.FILE:
                return f"php://{self.file}"
            else:
                if self.owner_type and self.symbol and self.owner_type != self.symbol:
                    return f"php://{ns_prefix}{self.owner_type}::{self.symbol}"
                else:
                    return f"php://{ns_prefix}{self.owner_type or self.symbol}"
        elif self.language in ("ts", "js"):
            if self.kind == EntityKind.FILE:
                return f"{self.language}://{self.file}"
            owner = f"{self.owner_type}::" if self.owner_type and self.owner_type != self.symbol else ""
            return f"{self.language}://{self.file}::{owner}{self.symbol}"
        elif self.language == "python":
            if self.kind == EntityKind.FILE:
                return f"python://{self.file}"
            mod = self.file.replace("/", ".").replace(".py", "")
            if self.kind in (EntityKind.CLASS, EntityKind.MODULE):
                return f"python://{mod}:{self.owner_type or self.symbol}"
            owner = f":{self.owner_type}." if self.owner_type else ":"
            return f"python://{mod}{owner}{self.symbol}"
        else:
            owner = f"::{self.owner_type}" if self.owner_type else ""
            return f"{self.language}://{self.file}{owner}::{self.symbol}"

    @classmethod
    def from_uri(cls, uri: str, repository: str = "nextcloud-server", file_hint: str = "") -> CanonicalEntityID:
        """Parse a canonical URI back into a structured CanonicalEntityID (PHASE 20)."""
        if "://" not in uri:
            raise ValueError(f"Invalid canonical URI format: {uri}")

        lang, rest = uri.split("://", 1)
        if lang in ("unresolved", "external"):
            kind = EntityKind.UNRESOLVED if lang == "unresolved" else EntityKind.EXTERNAL
            return cls(
                repository=repository,
                language=lang,
                file=file_hint,
                namespace="",
                owner_type="",
                symbol=rest,
                kind=kind,
            )

        if lang == "php":
            if "::" in rest:
                owner_part, sym_part = rest.split("::", 1)
                ns = owner_part.rsplit("\\", 1)[0] if "\\" in owner_part else ""
                owner = owner_part.rsplit("\\", 1)[-1]
                if sym_part.startswith("$"):
                    kind = EntityKind.PROPERTY
                elif sym_part.endswith("()"):
                    kind = EntityKind.METHOD
                    sym_part = sym_part[:-2]
                else:
                    kind = EntityKind.METHOD
                return cls(
                    repository=repository,
                    language=lang,
                    file=file_hint,
                    namespace=ns,
                    owner_type=owner,
                    symbol=sym_part,
                    kind=kind,
                )
            elif rest.endswith("()"):
                sym = rest[:-2]
                ns = sym.rsplit("\\", 1)[0] if "\\" in sym else ""
                sym_name = sym.rsplit("\\", 1)[-1]
                return cls(
                    repository=repository,
                    language=lang,
                    file=file_hint,
                    namespace=ns,
                    owner_type="",
                    symbol=sym_name,
                    kind=EntityKind.FUNCTION,
                )
            elif "/" in rest or rest.endswith(".php"):
                return cls(
                    repository=repository,
                    language=lang,
                    file=rest,
                    namespace="",
                    owner_type="",
                    symbol=rest.split("/")[-1].replace(".php", ""),
                    kind=EntityKind.FILE,
                )
            else:
                # Class / Interface
                ns = rest.rsplit("\\", 1)[0] if "\\" in rest else ""
                type_name = rest.rsplit("\\", 1)[-1]
                kind = EntityKind.INTERFACE if type_name.startswith("I") and len(type_name) > 2 and type_name[1].isupper() else EntityKind.CLASS
                return cls(
                    repository=repository,
                    language=lang,
                    file=file_hint,
                    namespace=ns,
                    owner_type=type_name,
                    symbol=type_name,
                    kind=kind,
                )
        elif lang in ("ts", "js"):
            parts = rest.split("::")
            file_p = parts[0]
            if len(parts) == 1:
                return cls(
                    repository=repository, language=lang, file=file_p,
                    namespace="", owner_type="", symbol=file_p.split("/")[-1], kind=EntityKind.FILE
                )
            elif len(parts) == 2:
                return cls(
                    repository=repository, language=lang, file=file_p,
                    namespace="", owner_type="", symbol=parts[1], kind=EntityKind.METHOD
                )
            else:
                return cls(
                    repository=repository, language=lang, file=file_p,
                    namespace="", owner_type=parts[1], symbol=parts[2], kind=EntityKind.METHOD
                )
        else:
            return cls(
                repository=repository, language=lang, file=file_hint or rest,
                namespace="", owner_type="", symbol=rest.split("::")[-1], kind=EntityKind.FILE
            )

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
        if norm_file:
            self.file_to_uris.setdefault(norm_file, set()).add(uri)

        # Generate standard aliases
        aliases = set(entity.aliases)
        aliases.add(uri)

        is_type = entity.kind in (EntityKind.CLASS, EntityKind.INTERFACE, EntityKind.TRAIT, EntityKind.ENUM)
        is_member = entity.kind in (EntityKind.METHOD, EntityKind.PROPERTY)

        if is_type:
            type_name = entity.owner_type or entity.symbol
            if type_name:
                aliases.add(type_name)
                if entity.namespace:
                    aliases.add(f"{entity.namespace}\\{type_name}")
            if norm_file and type_name:
                aliases.add(f"{norm_file}::{type_name}")
        elif is_member:
            if entity.symbol:
                aliases.add(entity.symbol)
                self.tail_to_uris.setdefault(entity.symbol, set()).add(uri)
            if entity.owner_type and entity.symbol:
                aliases.add(f"{entity.owner_type}::{entity.symbol}")
                if entity.namespace:
                    aliases.add(f"{entity.namespace}\\{entity.owner_type}::{entity.symbol}")
                if norm_file:
                    aliases.add(f"{norm_file}::{entity.owner_type}::{entity.symbol}")
            if norm_file and entity.symbol:
                aliases.add(f"{norm_file}::{entity.symbol}")
        elif entity.kind == EntityKind.FILE:
            if norm_file:
                aliases.add(norm_file)
        else:
            if entity.symbol:
                aliases.add(entity.symbol)
                self.tail_to_uris.setdefault(entity.symbol, set()).add(uri)
                if entity.namespace:
                    aliases.add(f"{entity.namespace}\\{entity.symbol}")

        for alias in aliases:
            if not alias:
                continue
            self.alias_to_uris.setdefault(alias, set()).add(uri)
            alias_lower = alias.lower()
            if alias_lower != alias:
                self.alias_to_uris.setdefault(alias_lower, set()).add(uri)

        return uri

    def get_aliases_for_uri(self, uri: str) -> set[str]:
        """Return all recorded aliases for a given canonical URI."""
        ent = self.entities.get(uri)
        if not ent:
            return set()
        res = {uri}
        if ent.symbol:
            res.add(ent.symbol)
        if ent.owner_type and ent.symbol:
            res.add(f"{ent.owner_type}::{ent.symbol}")
            if ent.namespace:
                res.add(f"{ent.namespace}\\{ent.owner_type}::{ent.symbol}")
        if ent.file:
            res.add(ent.file)
        res.update(ent.aliases)
        return res

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

        # Disambiguation passes
        if len(matches) > 1:
            # 1. Prefer internal entities over external://
            internals = {u for u in matches if not u.startswith("external://")}
            if internals:
                matches = internals

        if len(matches) > 1 and target_file_hint:
            norm_hint = target_file_hint.replace("\\", "/").strip("/")
            file_filtered = {
                uri for uri in matches
                if self.entities[uri].file.replace("\\", "/").strip("/") == norm_hint
            }
            if file_filtered:
                matches = file_filtered

        if len(matches) > 1:
            # 2. Prefer FILE kind if querying a file path
            if symbol_or_alias.endswith((".php", ".ts", ".js", ".py")):
                f_matches = {u for u in matches if self.entities[u].kind == EntityKind.FILE}
                if f_matches:
                    matches = f_matches
            # 3. Prefer CLASS/INTERFACE/TRAIT kind if querying a type name
            elif "::" not in symbol_or_alias and not symbol_or_alias.endswith("()"):
                t_matches = {
                    u for u in matches
                    if self.entities[u].kind in (EntityKind.CLASS, EntityKind.INTERFACE, EntityKind.TRAIT, EntityKind.ENUM)
                }
                if t_matches:
                    matches = t_matches

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
