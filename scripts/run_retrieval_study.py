"""Explicit, non-overwriting DEV retrieval study CLI."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "rcir/src")]
from experiments.benchmark_core.retrieval_study import run_study
from rcir.service import ServiceError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["repo", "commit", "public", "gold", "output"]:
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--graph")
    parser.add_argument("--arms", nargs="+", default=["R0"])
    args = parser.parse_args(argv)
    try:
        receipt = run_study(args.repo, args.commit, args.public, args.gold, args.output, arms=args.arms, graph=args.graph)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": getattr(exc, "status", "INVALID_SETUP"), "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(receipt["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
