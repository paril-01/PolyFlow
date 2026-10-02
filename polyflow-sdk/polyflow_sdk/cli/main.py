"""
PolyFlow SDK Unified CLI Entry Point.

Modeled after modern developer CLIs (Flutter, Cargo, Next.js).
Commands:
  polyflow doctor             - Diagnose host environment & toolchains
  polyflow run <file.poly>    - Execute multi-language contracts
  polyflow analyze <path>     - RCIR dependency graph & impact extraction
  polyflow test <dir>         - Validate .poly feature contracts
  polyflow agent <task>       - Run agent pool with token bounding
"""

import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from polyflow_sdk import __version__
from polyflow_sdk.cli.commands.doctor import execute_doctor
from polyflow_sdk.cli.commands.run import execute_run
from polyflow_sdk.cli.commands.analyze import execute_analyze
from polyflow_sdk.cli.commands.test import execute_test
from polyflow_sdk.cli.commands.agent import execute_agent


BANNER = rf"""
  ____       _        _____ _                 
 |  _ \ ___ | |_   _ |  ___| | _____      __  
 | |_) / _ \| | | | || |_  | |/ _ \ \ /\ / /  
 |  __/ (_) | | |_| ||  _| | | (_) \ V  V /   
 |_|   \___/|_|\__, ||_|   |_|\___/ \_/\_/    
               |___/   SDK v{__version__}
"""


def main():
    parser = argparse.ArgumentParser(
        prog="polyflow",
        description="PolyFlow Unified Multi-Language Contract Engine & RCIR Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use 'polyflow <command> --help' for command-specific options."
    )
    parser.add_argument("--version", "-v", action="version", version=f"PolyFlow SDK {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. doctor
    subparsers.add_parser("doctor", help="Diagnose environment and toolchains (Python, Node, Java, Go, PHP, Git, RCIR)")

    # 2. run
    run_parser = subparsers.add_parser("run", help="Execute a .poly file with optional input payload")
    run_parser.add_argument("file", help="Path to .poly contract file")
    run_parser.add_argument("--payload", "-p", help="JSON string payload to pass to entry point cell", default=None)

    # 3. analyze
    analyze_parser = subparsers.add_parser("analyze", help="Extract RCIR dependency graph and analyze impact")
    analyze_parser.add_argument("path", help="Path to codebase directory", default=".", nargs="?")
    analyze_parser.add_argument("--impact", "-i", help="Symbol name to compute change blast radius for", default=None)
    analyze_parser.add_argument("--output", "-o", help="JSON output file path for extracted graph", default=None)

    # 4. test
    test_parser = subparsers.add_parser("test", help="Discover and test all .poly contract files in project")
    test_parser.add_argument("dir", help="Directory to search for .poly files", default=".", nargs="?")

    # 5. agent
    agent_parser = subparsers.add_parser("agent", help="Run AI engineering agent pool with token-budget bounding")
    agent_parser.add_argument("task", help="Task description or prompt for the agent pool")
    agent_parser.add_argument("--repo", "-r", help="Repository path", default=".")
    agent_parser.add_argument("--budget", "-b", type=int, help="Maximum token budget ceiling", default=4000)

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        sys.exit(0)

    if args.command == "doctor":
        sys.exit(execute_doctor())
    elif args.command == "run":
        sys.exit(execute_run(args.file, args.payload))
    elif args.command == "analyze":
        sys.exit(execute_analyze(args.path, args.impact, args.output))
    elif args.command == "test":
        sys.exit(execute_test(args.dir))
    elif args.command == "agent":
        sys.exit(execute_agent(args.task, args.repo, args.budget))


if __name__ == "__main__":
    main()
