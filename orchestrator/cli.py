"""
CLI entrypoint for AEF Orchestrator.
Allows running the 5-agent sequential pipeline from the command line.
"""

import argparse
import sys
from pathlib import Path
from orchestrator.runner import OrchestratorRunner

def main():
    parser = argparse.ArgumentParser(
        description="AEF Orchestrator — Automated End-to-End AI Engineering Pipeline"
    )
    parser.add_argument(
        "request",
        nargs="?",
        default="Build a health check microservice with structured logging and rate limiting",
        help="Feature description or problem statement for the AEF pipeline"
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "openai", "anthropic", "gemini", "dry-run"],
        default="auto",
        help="LLM provider to use (default: auto, detects API key or falls back to dry-run)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force simulated dry-run mode without making external API calls"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console progress output"
    )

    args = parser.parse_args()

    provider_name = "dry-run" if args.dry_run else args.provider

    try:
        runner = OrchestratorRunner(provider_name=provider_name)
        runner.run_pipeline(args.request, verbose=not args.quiet)
    except Exception as e:
        print(f"Error executing AEF pipeline: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
