"""
PolyFlow @merge Strategy Engine.

Combines outputs from multiple isolated language cells based on configured merge strategy.
"""

from typing import List, Dict, Any, Optional
from polyflow.runtime import CellResult

class MergeError(Exception):
    pass

class PolyMergeEngine:
    def merge(self, results: List[CellResult], strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        strategy = strategy_config.get("strategy", "first-success").lower()
        order = strategy_config.get("order", [])

        if strategy == "first-success":
            return self._merge_first_success(results)
        elif strategy == "fallback":
            return self._merge_fallback(results, order)
        elif strategy == "all-success":
            return self._merge_all_success(results)
        elif strategy == "parallel-collect":
            return self._merge_parallel_collect(results)
        elif strategy == "vote":
            return self._merge_vote(results)
        else:
            return self._merge_first_success(results)

    def _merge_first_success(self, results: List[CellResult]) -> Dict[str, Any]:
        for res in results:
            if res.status == "success":
                return {
                    "status": "success",
                    "winner": f"{res.language}[{res.tag}]",
                    "output": res.output,
                    "execution_time_ms": res.execution_time_ms
                }

        failures = [f"{r.language}: {r.error}" for r in results]
        return {
            "status": "failed",
            "error": "All language cells failed.",
            "cell_failures": failures
        }

    def _merge_fallback(self, results: List[CellResult], order: List[str]) -> Dict[str, Any]:
        # Sort results according to preferred order if specified
        if order:
            order_lower = [o.lower() for o in order]
            def get_rank(res: CellResult):
                lang = res.language.lower()
                return order_lower.index(lang) if lang in order_lower else 999
            results = sorted(results, key=get_rank)

        for res in results:
            if res.status == "success":
                return {
                    "status": "success",
                    "winner": f"{res.language}[{res.tag}]",
                    "output": res.output,
                    "execution_time_ms": res.execution_time_ms
                }

        return {
            "status": "failed",
            "error": "All fallback cells failed.",
            "cell_failures": [f"{r.language}: {r.error}" for r in results]
        }

    def _merge_all_success(self, results: List[CellResult]) -> Dict[str, Any]:
        combined_outputs = {}
        for res in results:
            if res.status != "success":
                return {
                    "status": "failed",
                    "error": f"Cell {res.language}[{res.tag}] failed in all-success mode: {res.error}"
                }
            combined_outputs[f"{res.language}[{res.tag}]"] = res.output

        return {
            "status": "success",
            "outputs": combined_outputs
        }

    def _merge_parallel_collect(self, results: List[CellResult]) -> Dict[str, Any]:
        collected = {}
        for res in results:
            key = f"{res.language}[{res.tag}]"
            collected[key] = {
                "status": res.status,
                "output": res.output,
                "error": res.error,
                "execution_time_ms": res.execution_time_ms
            }

        return {
            "status": "success",
            "results": collected
        }

    def _merge_vote(self, results: List[CellResult]) -> Dict[str, Any]:
        votes: Dict[str, int] = {}
        output_map = {}

        for res in results:
            if res.status == "success":
                val_str = str(res.output)
                votes[val_str] = votes.get(val_str, 0) + 1
                output_map[val_str] = res.output

        if not votes:
            return {"status": "failed", "error": "No cell succeeded to vote."}

        majority_val_str = max(votes, key=votes.get)
        return {
            "status": "success",
            "winner_output": output_map[majority_val_str],
            "vote_count": votes[majority_val_str],
            "total_votes": sum(votes.values())
        }
