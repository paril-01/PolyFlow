"""
PolyFlow SDK Unified CLI Entry Point.

Modeled after modern developer CLIs (Flutter, Cargo, Next.js).
Commands:
  polyflow doctor              - Diagnose host environment & toolchains
  polyflow run <file.poly>     - Execute multi-language contracts
  polyflow inspect <file.poly> - Inspect .poly AST, contracts, and sources
  polyflow ast <file.poly>     - Output machine-readable AST JSON
  polyflow lint <path>         - Check .poly syntax and structural integrity
  polyflow fmt <path>          - Format .poly files
  polyflow errors              - Show structured execution error logs & suggestions
  polyflow self-test           - Run internal SDK verification test suite
  polyflow demo                - Run end-to-end multi-language system showcase
  polyflow analyze <path>      - RCIR dependency graph & impact extraction
  polyflow test <dir>          - Validate .poly feature contracts
  polyflow agent <task>        - Run AI coding agent with token bounding
  polyflow benchmark tokens    - Token telemetry reductions and comparison
"""

import sys
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from polyflow_sdk import __version__
from polyflow_sdk.cli.commands.doctor import execute_doctor
from polyflow_sdk.cli.commands.run import execute_run
from polyflow_sdk.cli.commands.analyze import execute_analyze
from polyflow_sdk.cli.commands.test import execute_test
from polyflow_sdk.cli.commands.agent import execute_agent
from polyflow_sdk.cli.commands.benchmark import execute_benchmark_tokens
from polyflow_sdk.cli.commands.inspect import execute_inspect, execute_ast
from polyflow_sdk.cli.commands.lint import execute_lint, execute_fmt
from polyflow_sdk.cli.commands.errors import execute_errors
from polyflow_sdk.cli.commands.selftest import execute_self_test
from polyflow_sdk.cli.commands.demo import execute_demo


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

    # 3. inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect .poly structure, contracts, schemas, and source refs")
    inspect_parser.add_argument("file", help="Path to .poly file")
    inspect_parser.add_argument("--json", "-j", action="store_true", help="Output machine-readable AST as JSON")

    # 4. ast
    ast_parser = subparsers.add_parser("ast", help="Output machine-readable AST as JSON")
    ast_parser.add_argument("file", help="Path to .poly file")
    ast_parser.add_argument("--json", "-j", action="store_true", default=True, help="Output formatted JSON (default)")

    # 5. lint
    lint_parser = subparsers.add_parser("lint", help="Lint .poly files for syntax errors and unclosed directives")
    lint_parser.add_argument("path", help="Path to .poly file or directory", default=".", nargs="?")

    # 6. fmt
    fmt_parser = subparsers.add_parser("fmt", help="Format .poly files")
    fmt_parser.add_argument("path", help="Path to .poly file or directory", default=".", nargs="?")
    fmt_parser.add_argument("--write", "-w", action="store_true", help="Overwrite file in-place with formatted output")

    # 7. errors
    errors_parser = subparsers.add_parser("errors", help="Display structured runtime error diagnostics and fix suggestions")
    errors_parser.add_argument("path", help="Directory or file path to check", default=None, nargs="?")

    # 8. self-test
    subparsers.add_parser("self-test", help="Execute internal SDK self-verification test suite")

    # 9. demo
    demo_parser = subparsers.add_parser("demo", help="Run end-to-end system showcase")
    demo_parser.add_argument("--profile", "-P", default="default", help="Demo profile (e.g. default, final)")

    # 10. analyze
    analyze_parser = subparsers.add_parser("analyze", help="Extract RCIR dependency graph and analyze impact")
    analyze_parser.add_argument("path", help="Path to codebase directory", default=".", nargs="?")
    analyze_parser.add_argument("--impact", "-i", help="Symbol name to compute change blast radius for", default=None)
    analyze_parser.add_argument("--output", "-o", help="JSON output file path for extracted graph", default=None)

    # 11. test
    test_parser = subparsers.add_parser("test", help="Discover and test all .poly contract files in project")
    test_parser.add_argument("dir", help="Directory to search for .poly files", default=".", nargs="?")

    # 12. agent
    agent_parser = subparsers.add_parser("agent", help="Run AI engineering agent pool with token-budget bounding")
    agent_parser.add_argument("task", help="Task description or prompt for the agent pool")
    agent_parser.add_argument("--repo", "-r", help="Repository path", default=".")
    agent_parser.add_argument("--budget", "-b", type=int, help="Maximum token budget ceiling", default=4000)

    # 13. benchmark
    bm_parser = subparsers.add_parser("benchmark", help="Empirical benchmark analytics and token reductions")
    bm_sub = bm_parser.add_subparsers(dest="benchmark_command", help="Benchmark action")
    tokens_parser = bm_sub.add_parser("tokens", help="Display empirical token reductions and comparison")
    tokens_parser.add_argument("--results-path", "-p", help="Path to agent_ab_runs.json", default=None)
    tokens_parser.add_argument("--format", "-f", choices=["text", "json", "csv"], default="text", help="Output format")

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        sys.exit(0)

    if args.command == "doctor":
        sys.exit(execute_doctor())
    elif args.command == "run":
        sys.exit(execute_run(args.file, args.payload))
    elif args.command == "inspect":
        sys.exit(execute_inspect(args.file, args.json))
    elif args.command == "ast":
        sys.exit(execute_ast(args.file, as_json=True))
    elif args.command == "lint":
        sys.exit(execute_lint(args.path))
    elif args.command == "fmt":
        sys.exit(execute_fmt(args.path, args.write))
    elif args.command == "errors":
        sys.exit(execute_errors(args.path))
    elif args.command == "self-test":
        sys.exit(execute_self_test())
    elif args.command == "demo":
        sys.exit(execute_demo(args.profile))
    elif args.command == "analyze":
        sys.exit(execute_analyze(args.path, args.impact, args.output))
    elif args.command == "test":
        sys.exit(execute_test(args.dir))
    elif args.command == "agent":
        sys.exit(execute_agent(args.task, args.repo, args.budget))
    elif args.command == "benchmark":
        if args.benchmark_command == "tokens":
            sys.exit(execute_benchmark_tokens(args.results_path, args.format))
        else:
            bm_parser.print_help()
            sys.exit(0)


if __name__ == "__main__":
    main()
