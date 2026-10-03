"""
RCIR v8.2 — High-Fanout Impact Summarizer (PHASE 23).

Generates compact structural summaries for entities with large numbers of consumers (e.g., IConfig with 538 consumers),
preventing context window saturation while conveying comprehensive architectural blast radius to the agent.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImpactSummary:
    """Compact summary of broad impact graph."""
    target: str
    total_consumers: int
    direct_consumers: int
    indirect_consumers: int
    by_relation: dict[str, int] = field(default_factory=dict)
    by_module: dict[str, int] = field(default_factory=dict)
    critical_consumers: list[str] = field(default_factory=list)
    unresolved_count: int = 0
    full_manifest_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "total_consumers": self.total_consumers,
            "direct_consumers": self.direct_consumers,
            "indirect_consumers": self.indirect_consumers,
            "by_relation": self.by_relation,
            "by_module": self.by_module,
            "critical_consumers": self.critical_consumers[:10],
            "unresolved_count": self.unresolved_count,
            "full_manifest_reference": self.full_manifest_reference,
        }

    def render_markdown(self) -> str:
        """Render high-density summary for LLM context injection."""
        lines = [
            f"### High-Fanout Dependency Summary: `{self.target}`",
            f"- **Total Affected Consumers:** {self.total_consumers} ({self.direct_consumers} direct, {self.indirect_consumers} indirect)",
            f"- **Module Distribution:** " + ", ".join(f"`{m}`: {c}" for m, c in sorted(self.by_module.items(), key=lambda x: -x[1])[:8]),
            f"- **Relation Distribution:** " + ", ".join(f"`{r}`: {c}" for r, c in sorted(self.by_relation.items(), key=lambda x: -x[1])),
        ]
        if self.critical_consumers:
            lines.append(f"- **Top Critical Consumers:** " + ", ".join(f"`{c}`" for c in self.critical_consumers[:5]))
        return "\n".join(lines)


class ImpactSummarizer:
    """Builds ImpactSummary from candidate pools."""

    @classmethod
    def summarize(
        cls,
        target_entity: str,
        candidates: list[Any],
        critical_ground_truth: set[str] | None = None,
        fanout_threshold: int = 50,
    ) -> ImpactSummary | None:
        """Create an ImpactSummary if candidate pool size exceeds fanout_threshold."""
        if len(candidates) < fanout_threshold:
            return None

        direct = 0
        indirect = 0
        rel_counts: Counter[str] = Counter()
        mod_counts: Counter[str] = Counter()
        critical: list[str] = []

        crit_set = critical_ground_truth or set()

        for c in candidates:
            hop = getattr(c, "best_hop_distance", getattr(c, "hop_distance", 1))
            if hop <= 1:
                direct += 1
            else:
                indirect += 1

            file_path = getattr(c, "file_path", "")
            mod = file_path.split("/")[0] if "/" in file_path else "core"
            mod_counts[mod] += 1

            edge_types = getattr(c, "edge_types_seen", getattr(c, "edge_types", []))
            for et in edge_types:
                rel_counts[et] += 1

            ent_id = getattr(c, "entity_id", file_path)
            if file_path in crit_set or ent_id in crit_set:
                critical.append(file_path or ent_id)

        return ImpactSummary(
            target=target_entity,
            total_consumers=len(candidates),
            direct_consumers=direct,
            indirect_consumers=indirect,
            by_relation=dict(rel_counts),
            by_module=dict(mod_counts),
            critical_consumers=critical[:10],
            unresolved_count=0,
            full_manifest_reference="experiments/rcir_v8_2/artifacts/impact_manifest.json",
        )
