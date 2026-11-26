"""Installable RCIR CLI. Product operations are separate from benchmark execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from .api import RepositoryService
from .snapshot import ServiceError, digest


def main(argv=None):
    parser = argparse.ArgumentParser(description="RCIR source evidence service; no benchmark success is implied.")
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ["index", "query", "serve", "status", "impact"]:
        sub = commands.add_parser(operation)
        sub.add_argument("--repo", type=Path, required=True)
        sub.add_argument("--ref", default="HEAD")
        sub.add_argument("--allow-overlay", action="store_true")
        if operation == "index":
            sub.add_argument("--output", type=Path)
        elif operation == "query":
            sub.add_argument("--query", required=True)
            sub.add_argument("--budget", type=int, default=4000)
        elif operation == "serve":
            sub.add_argument("--transport", choices=["stdio"], default="stdio")
        elif operation == "impact":
            sub.add_argument("--path", required=True)
    verify = commands.add_parser("verify-run")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "verify-run":
            from .proof import verify_run
            result = verify_run(args.run)
        else:
            service = RepositoryService(args.repo, args.ref, allow_overlay=args.allow_overlay)
            if args.operation == "serve":
                from .mcp_server import serve
                serve(service)
                return 0
            if args.operation == "query":
                result = service.retrieve(args.query, args.budget)
            elif args.operation == "impact":
                result = service.impact(args.path)
            else:
                result = service.status()
                if args.operation == "index":
                    output = args.output or Path.home() / ".cache/rcir" / digest(str(args.repo.resolve()).encode()) / "snapshot.json"
                    service.save_manifest(output)
                    result["manifest_path"] = str(output)
                    result["persistence_mode"] = "SOURCE_MANIFEST_INDEX_REBUILT_ON_START"
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (ServiceError, OSError, ImportError, ValueError) as exc:
        print(json.dumps({"status": getattr(exc, "status", "UNSUPPORTED"), "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
