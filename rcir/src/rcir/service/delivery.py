"""Default-off supplementary presentation. Never transforms exact evidence.

This deterministic comparator does not claim to integrate Headroom. Every view
is explicitly lossy; original bytes are available only while its scoped lease
is live. No networking or model inference is used.
"""
from collections import OrderedDict
from dataclasses import dataclass
import time

from .snapshot import ServiceError, canonical, digest


@dataclass(frozen=True)
class DeliveryScope:
    tenant: str
    snapshot: str
    policy: str


class SupplementaryDelivery:
    eligible = frozenset({"log", "search", "json", "diff"})

    def __init__(self, counter, *, enabled=False, max_entries=128, max_bytes=8_000_000, ttl_seconds=300, clock=time.monotonic):
        if max_entries < 1 or max_bytes < 1 or ttl_seconds <= 0:
            raise ServiceError("INVALID_SCOPE", "Positive cache bounds required")
        self.counter, self.enabled = counter, enabled
        self.max_entries, self.max_bytes, self.ttl, self.clock = max_entries, max_bytes, ttl_seconds, clock
        self.cache = OrderedDict()

    def _expire(self):
        now = self.clock()
        for key, (_, _, expiry) in list(self.cache.items()):
            if expiry <= now:
                del self.cache[key]

    def present(self, raw: bytes, kind: str, scope: DeliveryScope, budget: int, *, protected=False):
        if not isinstance(raw, bytes) or type(budget) is not int or budget <= 0:
            raise ServiceError("INVALID_SCOPE", "Bytes and a positive token budget required")
        text = raw.decode("utf-8")
        original_hash = digest(raw)
        result = {"kind": kind, "original_sha256": original_hash, "view": text, "lossy": False,
                  "restore_handle": None, "availability": "INLINE_ORIGINAL", "algorithm": "PASSTHROUGH"}
        # Preserve all instructions, verifier results, security and source kinds.
        if self.enabled and not protected and kind in self.eligible:
            lines = text.splitlines(keepends=True)
            view = []
            for line in lines:
                if not view or view[-1] != line:
                    view.append(line)
            compact = "".join(view)
            if compact != text:
                key = digest(canonical([scope.__dict__, original_hash, "adjacent-line-dedup-v1"]))
                original_result = dict(result)
                result.update(view=compact, lossy=True, restore_handle=key,
                              availability="SCOPED_CACHE_LEASE", algorithm="ADJACENT_LINE_DEDUP_V1")
                if self.counter.count(canonical(result).decode()) >= self.counter.count(canonical(original_result).decode()):
                    result = original_result
                    if self.counter.count(canonical(result).decode()) > budget:
                        raise ServiceError("BUDGET_INSUFFICIENT", "Original supplementary payload exceeds budget")
                    return result
                if len(raw) > self.max_bytes:
                    raise ServiceError("UNRESOLVED", "Original exceeds restoration cache capacity")
                self._expire()
                self.cache[key] = (scope, raw, self.clock() + self.ttl)
                self.cache.move_to_end(key)
                while len(self.cache) > self.max_entries or sum(len(v[1]) for v in self.cache.values()) > self.max_bytes:
                    self.cache.popitem(last=False)
        if self.counter.count(canonical(result).decode()) > budget:
            raise ServiceError("BUDGET_INSUFFICIENT", "Supplementary envelope exceeds budget")
        return result

    def restore(self, handle: str, scope: DeliveryScope):
        self._expire()
        record = self.cache.get(handle)
        if record is None or record[0] != scope:
            raise ServiceError("UNRESOLVED", "Original unavailable in this scope")
        _, raw, _ = record
        if digest(canonical([scope.__dict__, digest(raw), "adjacent-line-dedup-v1"])) != handle:
            raise ServiceError("STALE", "Original integrity mismatch")
        self.cache.move_to_end(handle)
        return raw
