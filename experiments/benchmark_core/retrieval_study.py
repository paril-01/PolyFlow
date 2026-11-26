"""Explicit DEV retrieval comparisons; public queries never receive gold labels."""
import json
import math
from pathlib import Path
import statistics
import time

from rcir.service import RepositoryService, ServiceError
from rcir.service.snapshot import canonical, digest, safe_path
from rcir.service.proof import seal_run


def percentile(values, probability):
    values = sorted(values)
    return values[min(len(values) - 1, math.ceil(probability * len(values)) - 1)] if values else None


def score_spans(spans, gold):
    """A hit requires exact path AND coverage of the complete required span."""
    hits, ranks = [], []
    for target in gold:
        matches = [i + 1 for i, span in enumerate(spans) if span["file_path"] == target["path"]
                   and span["start_line"] <= target["start_line"] and span["end_line"] >= target["end_line"]]
        hits.append(bool(matches))
        if matches:
            ranks.append(min(matches))
    return {"critical_span_recall": sum(hits) / len(gold), "all_critical_found": all(hits),
            "reciprocal_first_rank": 1 / min(ranks) if ranks else 0,
            "edge_precision": None, "edge_precision_status": "NOT_MEASURED_NO_EDGE_ORACLE"}


def run_study(repo, commit, public_path, gold_path, output, *, arms=("R0",), graph=None, budgets=(1000, 2000, 4000, 8000)):
    output, repo = Path(output), Path(repo).resolve()
    if output.exists():
        raise ServiceError("INVALID_SCOPE", "Run output must be new; receipts cannot be overwritten")
    if Path(public_path).resolve() == Path(gold_path).resolve():
        raise ServiceError("INVALID_SCOPE", "Public prompts and private gold must be separate")
    try:
        Path(gold_path).resolve().relative_to(repo)
    except ValueError:
        pass
    else:
        raise ServiceError("INVALID_SCOPE", "Private gold must stay outside the visible target repository")
    public_bytes, gold_bytes = Path(public_path).read_bytes(), Path(gold_path).read_bytes()
    public, gold = json.loads(public_bytes), json.loads(gold_bytes)
    tasks = public.get("tasks", [])
    if not tasks or len({t.get("task_id") for t in tasks}) != len(tasks):
        raise ServiceError("INVALID_SCOPE", "Nonempty uniquely identified tasks required")
    if not arms or len(set(arms)) != len(arms) or set(arms) - {"R0", "R1", "R2", "R3"}:
        raise ServiceError("INVALID_SCOPE", "Unknown or duplicate retrieval arm")
    if not budgets or any(type(b) is not int or b < 100 or b > 1_000_000 for b in budgets):
        raise ServiceError("INVALID_SCOPE", "Explicit bounded positive delivery budgets required")
    started = time.perf_counter()
    base = RepositoryService(repo, commit)
    if base.snapshot.commit != commit:
        raise ServiceError("STALE", "An exact resolved commit SHA is required")
    for task in tasks:
        if set(task) != {"task_id", "query"} or not isinstance(task["query"], str) or not task["query"].strip():
            raise ServiceError("INVALID_SCOPE", "Public task fields must be task_id and query only")
        targets = gold.get(task["task_id"])
        if not isinstance(targets, list) or not targets:
            raise ServiceError("INVALID_SCOPE", "Each task requires a nonempty independent critical-span oracle")
        if len({(t["path"], t["start_line"], t["end_line"]) for t in targets}) != len(targets):
            raise ServiceError("AMBIGUOUS", "Duplicate critical-span oracle entries")
        for target in targets:
            safe_path(repo, target["path"])
            source = base.snapshot.files.get(target["path"])
            if source is None or target.get("file_sha256") != source.sha256:
                raise ServiceError("STALE", "Gold must bind to actual source bytes")
            if not (type(target["start_line"]) is int and type(target["end_line"]) is int
                    and 1 <= target["start_line"] <= target["end_line"] <= len(source.raw.splitlines())):
                raise ServiceError("INVALID_SCOPE", "Invalid critical span coordinates")
    providers, index_seconds = {"R0": base}, {"R0": time.perf_counter() - started}
    if set(arms) & {"R1", "R3"}:
        from experiments.architecture_trials.v3.r1_adapter.adapter import R1RCIRAdapter
        start = time.perf_counter()
        canonical_provider = R1RCIRAdapter(repo, graph, commit)
        providers["R1"] = canonical_provider
        index_seconds["R1"] = time.perf_counter() - start
    if "R2" in arms:
        from experiments.architecture_trials.v3.r2_versioned_evidence.vest_lite import VestLiteEvidenceStore
        start = time.perf_counter()
        store = VestLiteEvidenceStore(repo, commit)
        # Exactly the same visible source census for every contender.
        for path in base.snapshot.files:
            store.index_file(path)
        r2 = RepositoryService(repo, commit)
        def vest(query):
            found = store.retrieve(query, max_tokens=1_000_000)["evidence_items"]
            return [{**r2.index._span(s["file_path"], s["start_line"], s["end_line"], s["symbol"], "INFERRED", "vest_regex_candidate"),
                     "score": s["score"]} for s in found]
        r2.candidate_provider, r2.retrieval_method = vest, "R2_VEST_SOURCE_REHYDRATED"
        providers["R2"], index_seconds["R2"] = r2, time.perf_counter() - start
    if "R3" in arms:
        hybrid = RepositoryService(repo, commit)
        def combined(query):
            lexical = hybrid.index.candidates(query)
            graph_spans = canonical_provider.candidates(query)
            seen, result = set(), []
            for span in lexical + graph_spans:
                key = span["file_path"], span["start_byte"], span["end_byte"]
                if key not in seen:
                    seen.add(key)
                    result.append(span)
            return result
        hybrid.candidate_provider, hybrid.retrieval_method = combined, "R3_LEXICAL_CANONICAL_UNION_CANDIDATE"
        providers["R3"], index_seconds["R3"] = hybrid, None
    records = []
    for task in tasks:
        for budget in budgets:
            for arm in arms:
                before = time.perf_counter()
                delivered = providers[arm].retrieve(task["query"], budget)
                elapsed = time.perf_counter() - before
                counter = base.counter
                actual = counter.count(canonical(delivered).decode())
                if actual > budget or delivered["tokens_consumed"] != actual:
                    raise ServiceError("BUDGET_INSUFFICIENT", "Actual delivery budget violation")
                records.append({"task_id": task["task_id"], "arm": arm, "budget": budget, "seconds": elapsed,
                                "measured_tokens": actual, "delivery": delivered,
                                **score_spans(delivered["evidence_items"], gold[task["task_id"]])})
    summary = {}
    for arm in arms:
        for budget in budgets:
            rows = [r for r in records if r["arm"] == arm and r["budget"] == budget]
            latency = [r["seconds"] for r in rows]
            summary[f"{arm}@{budget}"] = {"mean_critical_recall": statistics.mean(r["critical_span_recall"] for r in rows),
                                          "query_p50_seconds": statistics.median(latency), "query_p95_seconds": percentile(latency, .95),
                                          "budget_violations": 0}
    receipt = {"schema": "rcir.retrieval_study.v1", "scope": "DEV_ONLY", "winner": None,
               "architecture_approval": False, "snapshot": base.status(), "public_sha256": digest(public_bytes),
               "gold_sha256": digest(gold_bytes), "cold_index_seconds": index_seconds,
               "latency_scope": "QUERY_INCLUDES_FULL_SOURCE_FRESHNESS_VERIFICATION", "records": records, "summary": summary}
    output.mkdir(parents=True)
    (output / "receipt.json").write_bytes(canonical(receipt))
    seal_run(output)
    return receipt
