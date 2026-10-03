"""
RCIR v8 — Entity Resolver (PHASE 5).

Resolves query symbols to EntityIdentity objects with explicit ambiguity detection.
Prevents generic symbol collision where e.g. 'getId' matches dozens of unrelated classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rcir.entities.entity import EntityIdentity
from rcir.entities.registry import EntityRegistry


@dataclass
class ResolutionResult:
    """Result of resolving a symbol query against the entity registry."""
    query_symbol: str
    exact_matches: list[EntityIdentity] = field(default_factory=list)
    ambiguous_candidates: list[EntityIdentity] = field(default_factory=list)
    is_ambiguous: bool = False
    ambiguity_degree: int = 0
    resolved_entity: EntityIdentity | None = None
    warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_symbol": self.query_symbol,
            "is_ambiguous": self.is_ambiguous,
            "ambiguity_degree": self.ambiguity_degree,
            "resolved_entity_id": self.resolved_entity.entity_id if self.resolved_entity else None,
            "exact_match_count": len(self.exact_matches),
            "ambiguous_candidate_count": len(self.ambiguous_candidates),
            "warning": self.warning,
        }


class EntityResolver:
    """Disambiguates and resolves symbols to specific entity identities."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry

    def resolve(
        self,
        symbol: str,
        owner_hint: str | None = None,
        file_hint: str | None = None,
        namespace_hint: str | None = None,
    ) -> ResolutionResult:
        """Resolve a symbol with optional contextual hints to eliminate ambiguity.

        Args:
            symbol: Target symbol name (e.g. 'getId', 'Node::getId', 'ApiController::getThumbnail')
            owner_hint: Class/interface owner hint (e.g. 'Node', 'ApiController')
            file_hint: File path hint (e.g. 'lib/public/Files/Node.php')
            namespace_hint: Namespace prefix hint (e.g. 'OCP\\Files')
        """
        # Parse symbol for internal qualifiers
        clean_symbol = symbol.strip()
        parsed_owner = owner_hint

        if "::" in clean_symbol:
            parts = clean_symbol.split("::")
            parsed_owner = parts[0].split("\\")[-1]
            clean_symbol = parts[-1]

        candidates = self.registry.lookup_name(clean_symbol)
        ambiguity_count = len(candidates)

        if not candidates:
            # Try looking up as full FQCN or ID
            ent = self.registry.get_by_id(symbol)
            if ent:
                return ResolutionResult(
                    query_symbol=symbol,
                    exact_matches=[ent],
                    resolved_entity=ent,
                    is_ambiguous=False,
                    ambiguity_degree=1,
                )
            return ResolutionResult(
                query_symbol=symbol,
                warning=f"Symbol '{symbol}' not found in entity registry",
            )

        # Filter by file hint if present
        filtered = list(candidates)
        if file_hint:
            norm_file = file_hint.replace("\\", "/").strip("/")
            file_filtered = [c for c in filtered if norm_file in c.file or c.file.endswith(norm_file)]
            if file_filtered:
                filtered = file_filtered

        # Filter by owner hint if present
        if parsed_owner:
            owner_clean = parsed_owner.split("\\")[-1]
            owner_filtered = [c for c in filtered if c.owner and (owner_clean in c.owner or c.owner in owner_clean)]
            if owner_filtered:
                filtered = owner_filtered

        # Filter by namespace hint if present
        if namespace_hint:
            ns_clean = namespace_hint.strip("\\")
            ns_filtered = [c for c in filtered if ns_clean in c.namespace]
            if ns_filtered:
                filtered = ns_filtered

        # Evaluate ambiguity
        if len(filtered) == 1:
            return ResolutionResult(
                query_symbol=symbol,
                exact_matches=filtered,
                resolved_entity=filtered[0],
                is_ambiguous=False,
                ambiguity_degree=ambiguity_count,
            )

        # Still multiple matches: explicit ambiguity
        is_ambiguous = len(filtered) > 1 or ambiguity_count >= 5
        warning = ""
        if is_ambiguous:
            warning = (
                f"Generic symbol collision: '{symbol}' matches {len(filtered)} entities "
                f"(repository-wide ambiguity degree: {ambiguity_count}). "
                "Disambiguation required via owner or file hint."
            )

        return ResolutionResult(
            query_symbol=symbol,
            exact_matches=[] if is_ambiguous else filtered,
            ambiguous_candidates=filtered,
            is_ambiguous=is_ambiguous,
            ambiguity_degree=ambiguity_count,
            resolved_entity=None,
            warning=warning,
        )
