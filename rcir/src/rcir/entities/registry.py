"""
RCIR v8 — Entity Registry (PHASE 5).

Maintains indexed repository entities and tracks symbol ambiguity degrees.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from rcir.entities.entity import EntityIdentity, EntityKind


class EntityRegistry:
    """Repository-wide index of entities with ambiguity tracking."""

    def __init__(self, repository: str = "default"):
        self.repository = repository
        self.by_id: dict[str, EntityIdentity] = {}
        self.by_name: dict[str, list[EntityIdentity]] = defaultdict(list)
        self.by_owner_name: dict[tuple[str, str], list[EntityIdentity]] = defaultdict(list)
        self.by_file: dict[str, list[EntityIdentity]] = defaultdict(list)

    def register(self, entity: EntityIdentity) -> None:
        self.by_id[entity.entity_id] = entity
        self.by_name[entity.name].append(entity)
        if entity.owner:
            self.by_owner_name[(entity.owner, entity.name)].append(entity)
        if entity.file:
            self.by_file[entity.file].append(entity)

    def get_by_id(self, entity_id: str) -> EntityIdentity | None:
        return self.by_id.get(entity_id)

    def lookup_name(self, name: str) -> list[EntityIdentity]:
        """Lookup entities by simple symbol name."""
        return self.by_name.get(name, [])

    def lookup_qualified(self, owner: str, name: str) -> list[EntityIdentity]:
        """Lookup entities by owner and symbol name."""
        matches = self.by_owner_name.get((owner, name), [])
        if not matches:
            # Fuzzy match owner ending
            for (o, n), ents in self.by_owner_name.items():
                if n == name and (o.endswith(owner) or owner.endswith(o)):
                    matches.extend(ents)
        return matches

    def ambiguity_degree(self, symbol_name: str) -> int:
        """Count how many distinct entities share this symbol name."""
        return len(self.by_name.get(symbol_name, []))

    def is_generic_symbol(self, symbol_name: str, threshold: int = 5) -> bool:
        """Return True if symbol occurs widely across many distinct classes."""
        return self.ambiguity_degree(symbol_name) >= threshold

    @classmethod
    def from_graph(cls, graph: dict[str, Any], repository: str = "default") -> EntityRegistry:
        """Construct EntityRegistry from an existing RCIR graph dictionary."""
        reg = cls(repository=repository)
        nodes = graph.get("nodes", [])

        for node in nodes:
            path = node.get("path", "")
            file_part = path.split("::")[0].replace("\\", "/").strip("/") if "::" in path else path.replace("\\", "/").strip("/")
            symbol_part = path.split("::")[-1] if "::" in path else ""

            owner = None
            name = symbol_part
            namespace = ""

            if "\\" in symbol_part:
                ns_parts = symbol_part.rsplit("\\", 1)
                namespace = ns_parts[0]
                name = ns_parts[1]

            if "::" in symbol_part:
                sub_parts = symbol_part.split("::")
                owner = sub_parts[0].split("\\")[-1]
                name = sub_parts[-1]

            kind_str = node.get("kind", "unknown")
            try:
                kind = EntityKind(kind_str)
            except ValueError:
                kind = EntityKind.UNKNOWN

            lang = "php" if file_part.endswith(".php") else "typescript" if file_part.endswith((".ts", ".js")) else "python"
            module = "core"
            if "apps/" in file_part:
                parts = file_part.split("apps/")[1].split("/")
                if parts:
                    module = f"apps/{parts[0]}"

            entity = EntityIdentity(
                repository=repository,
                language=lang,
                file=file_part,
                namespace=namespace,
                module=module,
                kind=kind,
                owner=owner,
                name=name or file_part.split("/")[-1],
                entity_id=path,
            )
            reg.register(entity)

        return reg
