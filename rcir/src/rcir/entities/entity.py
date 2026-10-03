"""
RCIR v8 — Stable Entity Identity Model (PHASE 5).

Provides unique, namespace-aware, owner-qualified identities for repository symbols
to eliminate generic symbol collisions (e.g. 'getId').
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class EntityKind(str, Enum):
    FILE = "file"
    CLASS = "class"
    INTERFACE = "interface"
    TRAIT = "trait"
    METHOD = "method"
    FUNCTION = "function"
    ROUTE = "route"
    EVENT = "event"
    CONFIG_KEY = "config_key"
    SERVICE = "service"
    UNKNOWN = "unknown"


@dataclass
class EntityIdentity:
    """Stable, repository-wide entity identifier."""
    repository: str
    language: str
    file: str
    namespace: str
    module: str
    kind: EntityKind | str
    owner: str | None
    name: str
    signature_fingerprint: str | None = None
    entity_id: str = ""

    def __post_init__(self):
        if not self.entity_id:
            self.entity_id = self.compute_id()

    def compute_id(self) -> str:
        """Generate canonical composite entity ID."""
        parts = []
        if self.file:
            parts.append(self.file.replace("\\", "/").strip("/"))
        if self.namespace:
            parts.append(self.namespace.strip("\\"))
        if self.owner:
            parts.append(self.owner)
        parts.append(self.name)
        return "::".join([p for p in parts if p])

    @property
    def fqcn(self) -> str:
        """Fully qualified class/symbol name."""
        if self.namespace:
            ns = self.namespace.strip("\\")
            owner_prefix = f"{self.owner}::" if self.owner else ""
            return f"{ns}\\{owner_prefix}{self.name}"
        return f"{self.owner}::{self.name}" if self.owner else self.name

    def matches(self, symbol_name: str, owner_hint: str | None = None) -> bool:
        """Test whether this entity matches a query symbol with optional owner qualification."""
        clean_sym = symbol_name.strip("\\")
        if "::" in clean_sym:
            parts = clean_sym.split("::")
            req_owner = parts[0].split("\\")[-1]
            req_name = parts[-1]
            return self.name == req_name and (self.owner is None or req_owner in self.owner)

        if owner_hint and self.owner:
            owner_clean = owner_hint.split("\\")[-1]
            if owner_clean not in self.owner and self.owner not in owner_clean:
                return False

        return self.name == clean_sym or self.fqcn.endswith(clean_sym)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "repository": self.repository,
            "language": self.language,
            "file": self.file,
            "namespace": self.namespace,
            "module": self.module,
            "kind": self.kind.value if isinstance(self.kind, EntityKind) else str(self.kind),
            "owner": self.owner,
            "name": self.name,
            "signature_fingerprint": self.signature_fingerprint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityIdentity:
        return cls(
            repository=data.get("repository", "default"),
            language=data.get("language", "unknown"),
            file=data.get("file", ""),
            namespace=data.get("namespace", ""),
            module=data.get("module", "core"),
            kind=data.get("kind", EntityKind.UNKNOWN),
            owner=data.get("owner"),
            name=data.get("name", ""),
            signature_fingerprint=data.get("signature_fingerprint"),
            entity_id=data.get("entity_id", ""),
        )
