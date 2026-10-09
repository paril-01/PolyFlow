"""
RCIR Context Delivery Models (PHASE 3 / SECTION 7).

Defines the canonical ContextRetrievalResult model:
- Guarantees uniform structure between context providers and agent tools
- Provides backward and dict-access compatibility (no dictionary-shape guessing)
- Enforces strict tracking of candidates, delivered entries, tokens, and seen entities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Optional


@dataclass
class ContextRetrievalResult(Mapping[str, Any]):
    """
    Canonical delivery envelope for RCIR and baseline context retrievals.
    Every context provider and agent tool must use it.
    """
    entries: list[dict[str, Any]] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)
    rendered_markdown: str = ""
    tokens_added: int = 0
    duplicates_skipped: int = 0
    requested_symbol: str = ""
    source_task_id: str = ""
    budget: int = 1500
    candidate_count: int = 0
    remaining_budget: int = 0
    provider_name: str = "RCIRContextProvider"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-populate entity_ids if entries provided but entity_ids empty
        if not self.entity_ids and self.entries:
            self.entity_ids = [
                e.get("entity_id", "") for e in self.entries if e.get("entity_id")
            ]
        # Calculate remaining budget if not explicitly set
        if self.remaining_budget == 0 and self.budget > 0:
            self.remaining_budget = max(0, self.budget - self.tokens_added)
        # Auto-render markdown if empty and entries exist
        if not self.rendered_markdown and self.entries:
            self.rendered_markdown = self._default_render_markdown()

    def _default_render_markdown(self) -> str:
        """Render entries into markdown when provider did not supply pre-rendered text."""
        lines = [
            f"# Context for `{self.requested_symbol}` (Budget: {self.tokens_added}/{self.budget} tokens)",
            f"**Included Entities:** {len(self.entries)} | **Skipped (Seen):** {self.duplicates_skipped}",
            "",
        ]
        for idx, entry in enumerate(self.entries, start=1):
            ent_id = entry.get("entity_id", "unknown")
            source_file = entry.get("source_file", "")
            lines_range = entry.get("source_lines", [1, 1])
            snippet = entry.get("content_snippet", "")
            reason = entry.get("reason", "relevance")
            est_tokens = entry.get("estimated_tokens", 0)

            lines.append(f"## [{idx}] {ent_id}")
            if source_file:
                s_line = lines_range[0] if len(lines_range) > 0 else 1
                e_line = lines_range[1] if len(lines_range) > 1 else s_line
                lines.append(f"- **File:** `{source_file}` (Lines {s_line}-{e_line})")
            lines.append(f"- **Reason:** {reason} (~{est_tokens} tokens)")
            if snippet:
                lines.append("```php")
                lines.append(snippet.strip())
                lines.append("```")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": self.entries,
            "entity_ids": self.entity_ids,
            "entities": self.entity_ids,  # alias for legacy consumers
            "rendered_markdown": self.rendered_markdown,
            "context_markdown": self.rendered_markdown,  # alias for legacy consumers
            "tokens_added": self.tokens_added,
            "tokens_delivered": self.tokens_added,  # alias
            "duplicates_skipped": self.duplicates_skipped,
            "requested_symbol": self.requested_symbol,
            "source_task_id": self.source_task_id,
            "budget": self.budget,
            "candidate_count": self.candidate_count,
            "remaining_budget": self.remaining_budget,
            "provider_name": self.provider_name,
            "metadata": self.metadata,
        }

    # Dict-like mapping compatibility:
    def __getitem__(self, key: str) -> Any:
        # Support aliases
        if key == "context_markdown":
            return self.rendered_markdown
        if key == "entities":
            return self.entity_ids
        if key == "tokens_delivered":
            return self.tokens_added
        if key == "entities_found" or key == "entries_count":
            return len(self.entries)
        if key == "new_entities":
            return self.entity_ids
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextRetrievalResult:
        entries = data.get("entries", [])
        entity_ids = data.get("entity_ids", data.get("entities", []))
        rendered_md = data.get("rendered_markdown", data.get("context_markdown", ""))
        tokens = data.get("tokens_added", data.get("tokens_delivered", 0))
        skipped = data.get("duplicates_skipped", 0)
        symbol = data.get("requested_symbol", data.get("symbol", ""))
        task_id = data.get("source_task_id", data.get("task_id", ""))
        budget = data.get("budget", data.get("token_budget", 1500))
        cand_count = data.get("candidate_count", data.get("candidates_evaluated", len(entries)))
        rem_budget = data.get("remaining_budget", max(0, budget - tokens))

        return cls(
            entries=entries,
            entity_ids=entity_ids,
            rendered_markdown=rendered_md,
            tokens_added=tokens,
            duplicates_skipped=skipped,
            requested_symbol=symbol,
            source_task_id=task_id,
            budget=budget,
            candidate_count=cand_count,
            remaining_budget=rem_budget,
            provider_name=data.get("provider_name", "RCIRContextProvider"),
            metadata=data.get("metadata", {}),
        )
